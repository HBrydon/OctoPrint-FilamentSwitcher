# coding=utf-8

from __future__ import absolute_import

import version

import octoprint.plugin

class FilamentSwitcherPlugin(
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.TemplatePlugin
):

    ##~~ StartupPlugin mixin
    def on_after_startup(self):
        self._logger.info("FilamentSwitcher %s started *******", self._settings.get(["vers"]))
        self._logger.info("Magic url is %s" % self._settings.get(["url"]))

    ##~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        return dict(url="https://en.wikipedia.org/wiki/Hello_world",
                    urlDE="https://de.wikipedia.org/wiki/Hallo-Welt-Programm",
                    urlES="https://es.wikipedia.org/wiki/Hola_mundo",
                    ver_maj=version.VER_MAJOR,
                    ver_min=version.VER_MINOR,
                    vers=version.VERSION)

    def get_template_configs(self):
        return [
          dict(type="navbar", custom_bindings=False),
          dict(type="settings", custom_bindings=False)
          ]

    #def get_template_vars(self):
    #    return dict(url=self._settings.get(["url"]))

    ##~~ AssetPlugin mixin
    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        self._logger.info("FilamentSwitcher get_assets() hit")
        return {
            "js": ["js/filamentswitcher.js"],
            "css": ["css/filamentswitcher.css"],
            "less": ["less/filamentswitcher.less"]
        }

    ##~~ Softwareupdate hook
    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "FilamentSwitcher": {
                "displayName": "FilamentSwitcher Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "HBrydon",
                "repo": "OctoPrint-FilamentSwitcher",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/HBrydon/OctoPrint-FilamentSwitcher/archive/{target_version}.zip",
            }
        }




# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Filament Switcher"
#__plugin_version__ = "0.1.0"
__plugin_version__ = version.VERSION
#__plugin_description__ = "FilamentSwitcher - control interface for Filament Switcher device"



# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3
#__plugin_pythoncompat__ = ">=3.7,<4"       # (from seed code)


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = FilamentSwitcherPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
