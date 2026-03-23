"""
Capture scheduler for fajr-watch.

Runs the main loop: sleep until twilight, capture frames, run detection,
upload results, repeat.
"""

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..detect.solar import twilight_window, solar_depression
from ..detect.twilight import (
    TwilightEvent,
    FrameData,
    detect_fajr,
    detect_isha,
    extract_roi_data,
)

log = logging.getLogger(__name__)

DATA_DIR = Path("/var/lib/fajr-watch/data")
RESULTS_DIR = DATA_DIR / "results"
CAPTURES_DIR = DATA_DIR / "captures"


def load_config(path: str = "/boot/fajr-watch/station.yaml") -> dict:
    """Load station configuration from YAML."""
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


def capture_frame(camera, config: dict) -> tuple:
    """
    Capture a single frame from the camera.
    Returns (image_array, utc_timestamp).
    """
    camera_type = config["camera"]["type"]

    if camera_type.startswith("zwo_"):
        return _capture_zwo(camera, config)
    elif camera_type.startswith("pi_"):
        return _capture_picamera(camera, config)
    else:
        raise ValueError(f"Unknown camera type: {camera_type}")


def _capture_zwo(camera, config: dict) -> tuple:
    """Capture from ZWO ASI camera via the ZWO SDK."""
    import zwoasi

    utc_now = datetime.now(timezone.utc)

    # Auto-exposure: adjust to target brightness
    target = config["capture"].get("target_brightness", 80)
    max_exp = config["capture"].get("max_exposure_s", 30) * 1_000_000  # microseconds

    camera.set_control_value(zwoasi.ASI_EXPOSURE, min(int(max_exp), 30_000_000))
    camera.set_control_value(zwoasi.ASI_GAIN, 200)

    image = camera.capture_video_frame()
    return image, utc_now


def _capture_picamera(camera, config: dict) -> tuple:
    """Capture from Raspberry Pi camera via picamera2."""
    import numpy as np

    utc_now = datetime.now(timezone.utc)

    # camera is a Picamera2 instance, already configured
    image = camera.capture_array("main")
    return image, utc_now


def init_camera(config: dict):
    """Initialize the camera based on config."""
    camera_type = config["camera"]["type"]

    if camera_type.startswith("zwo_"):
        import zwoasi
        zwoasi.init("/usr/lib/libASICamera2.so")
        cameras = zwoasi.list_cameras()
        if not cameras:
            raise RuntimeError("No ZWO camera detected")
        camera = zwoasi.Camera(0)
        camera.set_control_value(zwoasi.ASI_BANDWIDTHOVERLOAD, 40)
        camera.set_image_type(zwoasi.ASI_IMG_RGB24)
        camera.start_video_capture()
        log.info("ZWO camera initialized: %s", cameras[0])
        return camera

    elif camera_type.startswith("pi_"):
        from picamera2 import Picamera2
        camera = Picamera2()

        raw_mode = config["capture"].get("raw_format", True)
        if raw_mode:
            cam_config = camera.create_still_configuration(
                main={"format": "RGB888"},
                raw={"format": camera.sensor_modes[0]["format"]},
            )
        else:
            cam_config = camera.create_still_configuration(
                main={"format": "RGB888"},
            )

        camera.configure(cam_config)
        camera.start()
        log.info("Pi camera initialized")
        return camera

    else:
        raise ValueError(f"Unknown camera type: {camera_type}")


