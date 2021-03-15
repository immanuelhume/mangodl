# TODO how the fuck do i package and interface?
# TODO handle connection and server erros !!!
# TODO AUTHENTICATION???
# TODO handle the other command line args
# TODO add choice for how many chapters per volume default, volumize or not
# TODO pytest
# TODO add color to logs
# TODO apparently some chapters can have no name - just ''
# TODO pipe to calibre? subprocess?
# TODO separate files from download
# TODO add a timer?
# TODO PASSWORD ENCRYPTION
# TODO image names must be pure numbers
# TODO add tqdm for volumizing

__version__ = "0.1.0"

from .mango_logging import mango_logging
from .cli import ARGS

from .manga import Manga, BadMangaError
from .search import Search
from .login import Login
from .filesys import FileSys
from .helpers import horizontal_rule, _Getch

import sys
import os
import logging
logger = logging.getLogger(__name__)

getch = _Getch()

COOKIE_FILE = Login.login()


def main():
    # search for `ARGS.manga`
    manga_id = Search.get_manga_id(ARGS.manga, COOKIE_FILE)
    manga = Manga(manga_id)
    # nothing has been downloaded before this point
    proc_download(manga)

    next_manga()


def search_another():
    horizontal_rule()
    manga_title = input('Search for a manga: ')
    manga_id = Search.get_manga_id(manga_title, COOKIE_FILE)
    manga = Manga(manga_id)
    proc_download(manga)

    next_manga()


def next_manga(skip_choice=False):
    while True:
        horizontal_rule()
        next_option()
        manga_title = input('Search for a manga: ')
        manga_id = Search.get_manga_id(manga_title, COOKIE_FILE)
        manga = Manga(manga_id)
        proc_download(manga)


def proc_download(manga):
    fs = FileSys(manga.title)
    manga.download_chapters(fs, ARGS.language)
    fs.create_volumes(manga.downloaded)
    manga.print_bad_chapters()
    logger.info(
        f'{manga.title} has finished downloading - see the raw and archived files @ {fs.base_path}')


def next_option():
    print('[a] - download another manga')
    print('[q] - quit application')
    r = getch()
    if r.lower() == 'a':
        logger.info(f'got input {r} - search for next manga')
    elif r.lower() == 'q':
        logger.info(f'got input {r} - quitting application')
        sys.exit()
    else:
        # don't accept the input
        logger.warning(f'input \'{r}\' is invalid')
        return next_option()
