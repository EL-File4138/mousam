import json
import time
from typing import List, Dict, Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from .CORE_Helpers import create_toast
from .API_FindCity import find_city
from .settings import settings
from .CORE_locationModel import LocationModel, WeatherLocation
from gettext import gettext as _, pgettext as C_

# --- Data Layer Utilities ---


class LocationData:
    """Helper to handle serialization and formatting of city data."""

    @staticmethod
    def to_storage_string(city_dict: Dict) -> str:
        """Converts a city dictionary to a JSON string for settings."""
        return WeatherLocation.from_dict(city_dict).to_storage_string()

    @staticmethod
    def from_storage_string(json_str: str) -> Dict:
        """Converts a JSON string from settings back to a dictionary."""
        location = WeatherLocation.from_storage_string(json_str)
        return location.to_dict() if location else {}

    @staticmethod
    def format_display_name(data: Dict) -> str:
        """Creates a clean 'City, State, Country' string."""
        return WeatherLocation.from_dict(data).display_name

    @staticmethod
    def get_coords_key(data: Dict) -> str:
        """Returns a unique coordinate string used for selection tracking."""
        return WeatherLocation.from_dict(data).coords_key


# --- Components ---


class CitySearchDialog(Adw.PreferencesWindow):
    """Encapsulated search UI."""

    def __init__(self, parent, on_selection_callback):
        super().__init__(transient_for=parent, default_width=350, default_height=500)
        self.set_title(_("Add New Location"))
        self.callback = on_selection_callback
        self.results_rows = []
        self._init_ui()

    def _init_ui(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()
        self.add(page)
        page.add(group)

        # Search Entry Box
        header_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6, margin_bottom=10
        )
        self.search_entry = Gtk.Entry(
            placeholder_text=_("Search for a city"), hexpand=True
        )
        self.search_entry.connect("activate", self._perform_search)

        search_btn = Gtk.Button(icon_name="system-search-symbolic")
        search_btn.connect("clicked", self._perform_search)

        header_box.append(self.search_entry)
        header_box.append(search_btn)
        group.add(header_box)

        # Results List
        self.results_group = Adw.PreferencesGroup()
        group.add(self.results_group)
        self._set_placeholder(_("Search for your city..."))

    def _set_placeholder(self, text):
        self.placeholder = Gtk.Label(label=text, margin_top=40)
        self.placeholder.add_css_class("dim-label")
        self.results_group.add(self.placeholder)

    def _perform_search(self, _widget):
        query = self.search_entry.get_text().strip()
        if not query:
            return

        # Logic to clear results
        if hasattr(self, "placeholder"):
            self.results_group.remove(self.placeholder)
        for row in self.results_rows:
            self.results_group.remove(row)
        self.results_rows.clear()

        cities = find_city(query, 5)  # Returns list of dicts

        if not cities:
            self._set_placeholder(_("No cities found."))
            return

        for city in cities:
            display = LocationData.format_display_name(city)
            row = Adw.ActionRow(
                title=display,
                subtitle=f"{city.get('latitude')}, {city.get('longitude')}",
            )
            row.set_activatable(True)
            # Store the raw dict on the row object for easy retrieval
            row.connect("activated", self._on_row_selected, city)
            self.results_group.add(row)
            self.results_rows.append(row)

    def _on_row_selected(self, row, city_data):
        self.callback(city_data)
        self.destroy()


# --- Main Application Window ---


