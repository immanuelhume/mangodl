import configparser
import os

CONFIG_FILE = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), 'config', 'mango.ini')
config = configparser.ConfigParser()


def read_config():
    config.read(CONFIG_FILE)
    return config


def get_username() -> str:
    config.read(CONFIG_FILE)
    try:
        return config['user info']['username']
    except KeyError:
        return None


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
        return None


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


if __name__ == '__main__':
    pass
