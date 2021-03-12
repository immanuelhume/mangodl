"""This is the first file ran. Manages command line args and 
other required variables.

These CLI arguments are available (all are optional):

-m : name of manga (str)
-f : absolute path to folder for download (str)
-l : manga language (str)
-s : low quality images (bool)
-u : mangadex username (str)
-p : mangadex password (str)
"""

import argparse
import os
from .config import mango_config

print('Welcome to mango!')

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

args = argparser.parse_args()


def check_title(args):
    if not args.manga:
        m = input('Search for a manga: ')
        args.manga = m


def check_folder(args):
    if not args.folder and not mango_config.get_root_dir():
        f = input('Please specify directory to store manga in: ')
        if not os.path.isdir(f):
            print(f'{f} does not exist. Create directory?')
            print('[y] - yes    [n] - no')
            resp = input()
            if resp.lower() == 'y':
                os.mkdir(f)
            elif resp.lower() == 'n':
                args.check_path()
            else:
                print('Invalid input.')
                args.check_path()
        args.folder = f
        mango_config.set_root_dir(f)
    elif not args.folder:
        args.folder = mango_config.get_root_dir()
    else:
        mango_config.set_root_dir(args.folder)


def check_username(args):
    if not args.username and not mango_config.get_username():
        u = input('Mangadex username: ')
        mango_config.set_username(u)
    elif not args.username:
        args.username = mango_config.get_username()
    else:
        mango_config.set_username(args.username)


def check_password(args):
    if not args.password and not mango_config.get_password():
        u = input('Mangadex password: ')
        mango_config.set_password(u)
    elif not args.password:
        args.password = mango_config.get_password()
    else:
        mango_config.set_password(args.password)
