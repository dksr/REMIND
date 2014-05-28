import os
import sys
import logging
import logging.handlers
from Singleton import Singleton

class attrdict(dict):
    """ Dictionary with attribute like access """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self        
  
class Logging_Manager(Singleton):
    def __init__(self):
        self.options = {'fquiet':              None, 
                        'loglevel':           'debug', 
                        'quiet':               None, 
                        'module':              "", 
                        'logdir':              '.', 
                        'clean':               False, 
                        'rotating_log':        True,
                        'rotating_file_mode': "a",
                        'maxBytes':            0,
                        'backupCount':         10,
                        'logfile':            'project.log'}
                
    def getLogger(self, options_dict):
        self.options.update(options_dict)
        self.options = attrdict(self.options)
        return Logger(self.options).getLogger()    
    
class Logger():
    def __init__(self,options):
        self.options = options
        
    def getLogger(self):
        """ Log information based upon users options.
        """
        options = self.options
        logger = logging.getLogger(options.module)
        formatter = logging.Formatter('%(asctime)s %(levelname)s\t%(message)s')
        debug_formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s \t%(message)s')
        level = logging.__dict__.get(options.loglevel.upper(),logging.DEBUG)
        logger.setLevel(level)
    
        # Output logging information to screen
        if not options.quiet:
            console_hdlr = logging.StreamHandler(sys.stdout)
            console_hdlr.setFormatter(debug_formatter)
            console_hdlr.setLevel(logging.DEBUG)
            logger.addHandler(console_hdlr)
        # Output logging information to file
        if not options.fquiet:
            log_file = os.path.join(options.logdir, options.logfile)
            if options.clean and os.path.isfile(log_file):
                os.remove(log_file)
            if options.rotating_log:
                rfm = options.rotating_file_mode
                mb  = options.maxBytes
                bc  = options.backupCount
                file_hdlr = logging.handlers.RotatingFileHandler(log_file, rfm, mb, bc)    
                file_hdlr.doRollover()
            else:    
                file_hdlr = logging.FileHandler(log_file)    
            file_hdlr.setFormatter(formatter)
            file_hdlr.setLevel(logging.DEBUG)
            logger.addHandler(file_hdlr)
            
        return logger
    
def initialize_logging(options_dict):
    options = {'fquiet':              None, 
               'loglevel':           'debug', 
               'quiet':               None, 
               'module':              "", 
               'logdir':              '.', 
               'clean':               False, 
               'rotating_log':        True,
               'rotating_file_mode': "a",
               'maxBytes':            0,
               'backupCount':         10,
               'logfile':            'main_log.log'}
    
    options.update(options_dict)
    options = attrdict(options)
    logger = logging.getLogger(options.module)
    formatter = logging.Formatter('%(asctime)s %(levelname)s \t %(name)s (%(lineno)d): %(message)s')
    debug_formatter = logging.Formatter('%(levelname)s \t %(name)s (%(lineno)d): %(message)s')
    level = logging.__dict__.get(options.loglevel.upper(),logging.DEBUG)
    logger.setLevel(level)
    logger.handlers = []

    # Output logging information to screen
    if not options.quiet:
        console_hdlr = logging.StreamHandler(sys.stderr)
        console_hdlr.setFormatter(formatter)
        console_hdlr.setLevel(logging.DEBUG)
        logger.addHandler(console_hdlr)
    # Output logging information to file
    if not options.fquiet:
        if not os.path.isdir(options.logdir):
            # if logdir not present, create the path
            os.system('mkdir -p ' + options.logdir)
        log_file = os.path.join(options.logdir, options.logfile)
        if options.clean and os.path.isfile(log_file):
            os.remove(log_file)
        if options.rotating_log:       
            rfm = options.rotating_file_mode
            mb  = options.maxBytes
            bc  = options.backupCount
            file_hdlr = logging.handlers.RotatingFileHandler(log_file, rfm, mb, bc)    
            file_hdlr.doRollover()
        else:    
            file_hdlr = logging.FileHandler(log_file)    
        file_hdlr.setFormatter(formatter)
        file_hdlr.setLevel(logging.DEBUG)
        logger.addHandler(file_hdlr)
        
    return logger
    
    
def test1():
    import Logging
    import logging 
    import time
    class Hel():
        def __init__(self):
            #self.log = Logging_Manager().getLogger({'module':'Hel'})
            options = {'fquiet':              None, 
                        'loglevel':           'info', 
                        'quiet':               None, 
                        'module':              "", 
                        'logdir':              '/tmp/', 
                        'clean':               False, 
                        'rotating_log':        True,
                        'rotating_file_mode': "a",
                        'maxBytes':            0,
                        'backupCount':         10,
                        'logfile':            'project.log'}
            options = attrdict(options)
            self.log = Logging.initialize_logging(options)
            self.log.info("START TIME: " + time.asctime())
            self.log.error('Creating new instance of  Hel')
        def hel(self):
            self.log.debug('iam in hel')

    class Hello():
        def __init__(self):            
            self.log = logging.getLogger('Hel')
            self.log.info('Creating new instance of Hello')
        def hello(self):
            self.log.debug('iam in hello')
            
    class Bello():        
        def __init__(self):
            self.log = logging.getLogger('Hel.Hello.Hello')
            self.log.info('Creating new instance of BELLO')
        def bel(self):
            self.log.debug('iam in BEl')
            
    g = Hel()
    g.hel()    
    h = Hello()
    h.hello()
    b = Bello()
    b.bel()
               
def test2(argv=None):
    import Logging
    from optparse import OptionParser
    
    if argv is None:
        argv = sys.argv[1:]
    # Setup command line options
    parser = OptionParser("usage: %prog [options]")
    parser.add_option("-l", "--logdir", dest="logdir", default=".", help="log DIRECTORY (default ./)")
    parser.add_option("-m", "--module", dest="module", default="project", help="module/project name from where logging")    
    parser.add_option("-f", "--logfile", dest="logfile", default="project.log", help="log file (default project.log)")    
    parser.add_option("-v", "--loglevel", dest="loglevel", default="debug", help="logging level (debug, info, error)")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", help="do not log to console")    
    parser.add_option("-n", "--filequiet", action="store_true", dest="fquiet", help="do not log to file")
    parser.add_option("-c", "--clean", dest="clean", action="store_true", default=False, help="remove old log file")
    
    # Process command line options
    (options, args) = parser.parse_args(argv)

    # Setup logger format and output locations
    log = Logging.initialize_logging(options)

    # Examples
    log.error("This is an error message.")
    log.info("This is an info message.")
    log.debug("This is a debug message.")

if __name__ == "__main__":
    test1()
    #test2(['-m', 'test', '-l', '/tmp/', '-c', '-n', '-f', 'log_test.log'])

    
