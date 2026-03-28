import sys

import gi

gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")

from gi.repository import Gio, GLib

from .CORE_currentLocation import CurrentLocationController
from .CORE_refreshService import WeatherRefreshService
from .config import settings


class WeatherBackgroundService(Gio.Application):
    def __init__(self):
        super().__init__(
            application_id=f"{settings.APP_ID}.BackgroundService",
            flags=Gio.ApplicationFlags.IS_SERVICE,
            inactivity_timeout=60000,
        )
        self.refresh_service = WeatherRefreshService(settings)
        self.current_location_controller = None
        self.refresh_source_id = None

    def do_startup(self):
        Gio.Application.do_startup(self)
        self.hold()

        self._sync_automatic_location_controller()

        self._schedule_refresh()
        if settings.background_refresh_enabled:
            self.refresh_service.refresh_async()

        for key in (
            "auto-refresh-interval",
            "background-refresh-enabled",
            "automatic-location",
            "selected-city",
            "added-cities",
            "current-location",
        ):
            settings.settings.connect(f"changed::{key}", self._on_settings_changed)

    def do_activate(self):
        return None

    def do_shutdown(self):
        if self.refresh_source_id is not None:
            GLib.source_remove(self.refresh_source_id)
            self.refresh_source_id = None

        Gio.Application.do_shutdown(self)

    def _on_settings_changed(self, *_args):
        self._sync_automatic_location_controller()
        self._schedule_refresh()

        if settings.background_refresh_enabled:
            self.refresh_service.refresh_async()

    def _on_automatic_location_changed(self, _location):
        if settings.background_refresh_enabled:
            self.refresh_service.refresh_async()

    def _schedule_refresh(self):
        if self.refresh_source_id is not None:
            GLib.source_remove(self.refresh_source_id)
            self.refresh_source_id = None

        interval = settings.auto_refresh_interval
        if not settings.background_refresh_enabled or interval <= 0:
            return

        self.refresh_source_id = GLib.timeout_add_seconds(
            interval * 60,
            self._on_refresh_timeout,
        )

    def _sync_automatic_location_controller(self):
        if settings.automatic_location and self.current_location_controller is None:
            self.current_location_controller = CurrentLocationController(
                settings, self._on_automatic_location_changed
            )
            self.current_location_controller.start()
            return

        if not settings.automatic_location:
            settings.current_location = ""
            self.current_location_controller = None

    def _on_refresh_timeout(self):
        if settings.background_refresh_enabled:
            self.refresh_service.refresh_async()
        return GLib.SOURCE_CONTINUE


def main(_version=None):
    app = WeatherBackgroundService()
    return app.run(sys.argv)
