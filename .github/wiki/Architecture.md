# Architecture

Fajr Watch is designed as a field appliance. The operator should be able to configure the station, leave it running, and recover useful twilight observations without managing a general-purpose server.

## Components

- `config/station.example.yaml` defines the station identity, coordinates, camera settings, upload target, and capture schedule.
- `src/` contains the Python package used by the appliance.
- `data/captures/` stores raw field captures and is intentionally kept out of git.
- `data/processed/` stores derived outputs and is intentionally kept out of git.
- `data/upload-queue/` holds pending records for later transfer.

## Operating Model

The station runs scheduled captures around expected Fajr and Isha windows. Captures are kept locally first so network failures do not destroy observations. Review and upload steps should treat raw captures as source data and derived records as reproducible outputs.

## Configuration Boundary

`config/station.example.yaml` is the committed template. A real station uses `config/station.yaml`, which is gitignored because it can contain location-specific and deployment-specific values.

