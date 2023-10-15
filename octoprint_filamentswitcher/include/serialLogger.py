
# Thanks to ChatGPT for writing the early part of this

import logging

# Based on info found at
#  https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
#  https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
# Use of this works good but puts binary info in the text file...
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


class serialLogger:
    def __init__(self, logfile, port="Unknown"):
        self.logfile = logfile
        self.port = port
        self.logger = logging.getLogger("serialUSBlogger")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.logfile)
        #formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        #formatter = logging.Formatter('\033[94m%(asctime)s\033[0m - \033[96m%(levelname)s\033[0m - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info("\033[1m>>> Logging initiated to file %s\033[0m", self.logfile)

    def __del__(self):
        self.logger.info("\033[1m<<< Closing logfile\033[0m")

    def log_send_message(self, message):
        self.logger.info('%sSend%s: %s', bcolors.OKBLUE, bcolors.ENDC, message)

    def log_recv_message(self, message):
        self.logger.info('%sRecv%s: %s', bcolors.OKGREEN, bcolors.ENDC, message)

    def log_message(self, message):
        self.logger.info("\033[1m%s\033[0m", message)

    # Log a message at the specified logging level (logging.DEBUG, logging.INFO, etc.).
    def log(self, level, message):
        if level == logging.DEBUG:
            self.logger.debug("\033[1m%s\033[0m", message)
        elif level == logging.INFO:
            self.logger.info("\033[1m%s\033[0m", message)
        elif level == logging.WARNING:
            self.logger.warning(message)
        elif level == logging.ERROR:
            self.logger.error(message)
        elif level == logging.CRITICAL:
            self.logger.critical(message)
        else:
            raise ValueError('Invalid log level')



def main():
    logfile = "inout.log"
    file_logger = serialLogger(logfile)

    # Log some messages
    file_logger.log_message("This is a log message.")
    file_logger.log_message("Another log message.")
    file_logger.log(logging.INFO, 'This is an informational message.')
    file_logger.log(logging.ERROR, 'An error occurred.')
    logger = None

if __name__ == "__main__":
    main()




