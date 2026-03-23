"""
Data upload module for fajr-watch.

Syncs completed detection results to the central pray-calc-ml dataset.
Runs as a cron job (hourly) or can be triggered manually.
"""

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

import requests

log = logging.getLogger(__name__)

RESULTS_DIR = Path("/var/lib/fajr-watch/data/results")
UPLOAD_QUEUE = Path("/var/lib/fajr-watch/data/upload-queue")
UPLOADED_DIR = Path("/var/lib/fajr-watch/data/uploaded")


def load_config() -> dict:
    """Load station config."""
    import yaml
    for path in ["/boot/fajr-watch/station.yaml", "/opt/fajr-watch/app/config/station.yaml"]:
        p = Path(path)
        if p.exists():
            with open(p) as f:
                return yaml.safe_load(f)
    raise FileNotFoundError("No station.yaml found")


def sync():
    """Upload all pending results to the central server."""
    config = load_config()
    upload_url = config["network"].get("upload_url", "")
    api_key = config["network"].get("api_key", "")

    if not upload_url:
        log.warning("No upload_url configured. Skipping sync.")
        return

    UPLOADED_DIR.mkdir(parents=True, exist_ok=True)

    # Collect all JSON result files
    results = sorted(RESULTS_DIR.glob("*.json"))
    if not results:
        log.info("No results to upload.")
        return

    log.info("Uploading %d result(s) to %s", len(results), upload_url)

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    uploaded = 0
    failed = 0

    for result_path in results:
        try:
            with open(result_path) as f:
                data = json.load(f)

            response = requests.post(
                upload_url,
                json=data,
                headers=headers,
                timeout=30,
            )

            if response.status_code in (200, 201, 204):
                # Move to uploaded archive
                shutil.move(str(result_path), str(UPLOADED_DIR / result_path.name))
                uploaded += 1
            else:
                log.warning("Upload failed for %s: HTTP %d %s",
                            result_path.name, response.status_code, response.text[:200])
                failed += 1

        except requests.RequestException as e:
            log.warning("Upload error for %s: %s", result_path.name, e)
            failed += 1
        except Exception as e:
            log.error("Unexpected error uploading %s: %s", result_path.name, e)
            failed += 1

    log.info("Upload complete: %d uploaded, %d failed, %d remaining",
             uploaded, failed, len(list(RESULTS_DIR.glob("*.json"))))


def export_csv(output_path: str = None):
    """
    Export all local results as a CSV compatible with pray-calc-ml ingest format.

    Useful for manual data transfer (USB stick) when the station has no internet.
    """
    import csv

    if output_path is None:
        output_path = f"/var/lib/fajr-watch/data/export_{datetime.now().strftime('%Y%m%d')}.csv"

    all_dirs = [RESULTS_DIR, UPLOADED_DIR]
    records = []

    for d in all_dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            with open(f) as fh:
                data = json.load(fh)
                records.append(data)

    if not records:
        log.info("No records to export.")
        return

    fieldnames = [
        "prayer", "date", "utc_time", "solar_depression_deg", "confidence",
        "lat", "lng", "elevation_m", "environment", "horizon",
        "camera", "sky_quality_mpsas", "moon_alt_deg", "cloud_score",
        "color_index_at_detection", "station_id", "n_frames",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    log.info("Exported %d records to %s", len(records), output_path)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1 and sys.argv[1] == "export":
        export_csv(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        sync()
