"""
Initializes config file if it doesn't already exist, and 
defines functions to interface with the config file.
"""

import configparser
import os
import logging
logger = logging.getLogger(__name__)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'mango_config.ini')
config = configparser.ConfigParser()
# check if config file exists
if not os.path.exists(CONFIG_FILE):
    config['links'] = {}
    config['links']['api_base'] = 'https://api.mangadex.org/v2/'
    config['links']['search_url'] = 'https://mangadex.org/search?tag_mode_exc=any&tag_mode_inc=all&title='
    config['links']['login_url'] = 'https://mangadex.org/ajax/actions.ajax.php?function=login&nojs=1'
    config['user info'] = {}
    config['settings'] = {}
    with open(CONFIG_FILE, 'w') as f:
        config.write(f)


def get_username() -> str:
    config.read(CONFIG_FILE)
    try:
        return config['user info']['username']
    except KeyError:
        pass


def set_username(new_username: str):
    config.read(CONFIG_FILE)
    config['user info']['username'] = new_username
    with open(CONFIG_FILE, 'w') as f:
        config.write(f)


def get_password() -> str:
    config.read(CONFIG_FILE)
    try:
        return config['user info']['password']
    except KeyError:
        pass


def set_password(new_password: str):
    config.read(CONFIG_FILE)
    config['user info']['password'] = new_password
    with open(CONFIG_FILE, 'w') as f:
        config.write(f)


def get_api_base() -> str:
    config.read(CONFIG_FILE)
    try:
        return config['links']['api_base']
    except KeyError:
        return None


def get_search_url() -> str:
    config.read(CONFIG_FILE)
    try:
        return config['links']['search_url']
    except KeyError:
        return None


def get_login_url() -> str:
    config.read(CONFIG_FILE)
    try:
        return config['links']['login_url']
    except KeyError:
        return None


def get_root_dir() -> str:
    config.read(CONFIG_FILE)
    try:
        return config['settings']['root_dir']
    except KeyError:
        return None


def set_root_dir(p: str):
    config.read(CONFIG_FILE)
    config['settings']['root_dir'] = p
    with open(CONFIG_FILE, 'w') as f:
        config.write(f)
