
import logging
from oslo.config import cfg

log_opts = [
    cfg.StrOpt('log_level',
               default='DEBUG',
               help='The log level of nvs monitor'),
    cfg.StrOpt('log_dir',
               default='./',
               help='Where the log file is stored on the disk'),
    cfg.StrOpt('log_file',
               default='monitor.log',
               help='The file name of nvs monitor log'),
    cfg.StrOpt('log_format',
               default='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
               help='The log output format'),
    cfg.StrOpt('log_date_format',
               default=None,
               help='The data-time output format of log'),
    ]

CONF = cfg.CONF
CONF.register_opts(log_opts)


LEVEL_MAP = {
	'DEBUG': logging.DEBUG,
	'INFO': logging.INFO,
	'WARN': logging.WARN,
	'ERROR': logging.ERROR,
}


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create file handler which logs even debug messages
fh = logging.FileHandler(CONF.log_dir + CONF.log_file)

if CONF.log_level not in LEVEL_MAP:
    CONF.log_level = 'DEBUG'
fh.setLevel(LEVEL_MAP[CONF.log_level])

# create formatter and add it to the handlers
formatter = logging.Formatter(fmt=CONF.log_format,
                            datefmt=CONF.log_date_format)
fh.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)

def getLogger(name):
    return logger.getChild(name)

