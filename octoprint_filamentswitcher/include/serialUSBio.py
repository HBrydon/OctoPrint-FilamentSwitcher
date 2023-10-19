# Thanks to ChatGPT for writing a lot of this!

from enum import Enum
import logging
import serial
import threading
import time
import queue

from octoprint_filamentswitcher.include.serialLogger import serialLogger


#@unique
class serStatus(Enum):
    UNKNOWN =-0
    CLOSED = 1
    OPEN = 2



class SerialUSBio:
    #def __init__(self, port='/dev/ttyUSB0', baudrate = 115200, logfile='inout.log'): # Error: number of parameters
    def __init__(self, port='/dev/ttyUSB0', logfile='inout.log'):
        self.port = port
        self.baudrate = 115200
        self.logfile = logfile
        self.timeout = 0.1
        #self.ser = serial.Serial(port, 115200)
        self.ser = None
        self.commstate = serStatus.CLOSED
        self.data_queue = queue.Queue()
        self.consumer_thread = None
        #self.consumer_thread = threading.Thread(target=self.buffered_read_thread)
        self._serialLogger = serialLogger(self.logfile, self.port)

    def __del__(self):
        self.stop()
        self.ser = None
        self._serialLogger = None

    def openSerial(self):
        if self.isSerialOpen():
            self._serialLogger.log(logging.WARNING, "Attempt to open logging after already open!")
        else:
            try:
                self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
                self.commstate = serStatus.OPEN
                self.consumer_thread = threading.Thread(target=self.buffered_read_thread)
                self.startReadLoop()
                self._serialLogger.log_message(f"Port opened for read/write: {self.port}")
                time.sleep(1)  # Allow serial device to settle
            except serial.serialutil.SerialException as e:
                self._serialLogger.log(logging.WARNING, f"Failed to open port {self.port}: {e}")
                self.ser = None

    def closeSerial(self):
        if self.ser != None:
            if self.isSerialOpen():
                self._serialLogger.log_message("Closing IO port")
                self.ser.close()
            self.ser = None
        self.commstate = serStatus.CLOSED

    def isSerialOpen(self):
        if self.ser == None:
            return False
        return self.ser.isOpen()

    def flushInput(self):
        if self.isSerialOpen():
            self.ser.flushInput()

    def flushOutput(self):
        if self.isSerialOpen():
            self.ser.flushOutput()

    def startReadLoop(self):
        self.consumer_thread.start()

    # (producer) Write record to the device, append newline "\n"
    def write_line(self, data):
        if self.isSerialOpen():
            self.ser.write(data.encode())
            self.ser.write(b"\n")
            self._serialLogger.log_send_message(data)
        else:
            self._serialLogger.log(logging.WARNING, "(Failed serial write, port closed): " + data)

    # (producer) Write record to the device
    def write(self, data):
        if self.isSerialOpen():
            self.ser.write(data.encode())
            self._serialLogger.log_send_message(data)
        else:
            self._serialLogger.log(logging.WARNING, "(Failed serial write, port closed): " + data)

    # (consumer) Read info from the device
    def buffered_read_thread(self):
        while True:
            if self.ser == None:
                self._serialLogger.log_message("Terminating read loop")
                return
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode().strip()
                    self.data_queue.put(data)
                    self._serialLogger.log_recv_message(data)
                    time.sleep(0.5)
            except serial.serialutil.SerialException as e:
                self._serialLogger.log(logging.WARNING, f"IO exception on port {self.port} (unplugged?): {e}")
                #self.ser = None
                self.closeSerial()


    def queue_count(self):
        return self.data_queue.qsize()

    def read_line_from_queue(self):
        if self.queue_count() > 0:
            try:
                return self.data_queue.get_nowait()
            except queue.Empty:
                pass
        return ""

    def stop(self):
        self.closeSerial()

    def getStatus(self):
        return self.commstate


