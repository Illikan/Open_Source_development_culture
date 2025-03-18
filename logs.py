import logging
import sys
import time
from logging.handlers import TimedRotatingFileHandler
import socket
from logging import handlers
FORMATTER_STRING = "%(asctime)s — %(name)s — %(levelname)s — %(message)s"
FORMATTER = logging.Formatter(FORMATTER_STRING)
LOG_FILE = "/tmp/my_app.log" 



HOST = 'localhost'
FROM = '"APPLICATION ALERT" <python@you'
TO = 'you@you'
SUBJECT = 'New Critical Event From [APPLICATION]'


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    logger.addHandler(console_handler)

    file_handler = TimedRotatingFileHandler(LOG_FILE, when='midnight')
    logger.addHandler(file_handler)


    handler = handlers.SMTPHandler(HOST, FROM, TO, SUBJECT)
    email_logger = logging.getLogger('smtp.example')
    email_logger.addHandler(handler)
    email_logger.setLevel = logging.CRITICAL

    return logger

if __name__ == "__main__":
    logger = get_logger("my_app_logger")
    logger.info("Start logging")
    logger.debug("Some debug message")
    while True:
        try: 
            time.sleep(1)
            logger.info("Keep logging")
        except KeyboardInterrupt:
            logger.fatal("User get bored")
            break
    try:
        logger.critical('Critical Event Notification\n\nTraceback:\n %s',
                          ''.join(traceback.format_stack()))
    except socket.error as error:
        logging.critical('Could not send email via SMTPHandler: %r', error)