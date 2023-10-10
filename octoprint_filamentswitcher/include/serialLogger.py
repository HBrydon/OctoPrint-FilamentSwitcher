
# Thanks to ChatGPT for writing the early part of this

import logging

class serialLogger:
    def __init__(self, logfile, port="Unknown"):
        self.logfile = logfile
        self.port = port
        self.logger = logging.getLogger("serialUSBlogger")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.logfile)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info(">>> Logging initiated to file %s", self.logfile)

    def __del__(self):
        self.logger.info("<<< Closing logfile")

    def log_send_message(self, message):
        self.logger.info('Send: %s', message)

    def log_recv_message(self, message):
        self.logger.info('Recv: %s', message)

    def log_message(self, message):
        self.logger.info(message)

    # Log a message at the specified logging level (logging.DEBUG, logging.INFO, etc.).
    def log(self, level, message):
        if level == logging.DEBUG:
            self.logger.debug(message)
        elif level == logging.INFO:
            self.logger.info(message)
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




