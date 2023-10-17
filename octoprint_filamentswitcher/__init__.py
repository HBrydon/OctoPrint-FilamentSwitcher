# coding=utf-8

from __future__ import absolute_import

import octoprint.plugin
import time

from enum import Enum

from octoprint_filamentswitcher.include import pluginversion
from octoprint_filamentswitcher.include.serialUSBio import serStatus, SerialUSBio

# Some info available at:
#  https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


#gcodeCounter = 0


class PrinterStatus(Enum):
    UNKNOWN = 0
    IDLING = 1
    PRINTING = 2

#class FilSwitcherStatus(Enum):
#    UNKNOWN = 0
#    IDLING = 1
#    PRINTING = 2


class FilamentSwitcherPlugin(
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.TemplatePlugin
):
    def __init__(self):
        #self._logger.info("**** FilamentSwitcher __init__() called")
        self.printerstatus = PrinterStatus.UNKNOWN
        self.gcodeCounter = 0

    def __del__(self):
        #self._logger.info("**** FilamentSwitcher __del__() called")
        self.closeUSBinterface()

    def initialize(self):
        self._logger.info(f"{bcolors.BOLD}**** FilamentSwitcher initialize() called{bcolors.ENDC}")
        self.printerstatus = PrinterStatus.IDLING
        self.openUSBinterface(self._settings.get(["fsPort"]), self._settings.get(["fsBaudRate"]), self._settings.get(["fsLogfile"]))

    ##~~ StartupPlugin mixin
    def on_after_startup(self):
        #self._logger.info("**** FilamentSwitcher %s started", pluginversion.VERSION)
        self._logger.info(f"{bcolors.BOLD}**** FilamentSwitcher {pluginversion.VERSION} started{bcolors.ENDC}")
        #self._logger.info("Magic url is %s" % self._settings.get(["url"]))
        ##self.openUSBinterface(self._settings.get(["fsPort"]), self._settings.get(["fsLogfile"]))
        #self.openUSBinterface(self._settings.get(["fsPort"]), self._settings.get(["fsBaudRate"]), self._settings.get(["fsLogfile"]))


    #def initialize(self):
    #    GPIO.setwarnings(True)
    #    # flag defining that the filament change command has been sent to printer, this does not however mean that
    #    # filament change sequence has been started
    #    self.changing_filament_initiated = False
    #    # flag defining that the filament change sequence has been started and the M600 command has been se to printer
    #    self.changing_filament_command_sent = False
    #    # flag defining that the filament change sequence has been started and the printer is waiting for user
    #    # to put in new filament
    #    self.paused_for_user = False
    #    # flag to prevent double detection
    #    self.changing_filament_started = False

    ##~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        return dict(
            fsPort="/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0",
            fsBaudRate=115200,
            fsLogfile="/home/pi/workarea/OctoPrint-FilamentSwitcher/USBsendrecv.log",
            url="https://en.wikipedia.org/wiki/Hello_world",
            urlDE="https://de.wikipedia.org/wiki/Hallo-Welt-Programm",
            urlES="https://es.wikipedia.org/wiki/Hola_mundo",
            #ver_maj=pluginversion.VER_MAJOR,
            #ver_min=pluginversion.VER_MINOR,
            #vers=pluginversion.VERSION,
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
            css=["css/filamentswitcher.css"]
            #less=["less/filamentswitcher.less"]
        )

    def monitor_gcode_queue(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if not hasattr(self, 'gcodeCounter'):
            self.gcodeCounter = 0
        self.gcodeCounter += 1
        msg = self.readUSBmessage()
        if self.gcodeCounter == 10000:            # *** Test test
            self.sendUSBmessage("FSEcho FS: FRO") # *** Test test
        if self.gcodeCounter % 697:               # *** Test test
            self.sendUSBmessage(f"FSPStat ?banana?")  # TODO: Fix this
        if msg != "":
            self._logger.info(f"Inbound: {msg}")
            fsCmdLine = msg.split()
            if len(fsCmdLine) > 1:
                if fsCmdLine[0] == "FS:":
                    self._logger.info(f"FS command is {fsCmdLine[1:]}")
            if msg == "FS: FRO" || msg == "FRO":
                self._logger.warn(f"FS FRO Event - DING DING DING")
                #comm_instance.setPause(True)  # Some day but not yet...
                self.gcodeCounter = 0
                # TODO:
                # set FS status
                # set printer to 'pause'
                # etc. per info below
        if gcode:
            if self.gcodeCounter < 200:
                self.sendUSBmessage(cmd)
            elif gcode == "M104": # Set hotend temp (no wait)
                self.sendUSBmessage(cmd)
                self.gcodeCounter = 0
            elif gcode == "M109": # Set hotend temp (wait)
                self.sendUSBmessage(cmd)
                self.gcodeCounter = 0
            elif gcode == "M117": # Send message to LCD
                # TODO: Capture layer info
                #2023-10-13 13:37:21,100 - serialUSBlogger - INFO - Send: M117 DASHBOARD_LAYER_INDICATOR 1
                #2023-10-13 13:37:21,108 - serialUSBlogger - INFO - Send: M117 0% L=0/166
                self.sendUSBmessage(cmd)
            #elif gcode.startswith("M"):
            #    self.sendUSBmessage(cmd)
            elif gcode != "G0" and gcode != "G1":
                self.sendUSBmessage(cmd)
        # TODO:
        # Need to check if FS has notified EndOfFilament event
        # Need to capture:
        # - hotend temperature
        # - comm_instance.pause_position.x
        # - comm_instance.pause_position.y
        # - comm_instance.pause_position.z
        # Looks like these are documented in
        #  /home/pi/workarea/OctoPrint/docs/features/gcode_scripts.rst
        # Looks like these are defined in
        #  /home/pi/workarea/OctoPrint/src/octoprint/util/comm.py
        # comm_instance.setPause(True)
        # change machine state, send to FS
        # Send commands to FS to back up 'x' mm
        # change machine state, send to FS
        # Back out filament past extruder
        # Move extruder to purge location
        # Wait for FS to feed new filament stream to extruder
        # Feed new stream to hotend, run purge process
        # change machine state, send to FS
        # Move hotend back to saved x, y, z location
        # change machine state, send to FS
        # comm_instance.setPause(False)
        # change machine state, send to FS
        # Resume printing
        # change machine state, send to FS (?)


    ## Starting code came from "Rewrite M600 plugin"
    #def rewrite_m600(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
    #    if gcode and gcode == "M600":
    #        self._plugin_manager.send_plugin_message(self._identifier, dict(type="popup", msg="Please change the filament and resume the print"))
    #        comm_instance.setPause(True)
    #        cmd = [("M117 Filament Change",),"G91","M83", "G1 Z+"+str(self._settings.get(["zDistance"]))+" E-0.8 F4500", "M82", "G90", "G1 X0 Y0"]
    #    return cmd

    ## Starting code came from "Rewrite M600 plugin"
    #def after_resume(self, comm_instance, phase, cmd, parameters, tags=None, *args, **kwargs):
    #    if cmd and cmd == "resume":
    #        if(comm_instance.pause_position.x):
    #            cmd = []
    #            cmd =["M83","G1 E-0.8 F4500", "G1 E0.8 F4500", "G1 E0.8 F4500", "M82", "G90", "G92 E"+str(comm_instance.pause_position.e), "M83", "G1 X"+str(comm_instance.pause_position.x)+" Y"+str(comm_instance.pause_position.y)+" Z"+str(comm_instance.pause_position.z)+" F4500"]
    #            if(comm_instance.pause_position.f):
    #                cmd.append("G1 F" + str(comm_instance.pause_position.f))
    #            comm_instance.commands(cmd)
    #        comm_instance.setPause(False)
    #    return

    def openUSBinterface(self, fsPort, fsBaudRate, fsLogfile):
        #self.fsDev = serialUSBio.SerialUSBio(fsPort, fsBaudRate, fsLogfile)
        if not hasattr(self, 'fsDev'):
            self.fsDev = None
        if self.fsDev == None:
            self.fsDev = SerialUSBio(fsPort, fsLogfile)
            self.fsDev.openSerial()
        #if not self.fsDev.isOpen():
        #    self.fsDev.openSerial()
        if(self.fsDev.getStatus() == serStatus.OPEN):
            #self.fsDev.start()
            self.sendUSBmessage("FSHello")
            #self.sendUSBmessage("FSStatus from octoprint")
            #self.sendCurrentState()
            time.sleep(1.0)
            #self.sendUSBmessage("FSEcho Now is the time for all good men to come to the aid of the party!")
            #self._logger.info(self.fsDev.read_line_from_queue())
            #self._logger.info(self.fsDev.read_line_from_queue())
            #self._logger.info(self.readUSBmessage())
            self._logger.info(f"{bcolors.BOLD}{self.readUSBmessage()}{bcolors.ENDC}")
        else:
            self._logger.info(f"{bcolors.BOLD}Serial connection {fsPort} is not open!{bcolors.ENDC}")

    def sendUSBmessage(self, msg):
        self.fsDev.write_line(msg)

    def readUSBmessage(self):
        return self.fsDev.read_line_from_queue()

    def sendCurrentState(self):
        self.sendUSBmessage(f"FSPStat {self.printerstatus}")

    def closeUSBinterface(self):
        self.fsDev.close()
        self.fsDev = None

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

                # Based on code found in
                #  OctoPrint-Smart-Filament-Sensor
                # stable releases
                "stable_branch" : {
                    "name":"Stable",
                    "branch":"main",
                    "comittish":["main"]
                    },

                # release candidates
                "prerelease_branches" : [
                    dict(
                        name="Release Candidate",
                        branch="PreRelease",
                        comittish=["PreRelease"],
                    )
                ],

                # update method: pip
                "pip": "https://github.com/HBrydon/OctoPrint-FilamentSwitcher/archive/{target_version}.zip"
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
__plugin_version__ = pluginversion.VERSION
#__plugin_description__ = "FilamentSwitcher - control interface for Filament Switcher device"

__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3
#__plugin_pythoncompat__ = ">=3.7,<4"  # Needed for async/await


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = FilamentSwitcherPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        # Described at https://docs.octoprint.org/en/master/plugins/hooks.html#octoprint-comm-protocol-gcode-phase
        "octoprint.comm.protocol.gcode.queuing":        __plugin_implementation__.monitor_gcode_queue,
        #"octoprint.comm.protocol.atcommand.queuing":    __plugin_implementation__.after_resume,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }

def main():
    #serialMgr = SerialUSBio("/dev/ttyUSB0", 115200)
    serialMgr = serialUSBio.SerialUSBio("/dev/ttyUSB0", "inout.log")
    try:
        serialMgr.start()
        serialMgr.write_line("FSHello")
        serialMgr.write_line("FSBlork")
        serialMgr.write_line("ON")
        serialMgr.write_line("FSNetInfo")
        serialMgr.write_line("FSInfo")

        while True:
            time.sleep(0.5)
            while serialMgr.queue_count() > 0:
                # Read data from the queue
                print(serialMgr.read_line_from_queue())
            text = input("Enter: ")
            serialMgr.write_line(text)
    except EOFError:
        print("EOF detected")
        serialMgr.stop()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        serialMgr.stop()

if __name__ == "__main__":
    main()

