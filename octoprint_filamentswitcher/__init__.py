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
                    vers=version.VERSION,
                    zDistance=80,
                    unload_length=500,
                    unload_speed=1600,
                    load_length=50,
                    load_speed=60,
                    pause_before_park=False,
                    retract_before_park=False,
                    home_before_park=False,
                    y_park=0,
                    x_park=0,
                    z_lift_relative=30,
                    park_speed=5000
                    )

    #def get_template_vars(self):
    #    return dict(url=self._settings.get(["url"]))

    def get_template_configs(self):
        return [
          dict(type="navbar", custom_bindings=False),
          dict(type="settings", custom_bindings=False)
          ]


    ##~~ AssetPlugin mixin
    def get_assets(self):
        return dict(
            js=["js/filamentswitcher.js"],
            css=["css/filamentswitcher.css"],
            less=["less/filamentswitcher.less"]
        )

    # Starting code came from "Rewrite M600 plugin"
    def rewrite_m600(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if gcode and gcode == "M600":
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="popup", msg="Please change the filament and resume the print"))
            comm_instance.setPause(True)
            cmd = [("M117 Filament Change",),"G91","M83", "G1 Z+"+str(self._settings.get(["zDistance"]))+" E-0.8 F4500", "M82", "G90", "G1 X0 Y0"]
        return cmd

    # Starting code came from "Rewrite M600 plugin"
    def after_resume(self, comm_instance, phase, cmd, parameters, tags=None, *args, **kwargs):
        if cmd and cmd == "resume":
            if(comm_instance.pause_position.x):
                cmd = []
                cmd =["M83","G1 E-0.8 F4500", "G1 E0.8 F4500", "G1 E0.8 F4500", "M82", "G90", "G92 E"+str(comm_instance.pause_position.e), "M83", "G1 X"+str(comm_instance.pause_position.x)+" Y"+str(comm_instance.pause_position.y)+" Z"+str(comm_instance.pause_position.z)+" F4500"]
                if(comm_instance.pause_position.f):
                    cmd.append("G1 F" + str(comm_instance.pause_position.f))
                comm_instance.commands(cmd)
            comm_instance.setPause(False)
        return

    ##~~ Softwareupdate hook
    def get_update_information(self):
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




# Control properties described at
#  https://docs.octoprint.org/en/master/plugins/controlproperties.html
#
#__plugin_name__
#__plugin_version__
#__plugin_description__
#__plugin_author__
#__plugin_url__
#__plugin_license__
#__plugin_privacypolicy__
#__plugin_pythoncompat__
#__plugin_implementation__
#__plugin_hooks__
#__plugin_check__
#__plugin_load__
#__plugin_unload__
#__plugin_enable__
#__plugin_disable__
#__plugin_settings_overlay__


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Filament Switcher"
#__plugin_version__ = "0.1.0"
__plugin_version__ = version.VERSION
#__plugin_description__ = "FilamentSwitcher - control interface for Filament Switcher device"

__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3
#__plugin_pythoncompat__ = ">=3.7,<4"  # Needed for async/await


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = FilamentSwitcherPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        # Described at https://docs.octoprint.org/en/master/plugins/hooks.html#octoprint-comm-protocol-gcode-phase
        "octoprint.comm.protocol.gcode.queuing":        __plugin_implementation__.rewrite_m600,
        "octoprint.comm.protocol.atcommand.queuing":    __plugin_implementation__.after_resume,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
