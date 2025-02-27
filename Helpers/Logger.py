"""Logging wrapper for Syslog and STDOUT"""
import USyslog.usyslog as syslogger
from Helpers.DateHelpers import TimeToString
from time import localtime

class MultiLogger:
    # Define the log levels (match to USyslog)
    LEVEL_EMERGENCY = syslogger.S_EMERG
    LEVEL_ALERT = syslogger.S_ALERT
    LEVEL_CRITICAL = syslogger.S_CRIT
    LEVEL_ERROR = syslogger.S_ERR
    LEVEL_WARN = syslogger.S_WARN
    LEVEL_NOTICE = syslogger.S_NOTICE
    LEVEL_INFO = syslogger.S_INFO
    LEVEL_DEBUG = syslogger.S_DEBUG

    def __init__(self, log_level=LEVEL_DEBUG, syslog_server=None, app_name="MicroPython"):
        self._sys_logger = None
        self._log_level = log_level
        self._app_name = app_name
        if syslog_server is not None:
            self._sys_logger = syslogger.UDPClient(ip=syslog_server, port=514, facility=syslogger.F_USER)
            
    def log(self, log_level, message):
        # Range check on log level
        if log_level > MultiLogger.LEVEL_DEBUG or log_level < MultiLogger.LEVEL_EMERGENCY:
            return
        # Check if log level is relevant to the logger
        if log_level > self._log_level:
            # Log entry can be ignored
            return
        log_level_text = ""
        if log_level == MultiLogger.LEVEL_EMERGENCY:
            log_level_text = "EMERGENCY"
        elif log_level == MultiLogger.LEVEL_ALERT:
            log_level_text = "ALERT"
        elif log_level == MultiLogger.LEVEL_CRITICAL:
            log_level_text = "CRITICAL"
        elif log_level == MultiLogger.LEVEL_ERROR:
            log_level_text = "ERROR"
        elif log_level == MultiLogger.LEVEL_WARN:
            log_level_text = "WARN"
        elif log_level == MultiLogger.LEVEL_NOTICE:
            log_level_text = "NOTICE"
        elif log_level == MultiLogger.LEVEL_INFO:
            log_level_text = "INFO"
        elif log_level == MultiLogger.LEVEL_DEBUG:
            log_level_text = "DEBUG"
        
        # If enabled, send the message to syslog
        if self._sys_logger is not None:
            self._sys_logger.log(log_level, f"TAG {self._app_name} {message}")
        # Print the message to the REPL console
        print(f"{TimeToString(localtime())} - {log_level_text}: {message}")
