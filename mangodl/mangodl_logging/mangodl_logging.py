import os
# configure root logger
import logging
import logging.config
logging.config.fileConfig(os.path.join(
    os.path.dirname(__file__), 'mangodl_logging.ini'))
