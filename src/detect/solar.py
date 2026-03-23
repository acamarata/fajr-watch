"""
Solar position utilities for fajr-watch.

Computes solar depression angle, twilight windows, and sun azimuth
for a given location and time. Uses PyEphem for accuracy.
"""

import math
from datetime import datetime, timedelta, timezone

import ephem


def solar_depression(utc_dt: datetime, lat: float, lng: float, elevation_m: float = 0) -> float:
    """
    Solar depression angle in degrees at the given UTC time and location.

    Returns positive values when the sun is below the horizon.
    Returns negative values when the sun is above the horizon.
    """
    obs = ephem.Observer()
    obs.lat = str(lat)
    obs.lon = str(lng)
    obs.elevation = elevation_m
    obs.pressure = 1013.25
    obs.temp = 15.0

    if utc_dt.tzinfo is not None:
        utc_dt = utc_dt.replace(tzinfo=None)
    obs.date = ephem.Date(utc_dt)

    sun = ephem.Sun(obs)
    altitude_deg = math.degrees(float(sun.alt))
    return -altitude_deg


def sun_azimuth(utc_dt: datetime, lat: float, lng: float, elevation_m: float = 0) -> float:
    """
    Sun azimuth in degrees (0=N, 90=E, 180=S, 270=W) at the given UTC time.
    """
    obs = ephem.Observer()
    obs.lat = str(lat)
    obs.lon = str(lng)
    obs.elevation = elevation_m
    obs.pressure = 1013.25
    obs.temp = 15.0

    if utc_dt.tzinfo is not None:
        utc_dt = utc_dt.replace(tzinfo=None)
    obs.date = ephem.Date(utc_dt)

    sun = ephem.Sun(obs)
    return math.degrees(float(sun.az))


def twilight_window(
    date: datetime,
    lat: float,
    lng: float,
    elevation_m: float = 0,
    margin_deg: float = 5.0,
) -> dict:
    """
    Compute the UTC time windows for Fajr and Isha observation tonight.

    Returns a dict with keys:
      fajr_start: UTC datetime to begin Fajr capture
      fajr_end:   UTC datetime to stop Fajr capture
      isha_start: UTC datetime to begin Isha capture
      isha_end:   UTC datetime to stop Isha capture

    The window is defined as when solar depression is between
    (target_angle + margin) and (target_angle - margin), roughly
    22+margin to 7-margin degrees, covering the full possible range.
    """
    obs = ephem.Observer()
    obs.lat = str(lat)
    obs.lon = str(lng)
    obs.elevation = elevation_m
    obs.pressure = 0  # no refraction for horizon crossing
    obs.date = ephem.Date(date.replace(tzinfo=None))

    # Find sunset and sunrise to anchor the windows
    sun = ephem.Sun()

    try:
        sunset = obs.next_setting(sun).datetime().replace(tzinfo=timezone.utc)
    except ephem.NeverUpError:
        # Polar night: no sunset
        return None
    except ephem.AlwaysUpError:
        # Midnight sun: no sunset
        return None

    try:
        obs.date = ephem.Date(sunset + timedelta(hours=1))
        sunrise = obs.next_rising(sun).datetime().replace(tzinfo=timezone.utc)
    except (ephem.NeverUpError, ephem.AlwaysUpError):
        return None

    # Isha window: starts at sunset, ends when depression exceeds 22+margin
    isha_start = sunset - timedelta(minutes=10)
    isha_end = sunset + timedelta(hours=2, minutes=30)

    # Fajr window: starts when depression is 22+margin before sunrise
    fajr_start = sunrise - timedelta(hours=2, minutes=30)
    fajr_end = sunrise + timedelta(minutes=10)

    return {
        "isha_start": isha_start,
        "isha_end": isha_end,
        "fajr_start": fajr_start,
        "fajr_end": fajr_end,
        "sunset": sunset,
        "sunrise": sunrise,
    }


def moon_altitude(utc_dt: datetime, lat: float, lng: float) -> float:
    """
    Moon altitude in degrees at the given time and location.
    Used to flag moonlit conditions that may affect detection.
    """
    obs = ephem.Observer()
    obs.lat = str(lat)
    obs.lon = str(lng)
    obs.pressure = 1013.25

    if utc_dt.tzinfo is not None:
        utc_dt = utc_dt.replace(tzinfo=None)
    obs.date = ephem.Date(utc_dt)

    moon = ephem.Moon(obs)
    return math.degrees(float(moon.alt))
