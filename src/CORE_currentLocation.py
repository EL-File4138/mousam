import logging

import requests

from .CORE_locationModel import LocationModel, WeatherLocation
from .config import settings
from .utils import GEONAMES_USERNAME

try:
    import gi

    gi.require_version("Geoclue", "2.0")
    from gi.repository import Geoclue
except (ImportError, ValueError):
    Geoclue = None


logger = logging.getLogger(__name__)

GEONAMES_NEARBY_URL = "https://secure.geonames.org/findNearbyPlaceNameJSON"
GEONAMES_TIMEZONE_URL = "https://secure.geonames.org/timezoneJSON"


class CurrentLocationController:
    def __init__(self, settings_obj=None, on_location_changed=None):
        self.settings = settings_obj or settings
        self.location_model = LocationModel(self.settings)
        self.on_location_changed = on_location_changed
        self.simple = None

    def start(self) -> bool:
        if Geoclue is None:
            logger.warning("GeoClue bindings are not available")
            return False

        if hasattr(Geoclue.Simple, "new_with_thresholds"):
            Geoclue.Simple.new_with_thresholds(
                self.settings.APP_ID,
                Geoclue.AccuracyLevel.CITY,
                0,
                100,
                None,
                self._on_simple_ready,
            )
            return True

        Geoclue.Simple.new(
            self.settings.APP_ID,
            Geoclue.AccuracyLevel.CITY,
            None,
            self._on_simple_ready,
        )
        return True

    def _on_simple_ready(self, _source, result):
        try:
            self.simple = Geoclue.Simple.new_finish(result)
        except Exception as error:
            logger.warning("Failed to start GeoClue: %s", error)
            self.location_model.set_automatic_location(None)
            return

        if not hasattr(Geoclue.Simple, "new_with_thresholds"):
            client = self.simple.get_client()
            if client is not None:
                client.distance_threshold = 100

        self.simple.connect("notify::location", self._on_location_updated)
        self._on_location_updated(self.simple, None)

    def _on_location_updated(self, simple, _pspec):
        geoclue_location = simple.get_location()
        if geoclue_location is None:
            self.location_model.set_automatic_location(None)
            return

        latitude = geoclue_location.get_property("latitude")
        longitude = geoclue_location.get_property("longitude")
        location = self._reverse_geocode(latitude, longitude)
        if location is None:
            location = WeatherLocation(
                name="Current Location",
                latitude=latitude,
                longitude=longitude,
                timezone="UTC",
                source="automatic",
            )

        self.location_model.set_automatic_location(location)
        if self.on_location_changed is not None:
            self.on_location_changed(location)

    def _reverse_geocode(self, latitude: float, longitude: float):
        params = {
            "lat": latitude,
            "lng": longitude,
            "username": GEONAMES_USERNAME,
        }

        try:
            response = requests.get(GEONAMES_NEARBY_URL, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as error:
            logger.warning("Failed to reverse geocode current location: %s", error)
            return None

        nearby_places = payload.get("geonames") or []
        if not nearby_places:
            return None

        place = nearby_places[0]
        timezone = self._lookup_timezone(latitude, longitude)
        return WeatherLocation(
            name=place.get("name") or "Current Location",
            country=place.get("countryName") or "",
            state=place.get("adminName1") or "",
            region=place.get("adminName2") or "",
            latitude=float(place.get("lat") or latitude),
            longitude=float(place.get("lng") or longitude),
            timezone=timezone,
            source="automatic",
        )

    def _lookup_timezone(self, latitude: float, longitude: float) -> str:
        params = {
            "lat": latitude,
            "lng": longitude,
            "username": GEONAMES_USERNAME,
        }
        try:
            response = requests.get(GEONAMES_TIMEZONE_URL, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as error:
            logger.warning("Failed to resolve current location timezone: %s", error)
            return "UTC"

        return payload.get("timezoneId") or "UTC"
