"""
This is the first line of code to run (after logging configuration).
Manages command line args and other required variables.

Interfaces with config.mangodl.ini.
"""

import argparse
import os
from .config import mangodl_config

import logging
logger = logging.getLogger(__name__)

# welcome line
print('(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ Welcome to Mango Downloads! (◠‿◠✿)')

_desc = """
        Download manga from the command line through the mangadex API. 

        The default behavior is to login to mangadex and search for a 
        manga. Your credentials are stored locally in a config file, so
        you only need to login once.

        If you wish to suppress this, run mangodl --url <url_to_manga> 
        to download directly without login.

        All arguments are optional - the app will prompt you for 
        anything it needs but doesn't have.
        """

argparser = argparse.ArgumentParser(prog='mangodl',
                                    usage='%(prog)s [options]',
                                    description=_desc,
                                    formatter_class=argparse.RawTextHelpFormatter)
#
# manga title
argparser.add_argument('-m', '--manga', metavar='MANGA', action='store', type=str,
                       help='name of the manga to download')
#
# root directory for downloads
argparser.add_argument('-f', '--folder', metavar='DOWNLOAD_DIRECTORY', action='store', type=str,
                       default=mangodl_config.get_root_dir(),
                       help='absolute path to download folder')
#
# username
argparser.add_argument('-u', '--username', metavar='USERNAME', action='store', type=str,
                       help='mangadex username')
#
# password
argparser.add_argument('-p', '--password', metavar='PASSWORD', action='store', type=str,
                       help='mangadex password')
#
# archive to volumes or not
argparser.add_argument('--novolume', action='store_true',
                       help='don\'t automatically compile into volumes')
#
# default chapters per volume
argparser.add_argument('--vollen', metavar='VOLUME_LENGTH', action='store', type=int, default=10,
                       help='number of chapters per volume to default to, if mangadex did not assign (defaults to %(default)s)')
#
# language
argparser.add_argument('-l', '--language', metavar='LANGUAGE', action='store', type=str,
                       default='gb', help='select manga language (defaults to english)')
#
# use low quality images
argparser.add_argument('-s', '--saver', action='store_true',
                       help='use low quality images')
#
# rate limit
argparser.add_argument('--ratelimit', metavar='LIMIT', action='store', type=int, default=30,
                       help='limit number of requests per second (defaults to %(default)s)')
#
# download by url
argparser.add_argument('--url', metavar='URL', action='store', type=str, nargs='+',
                       help='url to the manga on mangadex - using this will download directly without logging into mangadex')
#
# download all chapters, don't prompt
argparser.add_argument('--all', action='store_true',
                       help='don\'t prompt to ask which chapters to download, just download every chapter found')


ARGS = argparser.parse_args()


def check_title():
    if not ARGS.manga:
        m = input('Search for a manga: ')
        ARGS.manga = m


def check_folder():
    if not ARGS.folder:
        print('No download folder has been selected ⚆ _ ⚆')
        print('Would you like to use the current folder as the download directory?')
        print('[y] - okay, use current folder')
        print('[n] - specify my own folder')
        print('[d] - use default Downloads folder')
        c = input().strip()
        if c.lower() == 'y':
            f = os.path.abspath('.')
            logger.info(f'will save manga to {f}')
        elif c.lower() == 'd':
            f = os.path.join(os.path.expanduser('~'), 'Downloads')
            logger.info(f'will save manga to {f}')
        elif c.lower() == 'n':
            f = input('Please enter an absolute path: ')
            logger.info(f'will save manga to {f}')
        else:
            logger.error(f'input \'{c}\' is invalid')
            return check_folder()
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
        mangodl_config.set_root_dir(f)
    else:
        mangodl_config.set_root_dir(ARGS.folder)


def check_username():
    if not ARGS.username and not mangodl_config.get_username():
        u = input('Mangadex username: ')
        mangodl_config.set_username(u)
    elif not ARGS.username:
        ARGS.username = mangodl_config.get_username()
    else:
        mangodl_config.set_username(ARGS.username)


def check_password():
    if not ARGS.password and not mangodl_config.get_password():
        u = input('Mangadex password: ')
        mangodl_config.set_password(u)
    elif not ARGS.password:
        ARGS.password = mangodl_config.get_password()
    else:
        mangodl_config.set_password(ARGS.password)


# run checks
check_folder()
if not ARGS.url:
    check_title()
    check_username()
    check_password()
