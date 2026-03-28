import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from .config import settings


AUTO_LOCATION_ID = "__automatic__"


@dataclass(frozen=True)
class WeatherLocation:
    name: str = ""
    country: str = ""
    state: str = ""
    region: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = "UTC"
    source: str = "manual"

    @classmethod
    def from_dict(cls, payload: Optional[Dict]):
        payload = payload or {}
        return cls(
            name=payload.get("name") or "",
            country=payload.get("country") or "",
            state=payload.get("state") or "",
            region=payload.get("region") or "",
            latitude=float(payload.get("latitude") or 0.0),
            longitude=float(payload.get("longitude") or 0.0),
            timezone=payload.get("timezone") or "UTC",
            source=payload.get("source") or "manual",
        )

    @classmethod
    def from_storage_string(cls, raw_value: str):
        if not raw_value:
            return None
        try:
            return cls.from_dict(json.loads(raw_value))
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "country": self.country,
            "state": self.state,
            "region": self.region,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
            "source": self.source,
        }

    def to_storage_string(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @property
    def coords_key(self) -> str:
        return f"{self.latitude},{self.longitude}"

    @property
    def display_name(self) -> str:
        return ", ".join(
            filter(None, [self.name, self.state, self.country])
        )

    def shell_payload(self, selected: bool = False) -> Dict:
        payload = self.to_dict()
        payload["id"] = self.coords_key
        payload["selected"] = selected
        return payload


class LocationModel:
    def __init__(self, settings_obj=None):
        self.settings = settings_obj or settings

    def get_manual_locations(self) -> List[WeatherLocation]:
        locations = []
        for raw_value in self.settings.added_cities:
            location = WeatherLocation.from_storage_string(raw_value)
            if location is not None:
                locations.append(location)
        return locations

    def add_manual_location(self, location: WeatherLocation) -> bool:
        if self.has_manual_location(location.coords_key):
            return False
        locations = self.get_manual_locations()
        locations.append(location)
        self.settings.added_cities = [item.to_storage_string() for item in locations]
        return True

    def remove_manual_location(self, coords_key: str):
        updated_locations = [
            location
            for location in self.get_manual_locations()
            if location.coords_key != coords_key
        ]
        self.settings.added_cities = [
            item.to_storage_string() for item in updated_locations
        ]

    def has_manual_location(self, coords_key: str) -> bool:
        return any(
            location.coords_key == coords_key
            for location in self.get_manual_locations()
        )

    def get_automatic_location(self):
        return WeatherLocation.from_storage_string(self.settings.current_location)

    def set_automatic_location(self, location: Optional[WeatherLocation]):
        if location is None:
            self.settings.current_location = ""
            return
        automatic_location = WeatherLocation.from_dict(
            {**location.to_dict(), "source": "automatic"}
        )
        self.settings.current_location = automatic_location.to_storage_string()

    def get_selected_location(self):
        selected_key = self.settings.selected_city
        if (
            self.settings.automatic_location
            and selected_key in ("", AUTO_LOCATION_ID)
        ):
            automatic_location = self.get_automatic_location()
            if automatic_location is not None:
                return automatic_location

        for location in self.get_manual_locations():
            if location.coords_key == selected_key:
                return location

        manual_locations = self.get_manual_locations()
        if manual_locations:
            return manual_locations[0]

        return self.get_automatic_location()

    def get_primary_manual_location(self):
        manual_locations = self.get_manual_locations()
        if manual_locations:
            return manual_locations[0]
        return None

    def set_selected_location(self, location: Optional[WeatherLocation]):
        self.settings.selected_city = location.coords_key if location else ""

    def select_automatic_location(self):
        self.settings.selected_city = AUTO_LOCATION_ID

    def all_locations(self, include_automatic: bool = True) -> List[WeatherLocation]:
        locations = []
        automatic_location = self.get_automatic_location()
        if include_automatic and self.settings.automatic_location and automatic_location:
            locations.append(automatic_location)
        locations.extend(self.get_manual_locations())
        return locations

    def is_selected(self, location: WeatherLocation) -> bool:
        if location.source == "automatic":
            return (
                self.settings.automatic_location
                and self.settings.selected_city in ("", AUTO_LOCATION_ID)
                and self.get_automatic_location() is not None
            )

        return self.settings.selected_city == location.coords_key
