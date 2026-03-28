data_conf = configuration_data()
data_conf.set('APP_ID', 'io.github.amit9838.mousam')
data_conf.set('BINDIR', join_paths(get_option('prefix'), get_option('bindir')))

desktop_file = i18n.merge_file(
        input: 'io.github.amit9838.mousam.desktop.in',
       output: 'io.github.amit9838.mousam.desktop',
         type: 'desktop',
       po_dir: '../po',
      install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_alias_file = i18n.merge_file(
        input: 'org.gnome.Weather.desktop.in',
       output: 'org.gnome.Weather.desktop',
         type: 'desktop',
       po_dir: '../po',
      install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
  test('Validate desktop alias file', desktop_utils, args: [desktop_alias_file])
endif

appstream_file = i18n.merge_file(
        input: 'io.github.amit9838.mousam.appdata.xml.in',
       output: 'io.github.amit9838.mousam.appdata.xml',
       po_dir: '../po',
      install: true,
  install_dir: join_paths(get_option('datadir'), 'appdata')
)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util, args: ['validate', appstream_file])
endif


install_data('io.github.amit9838.mousam.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas'),
)

install_data(
  'ShellWeatherIntegration.xml',
  install_dir: join_paths(get_option('datadir'), meson.project_name()),
)

configure_file(
  input: 'io.github.amit9838.mousam.service.in',
  output: 'io.github.amit9838.mousam.service',
  configuration: data_conf,
  install: true,
  install_dir: join_paths(get_option('datadir'), 'dbus-1/services'),
)

configure_file(
  input: 'org.gnome.Weather.service.in',
  output: 'org.gnome.Weather.service',
  configuration: data_conf,
  install: true,
  install_dir: join_paths(get_option('datadir'), 'dbus-1/services'),
)

configure_file(
  input: 'io.github.amit9838.mousam.BackgroundService.service.in',
  output: 'io.github.amit9838.mousam.BackgroundService.service',
  configuration: data_conf,
  install: true,
  install_dir: join_paths(get_option('datadir'), 'dbus-1/services'),
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file',
       compile_schemas,
       args: ['--strict', '--dry-run', meson.current_source_dir()])
endif

subdir('icons')