def save_event(event: TwilightEvent, config: dict):
    """Save a detection event to disk as JSON."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    station = config["station"]
    filename = f"{event.prayer}_{event.utc_time.strftime('%Y-%m-%d_%H%M%S')}.json"

    record = {
        "station_id": station["id"],
        "date": event.utc_time.strftime("%Y-%m-%d"),
        "prayer": event.prayer,
        "utc_time": event.utc_time.isoformat(),
        "solar_depression_deg": round(event.solar_depression_deg, 4),
        "confidence": event.confidence,
        "lat": station["lat"],
        "lng": station["lng"],
        "elevation_m": station["elevation_m"],
        "environment": station.get("environment", "unknown"),
        "horizon": station.get("horizon", "unknown"),
        "camera": config["camera"]["type"],
        "sky_quality_mpsas": event.sky_quality_mpsas,
        "moon_alt_deg": event.moon_alt_deg,
        "cloud_score": event.cloud_score,
        "color_index_at_detection": event.color_index,
        "n_frames": event.n_frames,
    }

    path = RESULTS_DIR / filename
    with open(path, "w") as f:
        json.dump(record, f, indent=2)

    log.info("Saved %s detection: %.2f deg (confidence %.2f) -> %s",
             event.prayer, event.solar_depression_deg, event.confidence, path)
    return path


def run_capture_session(
    camera,
    config: dict,
    window_start: datetime,
    window_end: datetime,
    prayer: str,
) -> list[FrameData]:
    """
    Capture frames during a twilight window.
    Returns list of FrameData for detection.
    """
    station = config["station"]
    interval = config["capture"].get("interval_s", 10)
    lens_fov = config["camera"].get("lens_fov_deg", 180.0)
    az_offset = config["camera"].get("azimuth_offset", 0.0)

    frames = []
    log.info("Starting %s capture session: %s to %s (interval %ds)",
             prayer, window_start.isoformat(), window_end.isoformat(), interval)

    # Wait until window starts
    now = datetime.now(timezone.utc)
    if now < window_start:
        wait = (window_start - now).total_seconds()
        log.info("Sleeping %.0f seconds until %s window", wait, prayer)
        time.sleep(wait)

    while datetime.now(timezone.utc) < window_end:
        try:
            image, utc_time = capture_frame(camera, config)
            frame = extract_roi_data(
                image, utc_time,
                station["lat"], station["lng"], station["elevation_m"],
                lens_fov, az_offset,
            )
            frames.append(frame)

            dep = frame.solar_dep
            log.debug("Frame %s: dep=%.2f, east_mean=%.1f",
                      utc_time.strftime("%H:%M:%S"), dep,
                      float(frame.east_roi_rgb.mean()))

        except Exception as e:
            log.warning("Frame capture error: %s", e)

        time.sleep(interval)

    log.info("Capture session complete: %d frames", len(frames))
    return frames


def run_night(config: dict, camera):
    """
    Run one complete night: Isha capture + detection, sleep, Fajr capture + detection.
    """
    station = config["station"]
    lat = station["lat"]
    lng = station["lng"]
    elev = station["elevation_m"]
    margin = config["capture"].get("twilight_margin_deg", 5)

    now = datetime.now(timezone.utc)
    windows = twilight_window(now, lat, lng, elev, margin)

    if windows is None:
        log.warning("No twilight tonight (polar conditions). Sleeping 12 hours.")
        time.sleep(43200)
        return

    # Isha session (evening)
    if datetime.now(timezone.utc) < windows["isha_end"]:
        frames = run_capture_session(
            camera, config,
            windows["isha_start"], windows["isha_end"],
            "isha",
        )
        if frames:
            event = detect_isha(frames, lat, lng)
            if event and event.confidence >= config["processing"].get("min_confidence", 0.5):
                save_event(event, config)
            elif event:
                log.info("Isha detection below confidence threshold: %.2f", event.confidence)
            else:
                log.info("No Isha detection from %d frames", len(frames))

    # Sleep until Fajr window
    now = datetime.now(timezone.utc)
    if now < windows["fajr_start"]:
        wait = (windows["fajr_start"] - now).total_seconds()
        log.info("Sleeping %.0f seconds until Fajr window", wait)
        time.sleep(wait)

    # Fajr session (morning)
    frames = run_capture_session(
        camera, config,
        windows["fajr_start"], windows["fajr_end"],
        "fajr",
    )
    if frames:
        event = detect_fajr(frames, lat, lng)
        if event and event.confidence >= config["processing"].get("min_confidence", 0.5):
            save_event(event, config)
        elif event:
            log.info("Fajr detection below confidence threshold: %.2f", event.confidence)
        else:
            log.info("No Fajr detection from %d frames", len(frames))


def main():
    """Main entry point. Runs forever."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("/var/log/fajr-watch.log"),
        ],
    )

    config_path = "/boot/fajr-watch/station.yaml"
    if not Path(config_path).exists():
        config_path = "config/station.yaml"

    config = load_config(config_path)
    log.info("Station %s starting at %.4f, %.4f",
             config["station"]["id"],
             config["station"]["lat"],
             config["station"]["lng"])

    camera = init_camera(config)

    while True:
        try:
            run_night(config, camera)
        except KeyboardInterrupt:
            log.info("Shutdown requested")
            break
        except Exception as e:
            log.error("Night session error: %s", e, exc_info=True)
            time.sleep(300)  # wait 5 min on error, then retry


if __name__ == "__main__":
    main()
