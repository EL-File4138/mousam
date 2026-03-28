from gi.repository import Gio


class Settings:
    _instance = None
    APP_ID = "io.github.amit9838.mousam"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance.init_settings()
        return cls._instance

    def init_settings(self):
        self.settings = Gio.Settings(self.APP_ID)

    def reset_to_defaults(self):
        """Resets all keys in the schema to their default values."""
        for key in self.settings.list_keys():
            self.settings.reset(key)

    @property
    def added_cities(self):
        return self.settings.get_strv("added-cities")

    @added_cities.setter
    def added_cities(self, value):
        self.settings.set_strv("added-cities", value)

    @property
    def selected_city(self):
        return self.settings.get_string("selected-city")

    @selected_city.setter
    def selected_city(self, value):
        self.settings.set_string("selected-city", value)

    @property
    def is_using_dynamic_bg(self):
        return self.settings.get_boolean("use-gradient-bg")

    @is_using_dynamic_bg.setter
    def is_using_dynamic_bg(self, value):
        self.settings.set_boolean("use-gradient-bg", value)

    @property
    def is_using_inch_for_prec(self):
        return self.settings.get_boolean("use-inch-for-prec")

    @is_using_inch_for_prec.setter
    def is_using_inch_for_prec(self, value):
        self.settings.set_boolean("use-inch-for-prec", value)

    @property
    def is_using_24h_clock(self):
        return self.settings.get_boolean("use-24h-clock")

    @is_using_24h_clock.setter
    def is_using_24h_clock(self, value):
        self.settings.set_boolean("use-24h-clock", value)

    @property
    def window_width(self):
        return self.settings.get_int("window-width")

    @window_width.setter
    def window_width(self, value):
        self.settings.set_int("window-width", value)

    @property
    def window_height(self):
        return self.settings.get_int("window-height")

    @window_height.setter
    def window_height(self, value):
        self.settings.set_int("window-height", value)

    @property
    def window_maximized(self):
        return self.settings.get_boolean("window-maximized")

    @window_maximized.setter
    def window_maximized(self, value):
        self.settings.set_boolean("window-maximized", value)

    @property
    def auto_refresh_interval(self):
        return self.settings.get_int("auto-refresh-interval")

    @auto_refresh_interval.setter
    def auto_refresh_interval(self, value):
        self.settings.set_int("auto-refresh-interval", value)

    @property
    def unit(self):
        return self.settings.get_string("unit")

    @unit.setter
    def unit(self, value):
        self.settings.set_string("unit", value)

    @property
    def automatic_location(self):
        return self.settings.get_boolean("automatic-location")

    @automatic_location.setter
    def automatic_location(self, value):
        self.settings.set_boolean("automatic-location", value)

    @property
    def current_location(self):
        return self.settings.get_string("current-location")

    @current_location.setter
    def current_location(self, value):
        self.settings.set_string("current-location", value)

    @property
    def background_refresh_enabled(self):
        return self.settings.get_boolean("background-refresh-enabled")

    @background_refresh_enabled.setter
    def background_refresh_enabled(self, value):
        self.settings.set_boolean("background-refresh-enabled", value)

    @property
    def last_refresh_timestamp(self):
        return self.settings.get_int64("last-refresh-timestamp")

    @last_refresh_timestamp.setter
    def last_refresh_timestamp(self, value):
        self.settings.set_int64("last-refresh-timestamp", value)

    @property
    def last_refresh_status(self):
        return self.settings.get_string("last-refresh-status")

    @last_refresh_status.setter
    def last_refresh_status(self, value):
        self.settings.set_string("last-refresh-status", value)

    @property
    def shell_integration_enabled(self):
        return self.settings.get_boolean("shell-integration-enabled")

    @shell_integration_enabled.setter
    def shell_integration_enabled(self, value):
        self.settings.set_boolean("shell-integration-enabled", value)


def get_settings():
    return Settings()


settings = get_settings()
