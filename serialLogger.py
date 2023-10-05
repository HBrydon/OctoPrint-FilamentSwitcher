
# Thanks again to ChatGPT for writing a substantial part of this

import logging

class serialLogger:
    def __init__(self, logfile):
        self.logfile = logfile
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Create a file handler
        handler = logging.FileHandler(self.logfile)

        # Create a formatter and set it for the handler
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Add the handler to the logger
        self.logger.addHandler(handler)
        self.logger.info(">>> Logging initiated to %s", logfile)

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








#class serialLogger:
#    def __init__(self, logfile):
#        self.logger = logging.getLogger(__name__)
#        logging.basicConfig(filename=logfile, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y_%H:%M:%S', level=logging.INFO)
#        logging.debug('*** SerialLogger(%s)', logfile)
#        logging.info('*** SerialLogger(%s)', logfile)
#        logging.warning('*** SerialLogger(%s)', logfile)
#        logging.error('*** SerialLogger(%s)', logfile)
#        logging.critical('*** SerialLogger(%s)', logfile)
#        self.logger.info(">>> Logging initiated to %s", logfile)
#
#    def __del__(self):
#        logging.info("<<< Closing logfile")
#
#    def log_send_message(self, message, level=logging.INFO):
#        logging.info('Send: %s', message)
#
#    def log_recv_message(self, message, level=logging.INFO):
#        logging.info('Recv: %s', message)
#
#    def log_message(self, message, level=logging.INFO):
#        logging.info(message)
#
#def main():
#    logfile = "inout.log"
#    logger = serialLogger(logfile)
#
#    # Log some messages
#    logger.log_message("This is a log message.")
#    logger.log_message("Another log message.")
#    logger = None

#if __name__ == "__main__":
#    file_logger = serialLogger('logfile.log')
#
#    file_logger.log(logging.INFO, 'This is an informational message.')
#    file_logger.log(logging.ERROR, 'An error occurred.')


if __name__ == "__main__":
    main()




