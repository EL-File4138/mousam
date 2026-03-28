import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gettext import gettext as _, pgettext as C_
from gi.repository import Adw, Gtk

from .CORE_Helpers import create_toast
from .CORE_Logging import log_manager
from .CORE_locationModel import AUTO_LOCATION_ID, LocationModel
from .configs import AUTO_REFRESH_OPTIONS
from .settings import settings


class WeatherPreferences(Adw.PreferencesWindow):
    def __init__(self, application: Adw.Application, **kwargs):
        super().__init__(**kwargs)
        self.application = application
        self.set_transient_for(application)
        self.set_default_size(600, 500)
        self.set_title(_("Weather Preferences"))

        self._build_ui()
        self._bind_settings_to_ui()

    def _build_ui(self) -> None:
        appearance_page = Adw.PreferencesPage()
        appearance_page.set_title(_("Appearance"))
        appearance_page.set_icon_name("applications-graphics-symbolic")
        self.add(appearance_page)

        location_group = Adw.PreferencesGroup()
        location_group.set_title(_("Location"))
        appearance_page.add(location_group)
        self._add_automatic_location_row(location_group)

        general_group = Adw.PreferencesGroup()
        appearance_page.add(general_group)
        self._add_dynamic_background_row(general_group)
        self._add_notification_row(general_group)
        self._add_time_format_row(general_group)
        self._add_units_and_measurements_group(general_group)

        refresh_group = Adw.PreferencesGroup()
        refresh_group.set_title(_("Refresh and Integration"))
        refresh_group.set_margin_top(20)
        appearance_page.add(refresh_group)
        self._add_auto_refresh_row(refresh_group)
        self._add_shell_integration_row(refresh_group)
        self._add_background_refresh_row(refresh_group)

        advanced_page = Adw.PreferencesPage()
        advanced_page.set_title(_("Advanced"))
        advanced_page.set_icon_name("preferences-system-symbolic")
        self.add(advanced_page)

        debug_group = Adw.PreferencesGroup()
        debug_group.set_title(_("Logging &amp; Debugging"))
        advanced_page.add(debug_group)
        self._add_debug_mode_row(debug_group)
        self._add_open_logs_row(debug_group)
        self._add_clear_logs_row(debug_group)
        self._add_reset_row(advanced_page)

    def _add_automatic_location_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Automatic Location"),
            subtitle=_("Use your current location when a current-location entry is selected"),
            icon_name="find-location-symbolic",
            activatable=True,
        )
        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.connect("state-set", self._on_automatic_location_changed)
        row.add_suffix(switch)
        self._automatic_location_switch = switch
        parent.add(row)

    def _add_dynamic_background_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Dynamic Background"),
            subtitle=_("App background changes based on current weather conditions"),
            icon_name="preferences-color-symbolic",
            activatable=True,
        )
        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.connect("state-set", self._on_dynamic_bg_toggled)
        row.add_suffix(switch)
        self._dynamic_bg_switch = switch
        parent.add(row)

    def _add_notification_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Show Notifications"),
            subtitle=_("Show notification when weather is refreshed automatically"),
            icon_name="preferences-system-notifications-symbolic",
            activatable=True,
        )
        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.connect("state-set", self._on_notifications_toggled)
        row.add_suffix(switch)
        self._notification_switch = switch
        parent.add(row)

    def _add_time_format_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Time Format"),
            subtitle=_("Weather time format"),
            icon_name="preferences-system-time-symbolic",
            activatable=True,
        )
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.add_css_class("linked")
        button_box.set_valign(Gtk.Align.CENTER)
        row.add_suffix(button_box)

        btn_24h = Gtk.ToggleButton.new_with_label(_("24 Hour"))
        btn_24h.set_size_request(80, 20)
        btn_24h.set_css_classes(["btn-sm"])
        btn_24h.connect("clicked", self._on_24h_clock_toggled, True)

        btn_12h = Gtk.ToggleButton.new_with_label(_("AM / PM"))
        btn_12h.set_size_request(80, 20)
        btn_12h.set_css_classes(["btn-sm"])
        btn_12h.set_group(btn_24h)
        btn_12h.connect("clicked", self._on_24h_clock_toggled, False)

        button_box.append(btn_24h)
        button_box.append(btn_12h)
        self._time_btn_24h = btn_24h
        self._time_btn_12h = btn_12h
        parent.add(row)

    def _add_units_and_measurements_group(self, parent: Adw.PreferencesGroup) -> None:
        group = Adw.PreferencesGroup()
        group.set_margin_top(20)
        group.set_title(_("Units &amp; Measurements"))
        parent.add(group)

        unit_row = Adw.ActionRow(
            title=_("System Unit"),
            subtitle=_("Metric (C, mm, km/h) or Imperial (F, inches, mph) [restart required]"),
            icon_name="power-profile-balanced-symbolic",
            activatable=True,
        )
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.add_css_class("linked")
        button_box.set_valign(Gtk.Align.CENTER)

        btn_metric = Gtk.ToggleButton.new_with_label(_("Metric"))
        btn_metric.set_size_request(80, 20)
        btn_metric.set_css_classes(["btn-sm"])
        btn_metric.connect("clicked", self._on_unit_toggled, "metric")

        btn_imperial = Gtk.ToggleButton.new_with_label(_("Imperial"))
        btn_imperial.set_size_request(80, 20)
        btn_imperial.set_css_classes(["btn-sm"])
        btn_imperial.set_group(btn_metric)
        btn_imperial.connect("clicked", self._on_unit_toggled, "imperial")

        button_box.append(btn_metric)
        button_box.append(btn_imperial)
        unit_row.add_suffix(button_box)
        group.add(unit_row)
        self._unit_btn_metric = btn_metric
        self._unit_btn_imperial = btn_imperial

        prec_row = Adw.ActionRow(
            title=_("Precipitation in inches"),
            subtitle=_("This option works better in heavy precipitation"),
            icon_name="function-linear-symbolic",
            activatable=True,
        )
        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.connect("state-set", self._on_precip_unit_toggled)
        prec_row.add_suffix(switch)
        self._precip_switch = switch
        group.add(prec_row)

    def _add_auto_refresh_row(self, parent: Adw.PreferencesGroup) -> None:
        labels = Gtk.StringList.new([label for _value, label in AUTO_REFRESH_OPTIONS])
        row = Adw.ComboRow(
            title=_("Auto Refresh"),
            subtitle=_("Automatically refresh weather data at a set interval"),
            icon_name="view-refresh-symbolic",
            model=labels,
        )
        row.connect("notify::selected", self._on_auto_refresh_changed)
        self._auto_refresh_row = row
        parent.add(row)

    def _add_shell_integration_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("GNOME Shell Integration"),
            subtitle=_("Show the selected location in the GNOME Shell weather section"),
            icon_name="weather-clear-symbolic",
            activatable=True,
        )
        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.connect("state-set", self._on_shell_integration_changed)
        row.add_suffix(switch)
        self._shell_integration_switch = switch
        parent.add(row)

    def _add_background_refresh_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Background Refresh"),
            subtitle=_("Refresh weather in the background when the main window is closed"),
            icon_name="view-refresh-symbolic",
            activatable=True,
        )
        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.connect("state-set", self._on_background_refresh_changed)
        row.add_suffix(switch)
        self._background_refresh_row = row
        self._background_refresh_switch = switch
        parent.add(row)

    def _add_debug_mode_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Debug Mode"),
            subtitle=_("Enable verbose logging and console output"),
            icon_name="utilities-terminal-symbolic",
            activatable=True,
        )
        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.connect("state-set", self._on_debug_mode_toggled)
        row.add_suffix(switch)
        self._debug_switch = switch
        parent.add(row)

    def _add_open_logs_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Open Logs Folder"),
            subtitle=_("Access the application log files"),
            icon_name="folder-open-symbolic",
        )
        btn = Gtk.Button(icon_name="folder-open-symbolic", valign=Gtk.Align.CENTER)
        btn.add_css_class("flat")
        btn.connect("clicked", self._on_open_logs_clicked)
        row.add_suffix(btn)
        parent.add(row)

    def _add_clear_logs_row(self, parent: Adw.PreferencesGroup) -> None:
        row = Adw.ActionRow(
            title=_("Clear Log File"),
            subtitle=_("Delete all contents of the current log file"),
            icon_name="edit-clear-all-symbolic",
        )
        btn = Gtk.Button(icon_name="edit-clear-all-symbolic", valign=Gtk.Align.CENTER)
        btn.add_css_class("flat")
        btn.connect("clicked", self._on_clear_logs_clicked)
        row.add_suffix(btn)
        parent.add(row)

    def _add_reset_row(self, parent: Adw.PreferencesPage) -> None:
        group = Adw.PreferencesGroup()
        group.set_title(_("Data Management"))
        group.set_margin_top(20)
        parent.add(group)

        row = Adw.ActionRow(
            title=_("Reset to Default"),
            subtitle=_("Clear all preferences and restore default values"),
            icon_name="object-rotate-left-symbolic",
        )
        btn = Gtk.Button.new_with_label(_("Reset..."))
        btn.set_valign(Gtk.Align.CENTER)
        btn.add_css_class("destructive-action")
        btn.connect("clicked", self._on_reset_clicked)
        row.add_suffix(btn)
        group.add(row)

    def _bind_settings_to_ui(self) -> None:
        self._automatic_location_switch.set_active(settings.automatic_location)
        self._dynamic_bg_switch.set_active(settings.is_using_dynamic_bg)
        self._notification_switch.set_active(settings.show_notifications)
        self._precip_switch.set_active(settings.is_using_inch_for_prec)
        self._debug_switch.set_active(settings.debug_mode)
        self._shell_integration_switch.set_active(settings.shell_integration_enabled)
        self._background_refresh_switch.set_active(settings.background_refresh_enabled)

        if settings.is_using_24h_clock:
            self._time_btn_24h.set_active(True)
        else:
            self._time_btn_12h.set_active(True)

        if settings.unit == "metric":
            self._unit_btn_metric.set_active(True)
        else:
            self._unit_btn_imperial.set_active(True)

        selected_idx = 0
        for i, (value, _label) in enumerate(AUTO_REFRESH_OPTIONS):
            if value == settings.auto_refresh_interval:
                selected_idx = i
                break
        self._auto_refresh_row.set_selected(selected_idx)
        self._update_background_refresh_sensitivity()

        native_available = not settings.IS_FLATPAK
        self._shell_integration_switch.set_active(
            settings.shell_integration_enabled and native_available
        )
        self._shell_integration_switch.set_sensitive(native_available)
        self._background_refresh_switch.set_active(
            settings.background_refresh_enabled and native_available
        )
        if not native_available:
            self._background_refresh_row.set_subtitle(_("Unavailable in Flatpak builds"))

    def _on_dynamic_bg_toggled(self, _switch: Gtk.Switch, state: bool) -> None:
        settings.is_using_dynamic_bg = state
        self._start_refresh_thread()

    def _on_notifications_toggled(self, _switch: Gtk.Switch, state: bool) -> None:
        settings.show_notifications = state

    def _on_24h_clock_toggled(self, _button: Gtk.ToggleButton, use_24h: bool) -> None:
        settings.is_using_24h_clock = use_24h
        self._start_refresh_thread()

    def _on_unit_toggled(self, _button: Gtk.ToggleButton, unit: str) -> None:
        settings.unit = unit
        self.add_toast(create_toast(_("Switched to - {}").format(unit.capitalize()), 1))

    def _on_precip_unit_toggled(self, _switch: Gtk.Switch, state: bool) -> None:
        settings.is_using_inch_for_prec = state
        self._start_refresh_thread()

    def _on_auto_refresh_changed(self, combo: Adw.ComboRow, _pspec) -> None:
        idx = combo.get_selected()
        if idx >= len(AUTO_REFRESH_OPTIONS):
            return

        interval_val, _interval_label = AUTO_REFRESH_OPTIONS[idx]
        settings.auto_refresh_interval = interval_val
        if interval_val <= 0:
            settings.background_refresh_enabled = False
            self._background_refresh_switch.set_active(False)
        self._update_background_refresh_sensitivity()

        message = _("Auto refresh disabled")
        if interval_val > 0:
            message = _("Auto refresh every {} min").format(interval_val)
        self.add_toast(create_toast(message, 1))

    def _on_automatic_location_changed(self, _switch: Gtk.Switch, state: bool) -> None:
        location_model = LocationModel(settings)
        settings.automatic_location = state

        if not state and settings.selected_city in ("", AUTO_LOCATION_ID):
            location = location_model.get_primary_manual_location()
            if location is not None:
                settings.selected_city = location.coords_key

        self.application._start_data_refresh()
        message = _("Automatic location enabled") if state else _("Automatic location disabled")
        self.add_toast(create_toast(message, 1))

    def _on_shell_integration_changed(self, _switch: Gtk.Switch, state: bool) -> bool:
        if settings.IS_FLATPAK:
            return True
        settings.shell_integration_enabled = state
        message = _("GNOME Shell integration enabled") if state else _("GNOME Shell integration disabled")
        self.add_toast(create_toast(message, 1))
        return False

    def _on_background_refresh_changed(self, _switch: Gtk.Switch, state: bool) -> bool:
        if settings.IS_FLATPAK:
            return True
        settings.background_refresh_enabled = state
        message = _("Background refresh enabled") if state else _("Background refresh disabled")
        self.add_toast(create_toast(message, 1))
        return False

    def _update_background_refresh_sensitivity(self) -> None:
        if settings.IS_FLATPAK:
            self._background_refresh_row.set_sensitive(False)
            self._background_refresh_switch.set_sensitive(False)
            return
        enabled = settings.auto_refresh_interval > 0
        self._background_refresh_row.set_sensitive(enabled)
        self._background_refresh_switch.set_sensitive(enabled)

    def _on_debug_mode_toggled(self, _switch: Gtk.Switch, state: bool) -> None:
        settings.debug_mode = state
        log_manager.update_level()

    def _on_open_logs_clicked(self, _button: Gtk.Button) -> None:
        log_manager.open_log_folder()

    def _on_clear_logs_clicked(self, _button: Gtk.Button) -> None:
        if log_manager.clear_logs():
            self.add_toast(create_toast(_("Logs cleared"), 1))
        else:
            self.add_toast(create_toast(_("Failed to clear logs"), 1))

    def _on_reset_clicked(self, _button: Gtk.Button) -> None:
        dialog = Adw.MessageDialog.new(
            self,
            _("Reset Settings?"),
            _(
                "This will restore all settings to default and will clear your saved cities. "
                "This action cannot be undone."
            ),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("reset", _("Reset"))
        dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_reset_dialog_response)
        dialog.present()

    def _on_reset_dialog_response(self, _dialog: Adw.MessageDialog, response: str) -> None:
        if response == "reset":
            self._perform_reset()

    def _perform_reset(self) -> None:
        settings.reset_to_defaults()
        self._bind_settings_to_ui()
        self.add_toast(create_toast(_("Preferences have been reset"), 1))
        self._start_refresh_thread()

    def _start_refresh_thread(self) -> None:
        thread = threading.Thread(
            target=self.application._start_data_refresh,
            name="refresh_after_preference_change",
            daemon=True,
        )
        thread.start()
