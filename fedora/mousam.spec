%global forgeurl https://github.com/EL-File4138/mousam

Name:           mousam
Version:        2.0.2
Release:        1%{?dist}
Summary:        GTK weather application

License:        GPL-3.0-or-later
URL:            %{forgeurl}
Source0:        %{url}/archive/refs/tags/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  appstream
BuildRequires:  desktop-file-utils
BuildRequires:  gettext
BuildRequires:  glib2-devel
BuildRequires:  gtk4
BuildRequires:  meson >= 0.61.0
BuildRequires:  python3-devel

Requires:       geoclue2
Requires:       geocode-glib
Requires:       gtk4
Requires:       libadwaita
Requires:       libgweather
Requires:       python3-gobject
Requires:       python3-requests

Conflicts:      gnome-weather

%description
Mousam is a GTK 4 and libadwaita weather application for Linux that shows
current conditions, hourly forecasts, and multi-day forecasts.

This fork also ships native-only integrations for automatic location via
GeoClue, background refresh, and GNOME Shell weather compatibility.

%prep
%autosetup -n %{name}-%{version}

%build
%meson -Dflatpak=false
%meson_build

%install
%meson_install
%find_lang %{name}

%check
%meson_test

%files -f %{name}.lang
%license COPYING
%doc README.md
%{_bindir}/mousam
%{_bindir}/io.github.amit9838.mousam.BackgroundService
%{_datadir}/applications/io.github.amit9838.mousam.desktop
%{_datadir}/applications/org.gnome.Weather.desktop
%{_datadir}/dbus-1/services/io.github.amit9838.mousam.service
%{_datadir}/dbus-1/services/io.github.amit9838.mousam.BackgroundService.service
%{_datadir}/dbus-1/services/org.gnome.Weather.service
%{_datadir}/glib-2.0/schemas/io.github.amit9838.mousam.gschema.xml
%{_datadir}/icons/hicolor/scalable/apps/io.github.amit9838.mousam.svg
%{_datadir}/icons/hicolor/scalable/mousam_icons/
%{_datadir}/icons/hicolor/symbolic/apps/io.github.amit9838.mousam-symbolic.svg
%{_datadir}/metainfo/io.github.amit9838.mousam.metainfo.xml
%{_datadir}/mousam/

%changelog
* Sat Mar 28 2026 EL File4138 <el-file4138@elfile4138.moe> - 1.5.1-1
- Add an RPM spec for native Fedora-style packaging
