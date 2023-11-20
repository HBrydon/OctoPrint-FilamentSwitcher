# coding=utf-8

from __future__ import absolute_import

import octoprint.plugin
import time

from enum import Enum

from octoprint_filamentswitcher.include import pluginversion
from octoprint_filamentswitcher.include.serialUSBio import serStatus, SerialUSBio


# A short collection of regexes for communication parsing...
# (based on info in util/comm.py)

regex_float_pattern = r"[-+]?[0-9]*\.?[0-9]+"
regex_positive_float_pattern = r"[+]?[0-9]*\.?[0-9]+"
regex_int_pattern = r"\d+"

#regex_command = re.compile(   # Regex for a GCODE command.
#    r"^\s*((?P<codeGM>[GM]\d+)(\.(?P<subcode>\d+))?|(?P<codeT>T)\d+|(?P<codeF>F)\d+)"
#)


#regex_float = re.compile(regex_float_pattern)  # Regex for a float value.

regexes_parameters = {  # Regexes for parsing various GCode command parameters...
    "floatE": re.compile(r"(^|[^A-Za-z])[Ee](?P<value>%s)" % regex_float_pattern),
    "floatF": re.compile(r"(^|[^A-Za-z])[Ff](?P<value>%s)" % regex_float_pattern),
    "floatP": re.compile(r"(^|[^A-Za-z])[Pp](?P<value>%s)" % regex_float_pattern),
    "floatR": re.compile(r"(^|[^A-Za-z])[Rr](?P<value>%s)" % regex_float_pattern),
    "floatS": re.compile(r"(^|[^A-Za-z])[Ss](?P<value>%s)" % regex_float_pattern),
    "floatX": re.compile(r"(^|[^A-Za-z])[Xx](?P<value>%s)" % regex_float_pattern),
    "floatY": re.compile(r"(^|[^A-Za-z])[Yy](?P<value>%s)" % regex_float_pattern),
    "floatZ": re.compile(r"(^|[^A-Za-z])[Zz](?P<value>%s)" % regex_float_pattern),
    "intN": re.compile(r"(^|[^A-Za-z])[Nn](?P<value>%s)" % regex_int_pattern),
    "intS": re.compile(r"(^|[^A-Za-z])[Ss](?P<value>%s)" % regex_int_pattern),
    "intT": re.compile(r"(^|[^A-Za-z])[Tt](?P<value>%s)" % regex_int_pattern),
}


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


class PrinterStatus(Enum):
    UNKNOWN = 0
    IDLING = 1
    PRINTING = 2

class XYZAxisStatus(Enum):
    UNKNOWN = 0
    RELATIVE = 1
    ABSOLUTE = 2

class EAxisStatus(Enum):
    UNKNOWN = 0
    RELATIVE = 1
    ABSOLUTE = 2

class RunStatus(Enum):
    MONITOR_G0G1 = 0
    #LOOKFORG0G1 = 1
    WAITFORRETRACT = 2
    RELOAD_PARKX0Y0 = 3
    RELOAD_PURGE_RETURN = 4
    #RESUME = 5
    #PHASE4 = 6
    #PHASE5 = 7
    #PHASE6 = 8
    #PHASE7 = 9
    #PAUSEPRINTER = 10
    #PRINTERPAUSED = 11


