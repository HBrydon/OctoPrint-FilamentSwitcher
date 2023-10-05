# Thanks to ChatGPT for writing a lot of this!

import threading
import time
import serial
import queue
import serialLogger

class SerialUSBio:
    def __init__(self, port='/dev/ttyUSB0', logfile='inout.log'):
        #print('*** SerialUSBio(<', port, '>, <', logfile, '>)')
        self.ser = serial.Serial(port, 115200)
        self.data_queue = queue.Queue()
        self.consumer_thread = threading.Thread(target=self.buffered_read_thread)
        time.sleep(1)  # Allow serial device to settle
        self._serialLogger = serialLogger.serialLogger(logfile)

    def __del__(self):
        self._serialLogger.log_message(logging.INFO, "Closing Serial USB port")
        self.stop()
        self.ser = None
        self._serialLogger = None

    def start(self):
        self.consumer_thread.start()

    # (producer) Write record to the device, append newline "\n"
    def write_line(self, data):
        self.ser.write(data.encode())
        self.ser.write(b"\n")
        self._serialLogger.log_send_message(data)
        #print(f"Sending: {data}")

    # (consumer) Read info from the device
    def buffered_read_thread(self):
        while True:
            if self.ser.in_waiting > 0:
                data = self.ser.readline().decode().strip()
                self.data_queue.put(data)
                self._serialLogger.log_recv_message(data)
            time.sleep(0.5)

    def queue_count(self):
        return self.data_queue.qsize()

    def read_line_from_queue(self):
        return self.data_queue.get()

    def stop(self):
        if self.ser.isOpen():
            self.ser.close()


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
