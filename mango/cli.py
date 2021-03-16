"""
This is the first line of code to run (after logging configuration).
Manages command line args and other required variables.

Interfaces with config.mango.ini.
"""

import argparse
import os
from .config import mango_config

import logging
logger = logging.getLogger(__name__)

# welcome line
print('(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ Welcome to mango! (◠‿◠✿)')

argparser = argparse.ArgumentParser()
# manga title
argparser.add_argument('-m', '--manga', action='store', type=str,
                       help='Name of the manga to download.')
# root directory for downloads
argparser.add_argument('-f', '--folder', action='store', type=str,
                       default=mango_config.get_root_dir(),
                       help='Absolute path to download folder.')
# username
argparser.add_argument('-u', '--username', action='store', type=str,
                       help='Mangadex username.')
# password
argparser.add_argument('-p', '--password', action='store', type=str,
                       help='Mangadex password.')
# archive to volumes or not
argparser.add_argument('--novolume', action='store_true',
                       help='Don\'t automatically compile into volumes.')
# default chapters per volume
argparser.add_argument('--vollen', action='store', type=int, default=10,
                       help='Number of chapters per volume to default to, if mangadex did not assign. This value defaults to 10.')
# language
argparser.add_argument('-l', '--language', action='store', type=str,
                       choices=['gb', 'ru', 'it', 'th',
                                'sa', 'id', 'br', 'tr',
                                'il', 'es', 'hu', 'ph'],
                       default='gb', help='Select manga language. Defaults to english.')
# use low quality images
argparser.add_argument('-s', '--saver', action='store_true',
                       help='Use low quality images.')
# rate limit
argparser.add_argument('--ratelimit', action='store', type=int,
                       help='Limit number of requests per second.')

ARGS = argparser.parse_args()


def check_title():
    if not ARGS.manga:
        m = input('Search for a manga: ')
        ARGS.manga = m


def check_folder():
    if not ARGS.folder and not mango_config.get_root_dir():
        logger.warning('download directory not set')
        f = input('Please specify directory to store manga in: ')
        if not os.path.isdir(f):
            print(f'{f} does not exist. Create directory?')
            print('[y] - yes    [n] - no')
            resp = input()
            if resp.lower() == 'y':
                os.mkdir(f)
                logger.info(f'created -> {f}')
            elif resp.lower() == 'n':
                logger.info(f'input \'{resp}\' - enter another path')
                return check_folder()
            else:
                logger.error(f'input \'{resp}\' is invalid')
                return check_folder()
        ARGS.folder = f
        mango_config.set_root_dir(f)
    elif not ARGS.folder:
        ARGS.folder = mango_config.get_root_dir()
    else:
        mango_config.set_root_dir(ARGS.folder)


def check_username():
    if not ARGS.username and not mango_config.get_username():
        u = input('Mangadex username: ')
        mango_config.set_username(u)
    elif not ARGS.username:
        ARGS.username = mango_config.get_username()
    else:
        mango_config.set_username(ARGS.username)


def check_password():
    if not ARGS.password and not mango_config.get_password():
        u = input('Mangadex password: ')
        mango_config.set_password(u)
    elif not ARGS.password:
        ARGS.password = mango_config.get_password()
    else:
        mango_config.set_password(ARGS.password)


# run checks
check_title()
check_folder()
check_username()
check_password()
