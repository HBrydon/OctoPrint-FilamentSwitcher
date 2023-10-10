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
        self.commstate = serStatus.CLOSED
        self.data_queue = queue.Queue()
        self.consumer_thread = None
        #self.consumer_thread = threading.Thread(target=self.buffered_read_thread)
        self._serialLogger = serialLogger(self.logfile, self.port)

    def __del__(self):
        self.stop()
        self.ser = None
        self._serialLogger = None

    def open(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            self.commstate = serStatus.OPEN
            self.consumer_thread = threading.Thread(target=self.buffered_read_thread)
            self._serialLogger.log_message(f"Port opened for read/write: {self.port}")
            time.sleep(1)  # Allow serial device to settle
        except serial.serialutil.SerialException as e:
            self._serialLogger.log(logging.WARNING, f"Failed to open port {self.port}: {e}")
            self.ser = None
            #raise

    def close(self):
        if self.isOpen():
            self._serialLogger.log_message("Closing IO port")
            self.ser.close()
            self.ser = None
            self.commstate = serStatus.CLOSED

    def isOpen(self):
        return self.ser and self.ser.isOpen()

    def flushInput(self):
        if self.isOpen():
            self.ser.flushInput()

    def flushOutput(self):
        if self.isOpen():
            self.ser.flushOutput()

    def start(self):
        self.consumer_thread.start()

    # (producer) Write record to the device, append newline "\n"
    def write_line(self, data):
        if self.ser and self.ser.isOpen():
            self.ser.write(data.encode())
            self.ser.write(b"\n")
            self._serialLogger.log_send_message(data)
        else:
            self._serialLogger.log(logger.WARNING, "(Failed serial write, port closed)" % data)

    # (producer) Write record to the device
    def write(self, data):
        if self.ser and self.ser.isOpen():
            self.ser.write(data.encode())
            self._serialLogger.log_send_message(data)
        else:
            self._serialLogger.log(logger.WARNING, "(Failed serial write, port closed)" % data)

    # (consumer) Read info from the device
    def buffered_read_thread(self):
        #self.ser.flush()  # TODO: Do we need this?
        while True:
            if self.ser == None:
                self._serialLogger.log_message("Terminating read loop")
                return
            if self.ser.in_waiting > 0:
                data = self.ser.readline().decode().strip()
                self.data_queue.put(data)
                self._serialLogger.log_recv_message(data)
            time.sleep(0.5)

    def queue_count(self):
        return self.data_queue.qsize()

    def read_line_from_queue(self):
        try:
            return self.data_queue.get_nowait()
        except queue.Empty:
            return ""

    def stop(self):
        self.close()

    def getStatus(self):
        return self.commstate

# Test code
def main():
    serialMgr = SerialUSBio("/dev/ttyUSB0", "inout.log")
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

