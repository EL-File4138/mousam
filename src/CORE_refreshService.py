import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

try:
    from gi.repository import GLib
except ImportError:
    GLib = None

from .CORE_locationModel import LocationModel, WeatherLocation
from .CORE_weatherData import (
    fetch_current_air_pollution,
    fetch_current_weather,
    fetch_daily_forecast,
    fetch_hourly_forecast,
)
from .config import settings
from .utils import check_internet_connection, get_time_difference


@dataclass
class RefreshResult:
    success: bool
    status: str
    location: Optional[WeatherLocation] = None
    error: str = ""


class WeatherRefreshService:
    def __init__(self, settings_obj=None):
        self.settings = settings_obj or settings
        self.location_model = LocationModel(self.settings)

    def _set_refresh_state(self, status: str):
        self.settings.last_refresh_status = status
        self.settings.last_refresh_timestamp = int(time.time())

    def refresh(self, location: Optional[WeatherLocation] = None) -> RefreshResult:
        location = location or self.location_model.get_selected_location()

        if location is None:
            self._set_refresh_state("no-location")
            return RefreshResult(False, "no-location")

        if not check_internet_connection():
            self._set_refresh_state("no-internet")
            return RefreshResult(False, "no-internet", location=location)

        try:
            fetch_current_weather()
            fetch_hourly_forecast()
            fetch_daily_forecast()
            fetch_current_air_pollution()
            get_time_difference(location.timezone, True)
            self._set_refresh_state("ok")
            return RefreshResult(True, "ok", location=location)
        except Exception as error:
            self._set_refresh_state("error")
            return RefreshResult(False, "error", location=location, error=str(error))

    def refresh_async(
        self,
        location: Optional[WeatherLocation] = None,
        on_complete: Optional[Callable[[RefreshResult], None]] = None,
    ):
        def worker():
            result = self.refresh(location=location)
            if on_complete is None:
                return
            if GLib is None:
                on_complete(result)
                return
            GLib.idle_add(on_complete, result)

        threading.Thread(target=worker, daemon=True).start()
