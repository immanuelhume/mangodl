from pathlib import Path
# configure root logger
import logging
import logging.config
config_file = Path(__file__).parent / 'mangodl_logging.ini'
logging.config.fileConfig(config_file)
