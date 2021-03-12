import os
# configure root logger
import logging
import logging.config
logging.config.fileConfig(os.path.join(
    os.path.dirname(__file__), 'mango_logging.ini'))
