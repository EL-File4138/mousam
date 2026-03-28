import json
from pathlib import Path

import gi
from gi.repository import Gio, GLib

gi.require_version("GWeather", "4.0")
from gi.repository import GWeather

from .CORE_locationModel import AUTO_LOCATION_ID, LocationModel
from .settings import settings


BUS_PATH = "/io/github/amit9838/mousam"
GNOME_WEATHER_BUS_PATH = "/org/gnome/Weather"
SHELL_INTERFACE = "org.gnome.Shell.WeatherIntegration"


def _load_interface_xml() -> str:
    current_file = Path(__file__).resolve()
    candidates = [
        current_file.parent.parent / "data" / "ShellWeatherIntegration.xml",
        current_file.parent.parent / "ShellWeatherIntegration.xml",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")

    raise FileNotFoundError("ShellWeatherIntegration.xml was not found")


class ShellIntegrationExporter:
    def __init__(self, settings_obj=None):
        self.settings = settings_obj or settings
        self.location_model = LocationModel(self.settings)
        self.world = GWeather.Location.get_world()
        self.node_info = Gio.DBusNodeInfo.new_for_xml(_load_interface_xml())
        self.registration_id = None
        self.connection = None
        self.settings_handlers = []
        self.shell_settings = self._get_shell_settings()

        self.interface_info = self.node_info.interfaces[0]
    def export(self, connection: Gio.DBusConnection, object_path: str = BUS_PATH):
        if self.settings.IS_FLATPAK:
            return

        if self.registration_id is not None:
            return

        self.connection = connection
        self.registration_id = connection.register_object_with_closures2(
            object_path,
            self.interface_info,
            self._handle_method_call,
            self._handle_get_property,
            None,
        )

        for key in (
            "automatic-location",
            "current-location",
            "added-cities",
            "shell-integration-enabled",
            "selected-city",
        ):
            handler_id = self.settings.settings.connect(
                f"changed::{key}",
                self._on_settings_changed,
            )
            self.settings_handlers.append(handler_id)

        self._sync_shell_settings()

    def unexport(self):
        if self.connection is not None and self.registration_id is not None:
            self.connection.unregister_object(self.registration_id)

        self.registration_id = None
        self.connection = None

        for handler_id in self.settings_handlers:
            self.settings.settings.disconnect(handler_id)
        self.settings_handlers.clear()

    def _handle_method_call(self, *_args):
        return None

    def _handle_get_property(self, _connection, _sender, _object_path, _interface_name, property_name):
        if property_name == "AutomaticLocation":
            return GLib.Variant("b", self._selected_is_automatic())

        if property_name == "Locations":
            return GLib.Variant("av", self._build_location_variants())

        return None

    def _build_location_variants(self):
        if not self.settings.shell_integration_enabled:
            return []

        variants = []
        for location in self._ordered_manual_locations():
            serialized = self._serialize_location(location)
            if serialized is not None:
                variants.append(serialized)
        return variants

    def _ordered_manual_locations(self):
        manual_locations = self.location_model.get_manual_locations()
        selected_key = self.settings.selected_city
        if selected_key in ("", AUTO_LOCATION_ID):
            return manual_locations

        selected = None
        others = []
        for location in manual_locations:
            if location.coords_key == selected_key and selected is None:
                selected = location
            else:
                others.append(location)

        if selected is None:
            return manual_locations
        return [selected, *others]

    def _selected_is_automatic(self) -> bool:
        return (
            self.settings.shell_integration_enabled
            and
            self.settings.automatic_location
            and self.settings.selected_city in ("", AUTO_LOCATION_ID)
            and self.location_model.get_automatic_location() is not None
        )

    def _serialize_location(self, location):
        if self.world is None:
            return None

        try:
            nearest = self.world.find_nearest_city(location.latitude, location.longitude)
        except Exception:
            return None

        if nearest is None:
            return None

        try:
            return nearest.serialize()
        except Exception:
            return None

    def _get_shell_settings(self):
        if self.settings.IS_FLATPAK:
            return None

        schema_source = Gio.SettingsSchemaSource.get_default()
        if schema_source is None:
            return None

        schema = schema_source.lookup("org.gnome.shell.weather", True)
        if schema is None:
            return None

        return Gio.Settings.new_full(schema, None, None)

    def _to_variant(self, value):
        if isinstance(value, bool):
            return GLib.Variant("b", value)
        if isinstance(value, int):
            return GLib.Variant("i", value)
        if isinstance(value, float):
            return GLib.Variant("d", value)
        if value is None:
            return GLib.Variant("s", "")
        return GLib.Variant("s", str(value))

    def _on_settings_changed(self, *_args):
        self._sync_shell_settings()

        if self.connection is None:
            return

        changed = {
            "AutomaticLocation": GLib.Variant("b", self._selected_is_automatic()),
            "Locations": GLib.Variant("av", self._build_location_variants()),
        }
        self.connection.emit_signal(
            None,
            BUS_PATH,
            "org.freedesktop.DBus.Properties",
            "PropertiesChanged",
            GLib.Variant(
                "(sa{sv}as)",
                (
                    SHELL_INTERFACE,
                    changed,
                    [],
                ),
            ),
        )

    def _sync_shell_settings(self):
        if self.shell_settings is None:
            return

        self.shell_settings.set_boolean(
            "automatic-location",
            self._selected_is_automatic(),
        )
        self.shell_settings.set_value(
            "locations",
            GLib.Variant("av", self._build_location_variants()),
        )

    def dump_locations_json(self) -> str:
        return json.dumps(
            [
                location.shell_payload(
                    selected=self.location_model.is_selected(location)
                )
                for location in self.location_model.all_locations()
            ],
            sort_keys=True,
        )
