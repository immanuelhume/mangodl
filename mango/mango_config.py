import configparser

CONFIG_FILE = 'mango.ini'
config = configparser.ConfigParser()


def read_config():
    config.read(CONFIG_FILE)
    return config


def update_username(new_username: str):
    config['user info']['username'] = new_username
    with open(CONFIG_FILE, 'w') as f:
        config.write(f)


def update_password(new_password: str):
    config['user info']['password'] = new_password
    with open(CONFIG_FILE, 'w') as f:
        config.write(f)


if __name__ == '__main__':
    pass
