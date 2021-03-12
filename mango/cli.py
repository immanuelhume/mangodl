import argparse
import os
from .helpers import safe_mkdir
from .config import mango_config

print('Welcome to mango!')


class SafeArgs:

    def __init__(self, args: argparse.Namespace):
        for a in args.__dict__:
            setattr(self, a, args.__dict__[a])
        self.check_all()

    def check_title(self):
        if not self.manga:
            m = input('Search for a manga: ')
            self.manga = m

    def check_path(self):
        if not self.folder and not mango_config.get_root_dir():
            f = input('Please specify directory to store manga in: ')
            if not os.path.isdir(f):
                print(f'{f} does not exist. Create directory? - [y/n]')
                resp = input()
                if resp.lower() == 'y':
                    safe_mkdir(f)
                elif resp.lower() == 'n':
                    self.check_path()
                else:
                    print('Invalid input.')
                    self.check_path()
            self.folder = f
            mango_config.set_root_dir(f)
        elif not self.folder:
            self.folder = mango_config.get_root_dir()
        else:
            mango_config.set_root_dir(self.folder)

    def check_username(self):
        if not self.username and not mango_config.get_username():
            u = input('Mangadex username: ')
            mango_config.set_username(u)
        elif not self.username:
            self.username = mango_config.get_username()
        else:
            mango_config.set_username(self.username)

    def check_password(self):
        if not self.password and not mango_config.get_password():
            u = input('Mangadex password: ')
            mango_config.set_password(u)
        elif not self.password:
            self.password = mango_config.get_password()
        else:
            mango_config.set_password(self.password)

    def check_all(self):
        self.check_username()
        self.check_password()
        self.check_title()
        self.check_path()


argparser = argparse.ArgumentParser()
# manga title
argparser.add_argument('-m', '--manga', action='store', type=str,
                       help='Name of the manga to download.')
# root directory for downloads
argparser.add_argument('-f', '--folder', action='store', type=str,
                       default=mango_config.get_root_dir(),
                       help='Absolute path download folder.')
# language
argparser.add_argument('-l', '--language', action='store', type=str,
                       choices=['gb', 'ru', 'it', 'th',
                                'sa', 'id', 'br', 'tr',
                                'il', 'es', 'hu', 'ph'],
                       default='gb', help='Select manga language.')
# use low quality images
argparser.add_argument('-s', '--saver', action='store_true',
                       help='Use low quality images.')
# username
argparser.add_argument('-u', '--username', action='store', type=str,
                       help='Mangadex username.')
# password
argparser.add_argument('-p', '--password', action='store', type=str,
                       help='Mangadex password.')

safe_args = SafeArgs(argparser.parse_args())
