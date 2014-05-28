#!/usr/bin/env python
import logging
import logging.handlers
from Singleton import Singleton
import os

LOGPATH = '/tmp'
class LoggerManager(Singleton):
        def __init__(self):
                self.loggers = {}
                formatter = logging.Formatter('%(asctime)s:%(levelname)-8s:%(name)-10s:%(lineno)4s: %(message)-80s')
                level = 'DEBUG'
                nlevel = getattr(logging, level, None)
                if nlevel != None:
                        self.LOGGING_MODE = nlevel
                else:
                        self.LOGGING_MODE = logging.DEBUG
                self.LOGGING_HANDLER = logging.handlers.RotatingFileHandler(
                                        os.path.join(LOGPATH, 'log_event.log'),'a',0, 10)
                self.LOGGING_HANDLER.doRollover()
                self.ERROR_HANDLER = logging.handlers.RotatingFileHandler(
                                        os.path.join(LOGPATH,'log_error.log'),'a',0, 10)
                self.ERROR_HANDLER.doRollover()
                self.LOGGING_HANDLER.setFormatter(formatter)
                self.LOGGING_HANDLER.setLevel(self.LOGGING_MODE)
       
        def getLogger(self, loggername):
                if not self.loggers.has_key(loggername):
                        logger = Logger(loggername,
                                        logging_handler= self.LOGGING_HANDLER,
                                        error_handler = self.ERROR_HANDLER,
                                        logging_mode = self.LOGGING_MODE)
                        self.loggers[loggername] = logger
                return self.loggers[loggername]
class Logger:
        '''
        Implements the christine logging facility.
        '''
        def __init__(self, loggername, type = 'event', logging_handler= '', error_handler = '', logging_mode = ''):
                '''
                Constructor, construye una clase de logger.
               
                @param loggername: Nombre que el logger tendra.
                @param type: Tipo de logger. Los valores disponibles son : event y error
                                        por defecto apunta a event. En caso de utilizarse otro
                                        que no sea event o error se apuntara a event.
                '''
                # Creating two logger, one for the info, debug and warnings and
                #other for errors, criticals and exceptions
                self.__Logger = logging.getLogger(loggername)
                self.__ErrorLogger = logging.getLogger('Error'+ loggername)
                # Setting Logger properties
                self.__Logger.addHandler(logging_handler)
                self.__Logger.setLevel(logging_mode)
                self.__ErrorLogger.addHandler(error_handler)
                self.__ErrorLogger.setLevel(logging_mode)
                self.info = self.__Logger.info
                self.debug = self.__Logger.debug
                self.warning = self.__Logger.warning
               
                self.critical = self.__ErrorLogger.critical
                self.error = self.__ErrorLogger.error
                self.exception = self.__ErrorLogger.exception
 