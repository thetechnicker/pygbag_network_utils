import logging
import platform
import sys


class BrowserConsoleHandler(logging.Handler):
    def emit(self, record):
        if sys.platform == "emscripten":
            log_entry = self.format(record)
            if record.levelno >= logging.ERROR:
                platform.console.error(log_entry)
            elif record.levelno >= logging.WARNING:
                platform.console.warn(log_entry)
            elif record.levelno >= logging.DEBUG:
                platform.console.debug(log_entry)
            else:
                platform.console.log(log_entry)