class WeatherLocations(Adw.PreferencesWindow):
    def __init__(self, application, **kwargs):
        super().__init__(**kwargs)
        self.application = application
        self.location_model = LocationModel(settings)
        self.row_map = {}  # Track rows to prevent full UI rebuilds
        self._settings_handlers = []

        self.set_title(_("Locations"))
        self.set_transient_for(application)
        self.set_default_size(550, 450)

        self._build_ui()
        self._refresh_list()
        for key in ("automatic-location", "current-location", "selected-city", "added-cities"):
            handler_id = settings.settings.connect(
                f"changed::{key}",
                lambda *_: self._refresh_list(),
            )
            self._settings_handlers.append(handler_id)

    def _build_ui(self):
        page = Adw.PreferencesPage()
        self.location_grp = Adw.PreferencesGroup(title=_("Saved Locations"))

        add_btn = Gtk.Button(label=_("Add"), icon_name="list-add-symbolic")
        add_btn.connect(
            "clicked",
            lambda _: CitySearchDialog(self, self._handle_city_added).present(),
        )

        self.location_grp.set_header_suffix(add_btn)
        page.add(self.location_grp)
        self.add(page)

    def _refresh_list(self):
        """Clears and re-populates the location rows."""
        # Senior move: Clear rows efficiently
        while child := self.location_grp.get_row(0):
            if isinstance(child, Adw.ActionRow):
                self.location_grp.remove(child)
            else:
                break  # Keep the header suffix if it's there

        automatic_location = self.location_model.get_automatic_location()
        if settings.automatic_location and automatic_location is not None:
            row = self._create_row(
                automatic_location.to_dict(),
                subtitle=_("Current location"),
                removable=False,
                pinned=True,
            )
            self.location_grp.add(row)

        for location in self.location_model.get_manual_locations():
            row = self._create_row(location.to_dict())
            self.location_grp.add(row)

    def _create_row(
        self,
        data: Dict,
        subtitle: Optional[str] = None,
        removable: bool = True,
        pinned: bool = False,
    ) -> Adw.ActionRow:
        display_name = LocationData.format_display_name(data)
        coords = LocationData.get_coords_key(data)
        row_subtitle = subtitle or coords

        row = Adw.ActionRow(title=display_name, subtitle=row_subtitle, activatable=True)

        # Selection Indicator
        suffix_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        location = WeatherLocation.from_dict(data)
        if self.location_model.is_selected(location):
            indicator = Gtk.Image.new_from_icon_name("object-select-symbolic")
            indicator.add_css_class("accent")
            suffix_box.append(indicator)

        if pinned:
            pin_icon = Gtk.Image.new_from_icon_name("location-services-active-symbolic")
            pin_icon.add_css_class("dim-label")
            suffix_box.append(pin_icon)

        # Delete Button
        if removable:
            del_btn = Gtk.Button(icon_name="user-trash-symbolic", has_frame=False)
            del_btn.add_css_class("circular")
            del_btn.connect("clicked", self._handle_city_removed, data)
            suffix_box.append(del_btn)

        row.add_suffix(suffix_box)
        if location.source == "automatic":
            row.connect("activated", self._handle_automatic_location_switched, data)
        else:
            row.connect("activated", self._handle_city_switched, data)

        return row

    def _handle_city_added(self, city_dict: Dict):
        location = WeatherLocation.from_dict(city_dict)
        if not self.location_model.add_manual_location(location):
            self.add_toast(Adw.Toast(title=_("Location already exists")))
            return

        self.application.added_cities = settings.added_cities

        self._refresh_list()

        if len(settings.added_cities) == 1:
            self._handle_city_switched(None, location.to_dict())

    def _handle_city_switched(self, _row, city_dict: Dict):
        new_coords = LocationData.get_coords_key(city_dict)

        if settings.selected_city == new_coords:
            return

        self.location_model.set_selected_location(WeatherLocation.from_dict(city_dict))
        self._refresh_list()
        self.application._start_data_refresh()
        self.add_toast(Adw.Toast(title=_("Switched to {}").format(city_dict.get("name"))))

    def _handle_automatic_location_switched(self, _row, city_dict: Dict):
        settings.automatic_location = True
        if self.location_model.is_selected(WeatherLocation.from_dict(city_dict)):
            return
        self.location_model.select_automatic_location()
        self._refresh_list()
        self.application._start_data_refresh()
        self.add_toast(
            Adw.Toast(title=_("Switched to {}").format(city_dict.get("name")))
        )

    def _handle_city_removed(self, _btn, city_data: str):
        coords_to_remove = LocationData.get_coords_key(city_data)
        self.location_model.remove_manual_location(coords_to_remove)
        new_list = settings.added_cities
        self.application.added_cities = settings.added_cities

        if len(self.application.added_cities) == 0:
            self.application._start_data_refresh()

        # Reset selection if we deleted the active city
        if settings.selected_city == coords_to_remove and new_list:
            first_city = LocationData.from_storage_string(new_list[0])
            self.location_model.set_selected_location(WeatherLocation.from_dict(first_city))

            self.application._start_data_refresh()

        self._refresh_list()

    def destroy(self):
        for handler_id in self._settings_handlers:
            settings.settings.disconnect(handler_id)
        self._settings_handlers.clear()
        super().destroy()