class FilamentSwitcherPlugin(
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.TemplatePlugin
):
    def __init__(self):
        #self._logger.info("**** FilamentSwitcher __init__() called")
        self._printerstatus = PrinterStatus.UNKNOWN
        self._gcodeCounter = 0

    def __del__(self):
        #self._logger.info("**** FilamentSwitcher __del__() called")
        self.closeUSBinterface()

    def initialize(self):
        self._logger.info(f"{bcolors.BOLD}**** FilamentSwitcher initialize() called{bcolors.ENDC}")
        self._printerstatus = PrinterStatus.IDLING
        self.openUSBinterface(self._settings.get(["fsPort"]), self._settings.get(["fsBaudRate"]), self._settings.get(["fsLogfile"]))
        self._eAxisStatus = EAxisStatus.UNKNOWN
        self._xyzAxisStatus = XYZAxisStatus.UNKNOWN
        self._fsState = RunStatus.MONITOR_G0G1

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
        if not hasattr(self, '_gcodeCounter'):
            self._gcodeCounter = 0
        if not hasattr(self, '_savedGCode'):
            self._savedGCode = []
        if not hasattr(self, '_fsState'):
            self._fsState = RunStatus.MONITOR_G0G1
        if self._fsState == RunStatus.MONITOR_G0G1:
            if gcode:
                self._gcodeCounter += 1
                if self._gcodeCounter == 500:                                 # *** Test test
                    self.sendUSBmessage("FSEcho FS: FRO   **|**|**|**|**|**") # *** Test test
                    self._gcodeCounter = 0                                    # *** Test test
                #if 100 == self._gcodeCounter % 497:                           # *** Test test
                #    x = comm_instance.pause_position.x
                #    y = comm_instance.pause_position.y
                #    z = comm_instance.pause_position.z
                #    t = comm_instance.pause_position.t
                #    #t = comm_instance.pause_temperature
                #    self.sendUSBmessage(f"FSPStat gcode:{gcode} X{x} Y{y} Z{z} T{t}")
                if gcode == "M82": # Absolute E positioning
                    self._eAxisStatus = EAxisStatus.ABSOLUTE
                    self.sendUSBmessage(cmd)
                elif gcode == "M83": # Relative E positioning
                    self._eAxisStatus = EAxisStatus.RELATIVE
                    self.sendUSBmessage(cmd)
                elif gcode == "G90": # Absolute XYZE positioning
                    self._eAxisStatus = EAxisStatus.ABSOLUTE
                    self._xyzAxisStatus = XYZAxisStatus.ABSOLUTE
                    self.sendUSBmessage(cmd)
                elif gcode == "G91": # Relative XYZE positioning
                    self._eAxisStatus = EAxisStatus.RELATIVE
                    self._xyzAxisStatus = XYZAxisStatus.RELATIVE
                    self.sendUSBmessage(cmd)
                elif gcode == "M104": # Set hotend temp (no wait)
                    self.sendUSBmessage(cmd)
                    match = regexes_parameters["floatS"].search(cmd)
                    if match:
                        try:
                            self._currentHotendTemp = float(match.group("value"))
                            self._logger.info(f"HotendTemp: {self._currentHotendTemp}")
                        except ValueError:
                            self._logger.info("HotendTemp M104 exception")
                            pass
                    self._gcodeCounter = 0
                elif gcode == "M109": # Set hotend temp (wait)
                    self.sendUSBmessage(cmd)
                    match = regexes_parameters["floatS"].search(cmd)
                    if match:
                        try:
                            self._currentHotendTemp = float(match.group("value"))
                            self._logger.info(f"HotendTemp: {self._currentHotendTemp}")
                        except ValueError:
                            self._logger.info("HotendTemp M109 exception")
                            pass
                    self._gcodeCounter = 0
                # TODO (?): Capture bed temperature settings (M140, M190)
                elif gcode == "M114": # Request position info
                    self.sendUSBmessage(cmd)
                elif gcode == "M117": # Send message to LCD
                    self.sendUSBmessage(cmd)
                    # TODO (?): Capture layer info
                    #2023-10-13 13:37:21,100 - serialUSBlogger - INFO - Send: M117 DASHBOARD_LAYER_INDICATOR 1
                    #2023-10-13 13:37:21,108 - serialUSBlogger - INFO - Send: M117 0% L=0/166
                elif gcode != "G0" and gcode != "G1":
                    self.sendUSBmessage(cmd)
                elif self._gcodeCounter < 200:
                    self.sendUSBmessage(cmd)
                if gcode == "G0" or gcode == "G1":
                    #self.process_inbound_commands(comm_instance, cmd, gcode)
                    msg = self.readUSBmessage()
                    if msg != "":
                        self._logger.info(f"Inbound: {msg}")
                        fsCmdLine = msg.split()
                        if len(fsCmdLine) > 1:
                            if fsCmdLine[0] == "FS:" and fsCmdLine[1] == "FRO":  # Filament runout event detected by FS
                                self._gcodeCounter = 0
                                self._savedGCode.append(cmd)
                                self._gobackX = self._currentX
                                self._gobackY = self._currentY
                                self._gobackZ = self._currentZ
                                self._gobackE = self._currentE
                                self._gobackF = self._currentF
                                self.sendUSBmessage(f"FSPStat (FRO Event) Detected By Plugin - DING DING DING***********")  # *** Debug - acknowledge FRO event
                                self.sendUSBmessage(f"FSPStat Position {self._xyzAxisStatus}: X{self._gobackX} Y{self._gobackY} Z{self._gobackZ} E{self._gobackE} {self._eAxisStatus} F{self._gobackF}")
                                # TODO: Add MQTT event
                                newcmd = []
                                newcmd.append("M117 Filament Change",)  # TODO: Can we add layer info here?
                                #if self._xyzAxisStatus == XYZAxisStatus.ABSOLUTE:
                                #    newZ = self._gobackZ + self._settings.get(["zDistance"])
                                #else
                                #    newZ = self._settings.get(["zDistance"])
                                newZ = self._gobackZ + self._settings.get(["zDistance"])
                                newcmd.append("G90")    # Absolute XYZE
                                newcmd.append("M83")    # Relative E
                                newcmd.append("M92 E0") # Set E position to 0
                                newcmd.append("G1 Z+" + str(newZ) + " E-0.8 F4500")  # Raise hotend above work piece, pull back filament a bit
                                #if self._eAxisStatus == EAxisStatus.ABSOLUTE:
                                #    newE = self._gobackE + self._settings.get(["unload_length"])
                                #else
                                #    newE = self._settings.get(["unload_length"])
                                newE = self._settings.get(["unload_length"]) # TODO: If length > 100 then break it up
                                newcmd.append("G1 E-" + str(newE) + " F4500") # Retract past extruder drive
                                newcmd.append("G4")  # Dwell
                                cmd = newcmd
                                self._fsState = RunStatus.RELOAD_PARKX0Y0
                    elif "X" in cmd or "Y" in cmd or "Z" in cmd or "E" in cmd or "F" in cmd:
                        # track X
                        match = regexes_parameters["floatX"].search(cmd)
                        if match:
                            try:
                                self._currentX = float(match.group("value"))
                                self._logger.info(f"X: {self._currentX}")
                            except ValueError:
                                self._logger.info("X exception (ValueError)")
                                pass
                        # track Y
                        match = regexes_parameters["floatY"].search(cmd)
                        if match:
                            try:
                                self._currentY = float(match.group("value"))
                                self._logger.info(f"Y: {self._currentY}")
                            except ValueError:
                                self._logger.info("Y exception (ValueError)")
                                pass
                        # track Z
                        match = regexes_parameters["floatZ"].search(cmd)
                        if match:
                            try:
                                self._currentZ = float(match.group("value"))
                                self._logger.info(f"Z: {self._currentZ}")
                            except ValueError:
                                self._logger.info("Z exception (ValueError)")
                                pass
                        # track E
                        match = regexes_parameters["floatE"].search(cmd)
                        if match:
                            try:
                                self._currentE = float(match.group("value"))
                                self._logger.info(f"E: {self._currentE}")
                            except ValueError:
                                self._logger.info("E exception (ValueError)")
                                pass
                        # track F
                        match = regexes_parameters["floatF"].search(cmd)
                        if match:
                            try:
                                self._currentF = float(match.group("value"))
                                self._logger.info(f"F: {self._currentF}")
                            except ValueError:
                                self._logger.info("F exception (ValueError)")
                                pass
        elif self._fsState == RunStatus.RELOAD_PARKX0Y0: # Send reload request, go to X0 Y0 while it is in progress
            self._savedGCode.append(cmd)
            self._logger.info(f"Phase: {self._fsState}")
            self.sendUSBmessage("FSReload")
            newcmd = []
            newcmd.append("G90")  # Absolute XYZE
            newcmd.append("G1 X0 Y0")
            newcmd.append("G4")   # Dwell: Flush queue
            cmd = newcmd
            self._fsState = RunStatus.RELOAD_PURGE_RETURN
        elif self._fsState == RunStatus.RELOAD_PURGE_RETURN: # Sit at X0 Y0, wait for FS to reload, purge, return to work
            self._savedGCode.append(cmd)
            self._logger.info(f"Phase: {self._fsState}")
            while True:  # TODO: Add timeout, ask operator for help
                msg = self.readUSBmessage()
                if msg != "":
                    self._logger.info(f"Inbound: {msg}")
                    fsCmdLine = msg.split()
                    if len(fsCmdLine) > 1:
                        if fsCmdLine[0] == "FS:" and fsCmdLine[1] == "RESPOOLED":  # The moment we've been waiting for...
                            break
            newcmd = []
            newE = self._settings.get(["unload_length"]) # TODO: If length > 100 then break it up
            newcmd.append("G1 E+0.8 F4500") # Start feed into extruder
            newcmd.append("G4 S1") # Wait a second - orient filament into bowden/hot end # *** Debug
            newcmd.append("G1 E+" + str(newE) + " F4500") # Refeed through Bowden tube etc. from extruder to hot end
            newcmd.append("G4 S1") # Wait a second - heat filament before purge(?) # *** Debug
            newcmd.append("G1 E5 F4500") # Purge
            newcmd.append("G4 S5") # Wait a second - let purged junk roll out
            # TODO: Implement nozzle wipe feature
            newcmd.append("G1 X" + str(self._gobackX) + " Y" + str(self._gobackY))  # Return to work piece XY location (at elevated Z)
            newcmd.append("G1 Z" + str(self._gobackZ))  # Drop down to work piece Z location
            if self._eAxisStatus == EAxisStatus.ABSOLUTE:
                newcmd.append("M82")  # E Absolute
            else
                newcmd.append("M83")  # E Relative
            newcmd.append("G92 E" + str(self._gobackE))  # Set original E value
            if self._gobackF:
                newcmd.append("G1 F" + str(self._gobackF)) # Set original F value
            newcmd.append("G92 E" + str(self._gobackE) + " F" + str(self._gobackF))  # Set original E+F values
            #newcmd.append("G4")  # (not needed?)
            cmd = newcmd
            self._fsState = RunStatus.RESUME
        elif self._fsState == RunStatus.RESUME:
            self._savedGCode.append(cmd)
            self._logger.info(f"Phase: {self._fsState}")
            cmd = self._savedGCode
            self._savedGCode = []  # (Redundant)
            self._fsState = RunStatus.MONITOR_G0G1

        #elif self._fsState == RunStatus.PHASE4:
        #    self._savedGCode.append(cmd)
        #    self._logger.info(f"Phase: {self._fsState}")
        #    self._fsState = RunStatus.PHASE5
        #elif self._fsState == RunStatus.PHASE5:
        #    self._savedGCode.append(cmd)
        #    self._logger.info(f"Phase: {self._fsState}")
        #    # work work work...
        #    self._fsState = RunStatus.PHASE6
        #elif self._fsState == RunStatus.PHASE6:
        #    self._savedGCode.append(cmd)
        #    self._logger.info(f"Phase: {self._fsState}")
        #    # work work work...
        #    self._fsState = RunStatus.PHASE7
        #elif self._fsState == RunStatus.PHASE7:
        #    self._savedGCode.append(cmd)
        #    self._logger.info(f"Phase: {self._fsState}")
        #    # work work work...
        #    self._fsState = RunStatus.PAUSEPRINTER
        #elif self._fsState == RunStatus.PAUSEPRINTER:
        #    self._savedGCode.append(cmd)
        #    self._logger.info(f"Phase: {self._fsState}")
        #    cmd = ["M104 S0", "M140 S0", ("M117 Shutting off hotend, bed heaters")]
        #    self._fsState = RunStatus.PRINTERPAUSED
        #elif self._fsState == RunStatus.PRINTERPAUSED:
        #    self._logger.info("Pausing printer")
        #    self._logger.info(f"Phase: {self._fsState}")
        #    comm_instance.setPause(True)
        #elif self._fsState == RunStatus.PRINTERRESUME:
        #    self._logger.info("Resume operations")
        #    self._logger.info(f"Phase: {self._fsState}")
        #    # TODO: (?) Turn on bed heater, hotend heater to saved values
        #    #comm_instance.setPause(False)  (?)
        #    # TODO: Change state to MONITOR_G0G1(?)
        return cmd

    # Process requests coming from the FS device
    def process_inbound_commands(self, comm_instance, cmd, gcode):
        msg = self.readUSBmessage()
        if msg != "":
            self._logger.info(f"Inbound: {msg}")
            fsCmdLine = msg.split()
            if len(fsCmdLine) > 1:
                if fsCmdLine[0] == "FS:":
                    #self._logger.info(f"FS command is {fsCmdLine[1:]}")
                    if fsCmdLine[1] == "FRO":
                        self._gcodeCounter = 0
                        self.sendUSBmessage(f"FSPStat (FRO Event) Detected By Plugin - DING DING DING***********")
                        self._savedGCode.append(cmd)
                        #comm_instance.setPause(True)
                        #e = comm_instance.pause_position.e
                        #t = comm_instance.pause_position.t
                        #x = comm_instance.pause_position.x
                        #y = comm_instance.pause_position.y
                        #z = comm_instance.pause_position.z
                        #self.sendUSBmessage(f"FSPStat (FRO Event) gcode:{gcode} X{x} Y{y} Z{z} T{t} E{e}")
                        #newcmd = [("M117 Filament Change",),"G91","M83", "G1 Z+80 E-0.8 F4500", "M82", "G90", "G1 X0 Y0"]
                        #newcmd.extend(cmd)
                        #cmd = newcmd
                        #comm_instance.setPause(False)
                        # TODO:
                        # set FS status
                        # set printer to 'pause'
                        # etc. per info below
            if cmd and cmd == "resume":
                if(comm_instance.pause_position.x):
                    oldcmd = cmd
                    e = comm_instance.pause_position.e
                    #f = comm_instance.pause_position.f
                    x = comm_instance.pause_position.x
                    y = comm_instance.pause_position.y
                    z = comm_instance.pause_position.z
                    newcmd =["M83","G1 E-0.8 F4500", "G1 E0.8 F4500", "G1 E0.8 F4500", "M82", "G90", "G92 E"+str(e), "M83", "G1 X"+str(x)+" Y"+str(y)+" Z"+str(z)+" F4500"]
                    if(comm_instance.pause_position.f):
                        newcmd.append("G1 F" + str(comm_instance.pause_position.f))
                    newcmd.extend(cmd)
                    cmd = newcmd
                    comm_instance.commands(cmd)
                comm_instance.setPause(False)

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

    def monitor_atcommand_queue(self, comm_instance, phase, cmd, parameters, tags=None, *args, **kwargs):
        if not hasattr(self, 'cmdCounter'):
            self.cmdCounter = 0
        self.cmdCounter += 1
        if self.cmdCounter < 200:
            self.sendUSBmessage(f"atcmd: {cmd}")


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
        self.sendUSBmessage(f"FSPStat {self._printerstatus}")

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
        "octoprint.comm.protocol.atcommand.queuing":    __plugin_implementation__.monitor_atcommand_queue,
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

