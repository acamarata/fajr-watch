"""
Twilight detection algorithm for fajr-watch.

Detects the exact moment of Fajr Sadiq (true dawn) and Shafaq al-Abyad
disappearance (Isha) from a sequence of captured horizon images.

The algorithm does NOT use a fixed brightness threshold. It detects the
physical signature of dawn/dusk using multi-channel color analysis and
temporal derivative tracking.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np

from .solar import solar_depression, sun_azimuth, moon_altitude


@dataclass
class TwilightEvent:
    """Result of a single twilight detection."""
    prayer: str                    # "fajr" or "isha"
    utc_time: datetime             # UTC time of detected event
    solar_depression_deg: float    # depression angle at detection moment
    confidence: float              # 0.0 to 1.0
    color_index: float             # (R-B)/(R+B) at detection
    brightness_east: float         # mean brightness of east ROI
    brightness_west: float         # mean brightness of west ROI
    sky_quality_mpsas: Optional[float]  # estimated sky quality
    moon_alt_deg: float            # moon altitude at detection
    cloud_score: float             # 0.0 = clear, 1.0 = overcast
    n_frames: int                  # frames in the sequence


@dataclass
class FrameData:
    """Extracted data from a single captured frame."""
    utc_time: datetime
    east_roi_rgb: np.ndarray       # shape (3,) mean R, G, B in east ROI
    west_roi_rgb: np.ndarray       # shape (3,) mean R, G, B in west ROI
    ref_roi_rgb: np.ndarray        # shape (3,) mean R, G, B in reference ROI
    east_roi_std: float            # spatial std dev in east ROI (cloud proxy)
    solar_dep: float               # solar depression at this frame
    sun_az: float                  # sun azimuth at this frame


def extract_roi_data(
    image: np.ndarray,
    utc_time: datetime,
    lat: float,
    lng: float,
    elevation_m: float,
    lens_fov_deg: float = 180.0,
    azimuth_offset: float = 0.0,
) -> FrameData:
    """
    Extract horizon ROI brightness data from a captured frame.

    For an all-sky fisheye image, the ROIs are defined as:
    - East ROI: 30-degree azimuth band centered on the sun's rising azimuth,
      elevation -2 to +15 degrees
    - West ROI: same band centered on the sun's setting azimuth
    - Reference ROI: north sky, elevation 30-60 degrees (away from twilight)

    For a horizon-pointed camera, the east ROI covers the central 60% of the frame
    horizontally and the lower 40% vertically.
    """
    h, w = image.shape[:2]
    dep = solar_depression(utc_time, lat, lng, elevation_m)
    az = sun_azimuth(utc_time, lat, lng, elevation_m)

    if lens_fov_deg >= 150:
        # All-sky fisheye: map azimuth/elevation to pixel coordinates
        east_roi, west_roi, ref_roi = _extract_fisheye_rois(
            image, az, azimuth_offset, h, w
        )
    else:
        # Horizon-pointed: simple rectangular ROIs
        east_roi, west_roi, ref_roi = _extract_horizon_rois(image, h, w)

    east_rgb = np.mean(east_roi, axis=(0, 1)).astype(float)
    west_rgb = np.mean(west_roi, axis=(0, 1)).astype(float)
    ref_rgb = np.mean(ref_roi, axis=(0, 1)).astype(float)
    east_std = float(np.std(east_roi))

    return FrameData(
        utc_time=utc_time,
        east_roi_rgb=east_rgb,
        west_roi_rgb=west_rgb,
        ref_roi_rgb=ref_rgb,
        east_roi_std=east_std,
        solar_dep=dep,
        sun_az=az,
    )


def _extract_fisheye_rois(
    image: np.ndarray,
    sun_az: float,
    az_offset: float,
    h: int,
    w: int,
) -> tuple:
    """
    Extract ROIs from an all-sky fisheye image.

    In a standard all-sky image:
    - Center of image = zenith
    - Edge of image = horizon (radius = min(h,w)/2)
    - Azimuth maps to angle from top (north=0, east=90 clockwise)
    """
    cx, cy = w // 2, h // 2
    radius = min(h, w) // 2

    # Sun azimuth (east at dawn, west at dusk)
    east_az = sun_az - az_offset
    west_az = (east_az + 180) % 360
    north_az = 0 - az_offset

    # Define ROI masks using polar coordinates
    y_grid, x_grid = np.ogrid[:h, :w]
    dx = x_grid - cx
    dy = y_grid - cy
    r = np.sqrt(dx**2 + dy**2)
    theta = np.degrees(np.arctan2(dx, -dy)) % 360  # 0=N, 90=E

    # Elevation: center=90deg, edge=0deg
    elev = 90.0 * (1.0 - r / radius)

    # East ROI: azimuth within 30deg of sun, elevation -2 to 15
    east_az_dist = np.minimum(
        np.abs(theta - east_az),
        360 - np.abs(theta - east_az)
    )
    east_mask = (east_az_dist < 30) & (elev > -2) & (elev < 15) & (r < radius)

    # West ROI: opposite side
    west_az_dist = np.minimum(
        np.abs(theta - west_az),
        360 - np.abs(theta - west_az)
    )
    west_mask = (west_az_dist < 30) & (elev > -2) & (elev < 15) & (r < radius)

    # Reference ROI: north, elevation 30-60
    north_az_dist = np.minimum(
        np.abs(theta - north_az),
        360 - np.abs(theta - north_az)
    )
    ref_mask = (north_az_dist < 45) & (elev > 30) & (elev < 60) & (r < radius)

    # Extract pixels (fall back to full image quadrants if masks are empty)
    east_pixels = image[east_mask] if east_mask.any() else image[cy:, cx:]
    west_pixels = image[west_mask] if west_mask.any() else image[cy:, :cx]
    ref_pixels = image[ref_mask] if ref_mask.any() else image[:cy // 2, :]

    return east_pixels, west_pixels, ref_pixels


def _extract_horizon_rois(
    image: np.ndarray,
    h: int,
    w: int,
) -> tuple:
    """
    Extract ROIs from a horizon-pointed camera (not fisheye).

    East ROI: center-right of frame, lower half (horizon band)
    West ROI: center-left of frame, lower half
    Reference: top quarter of frame (sky above horizon)
    """
    mid_w = w // 2
    horizon_top = h * 3 // 5  # horizon in lower 40%

    east_roi = image[horizon_top:, mid_w:]
    west_roi = image[horizon_top:, :mid_w]
    ref_roi = image[:h // 4, :]

    return east_roi, west_roi, ref_roi


def color_index(rgb: np.ndarray) -> float:
    """
    Compute the color index (R-B)/(R+B).

    Positive = warm/reddish (scattered light, zodiacal)
    Zero = neutral white (Fajr Sadiq signature)
    Negative = bluish (post-dawn sky)

    Returns 0.0 if both channels are near zero (dark sky).
    """
    r, _, b = float(rgb[0]), float(rgb[1]), float(rgb[2])
    denom = r + b
    if denom < 1.0:
        return 0.0
    return (r - b) / denom


def detect_fajr(
    frames: list[FrameData],
    lat: float,
    lng: float,
) -> Optional[TwilightEvent]:
    """
    Detect Fajr Sadiq from a sequence of morning twilight frames.

    Algorithm:
    1. Sort frames by time (earliest first)
    2. Compute color index time series for east ROI
    3. Compute brightness derivative time series for east ROI
    4. Find the inflection point where:
       a. East ROI brightness begins sustained increase (dB/dt > threshold)
       b. Color index transitions from positive toward zero (warm -> white)
       c. Solar depression is in the 7-22 degree range
    5. Score confidence based on:
       - Smoothness of the brightness curve (noisy = clouds)
       - Consistency between R, G, B channels
       - Moon altitude (moonlit = lower confidence)
    """
    if len(frames) < 10:
        return None

    frames = sorted(frames, key=lambda f: f.utc_time)

    # Filter to frames where solar depression is in the relevant range
    twilight = [f for f in frames if 5.0 <= f.solar_dep <= 24.0]
    if len(twilight) < 5:
        return None

    # Compute time series
    times = np.array([(f.utc_time - twilight[0].utc_time).total_seconds() for f in twilight])
    east_brightness = np.array([np.mean(f.east_roi_rgb) for f in twilight])
    east_ci = np.array([color_index(f.east_roi_rgb) for f in twilight])
    solar_deps = np.array([f.solar_dep for f in twilight])
    cloud_scores = np.array([f.east_roi_std for f in twilight])

    # Smooth the brightness curve (5-point median)
    if len(east_brightness) >= 5:
        smoothed = np.convolve(east_brightness, np.ones(5) / 5, mode="same")
    else:
        smoothed = east_brightness

    # Compute temporal derivative
    dt = np.diff(times)
    dt[dt == 0] = 1  # prevent division by zero
    db_dt = np.diff(smoothed) / dt

    # Find sustained positive brightness increase
    # (at least 3 consecutive frames with increasing brightness)
    candidates = []
    run_length = 0
    for i in range(len(db_dt)):
        if db_dt[i] > 0:
            run_length += 1
            if run_length >= 3:
                onset_idx = i - run_length + 1
                if 7.0 <= solar_deps[onset_idx] <= 22.0:
                    candidates.append(onset_idx)
                    break
        else:
            run_length = 0

    if not candidates:
        # Fall back: find the frame with maximum brightness derivative
        # in the valid depression range
        valid = (solar_deps[:-1] >= 7.0) & (solar_deps[:-1] <= 22.0)
        if not valid.any():
            return None
        valid_db = np.where(valid, db_dt, -np.inf)
        onset_idx = int(np.argmax(valid_db))
    else:
        onset_idx = candidates[0]

    # The detection frame
    det = twilight[onset_idx]

    # Confidence scoring
    confidence = 1.0

    # Penalize for clouds (high spatial variance)
    mean_cloud = float(np.mean(cloud_scores))
    if mean_cloud > 50:
        confidence *= 0.5
    elif mean_cloud > 20:
        confidence *= 0.8

    # Penalize for moon interference
    moon_alt = moon_altitude(det.utc_time, lat, lng)
    if moon_alt > 10:
        confidence *= 0.7
    elif moon_alt > 0:
        confidence *= 0.9

    # Penalize if color index is far from zero (not white)
    ci = color_index(det.east_roi_rgb)
    if abs(ci) > 0.3:
        confidence *= 0.6

    # Penalize for few frames
    if len(twilight) < 20:
        confidence *= 0.7

    return TwilightEvent(
        prayer="fajr",
        utc_time=det.utc_time,
        solar_depression_deg=det.solar_dep,
        confidence=round(confidence, 3),
        color_index=round(ci, 4),
        brightness_east=float(np.mean(det.east_roi_rgb)),
        brightness_west=float(np.mean(det.west_roi_rgb)),
        sky_quality_mpsas=None,  # computed by calibration module
        moon_alt_deg=round(moon_alt, 1),
        cloud_score=round(mean_cloud / 100, 3),
        n_frames=len(twilight),
    )


def detect_isha(
    frames: list[FrameData],
    lat: float,
    lng: float,
) -> Optional[TwilightEvent]:
    """
    Detect Isha (Shafaq al-Abyad disappearance) from evening twilight frames.

    Same algorithm as Fajr but reversed:
    - Monitors the WEST ROI instead of east
    - Looks for sustained brightness DECREASE (dB/dt < 0)
    - Detects when color index of the west horizon returns to zero
      (white glow gone, sky fully dark)
    """
    if len(frames) < 10:
        return None

    frames = sorted(frames, key=lambda f: f.utc_time)

    twilight = [f for f in frames if 5.0 <= f.solar_dep <= 24.0]
    if len(twilight) < 5:
        return None

    times = np.array([(f.utc_time - twilight[0].utc_time).total_seconds() for f in twilight])
    west_brightness = np.array([np.mean(f.west_roi_rgb) for f in twilight])
    west_ci = np.array([color_index(f.west_roi_rgb) for f in twilight])
    solar_deps = np.array([f.solar_dep for f in twilight])
    cloud_scores = np.array([f.east_roi_std for f in twilight])

    if len(west_brightness) >= 5:
        smoothed = np.convolve(west_brightness, np.ones(5) / 5, mode="same")
    else:
        smoothed = west_brightness

    dt = np.diff(times)
    dt[dt == 0] = 1
    db_dt = np.diff(smoothed) / dt

    # For Isha: find where brightness stabilizes at minimum (dB/dt approaches 0
    # from negative) AND the color index has returned to near-zero.
    # This marks the moment the white glow is fully gone.
    candidates = []
    for i in range(3, len(db_dt)):
        if solar_deps[i] < 10.0 or solar_deps[i] > 22.0:
            continue
        # Look for the transition: brightness was decreasing, now stabilized
        recent_db = db_dt[max(0, i - 3):i]
        if len(recent_db) >= 2 and np.all(recent_db < 0):
            # Still decreasing. Check if next frame stabilizes.
            if i < len(db_dt) - 1 and abs(db_dt[i]) < abs(np.mean(recent_db)) * 0.3:
                candidates.append(i)
                break

    if not candidates:
        # Fall back: find the frame with the most negative derivative
        valid = (solar_deps[:-1] >= 10.0) & (solar_deps[:-1] <= 22.0)
        if not valid.any():
            return None
        valid_db = np.where(valid, db_dt, np.inf)
        onset_idx = int(np.argmin(valid_db))
    else:
        onset_idx = candidates[0]

    det = twilight[onset_idx]

    confidence = 1.0
    mean_cloud = float(np.mean(cloud_scores))
    if mean_cloud > 50:
        confidence *= 0.5
    elif mean_cloud > 20:
        confidence *= 0.8

    moon_alt = moon_altitude(det.utc_time, lat, lng)
    if moon_alt > 10:
        confidence *= 0.7
    elif moon_alt > 0:
        confidence *= 0.9

    ci = color_index(det.west_roi_rgb)
    if abs(ci) > 0.3:
        confidence *= 0.6

    if len(twilight) < 20:
        confidence *= 0.7

    return TwilightEvent(
        prayer="isha",
        utc_time=det.utc_time,
        solar_depression_deg=det.solar_dep,
        confidence=round(confidence, 3),
        color_index=round(ci, 4),
        brightness_east=float(np.mean(det.east_roi_rgb)),
        brightness_west=float(np.mean(det.west_roi_rgb)),
        sky_quality_mpsas=None,
        moon_alt_deg=round(moon_alt, 1),
        cloud_score=round(mean_cloud / 100, 3),
        n_frames=len(twilight),
    )
