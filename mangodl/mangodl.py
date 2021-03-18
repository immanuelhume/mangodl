"""Main app logic."""

# BUG random network errors unhandled
# TODO more automated tests
# TODO add a timer?
# TODO encrypt login info?
# TODO options for file format?
# TODO automatically search another site
# TODO add multiple url option

from .mangodl_logging import mangodl_logging
from .cli import ARGS

from .manga import Manga
from .search import Search
from .login import Login
from .filesys import FileSys
from .helpers import horizontal_rule, _Getch

import sys
import os
import logging
logger = logging.getLogger(__name__)

getch = _Getch()


def main():
    """This function is the program's entry point."""
    #
    # download via url - no login
    if ARGS.url:
        for url in ARGS.url:
            logger.info(f'downloading manga at {url}')
            manga_id = url.split('/')[-2]
            manga = Manga(manga_id)
            proc_download(manga)
        sys.exit()
    #
    # login
    global COOKIE_FILE
    COOKIE_FILE = Login.login()
    #
    # search for `ARGS.manga`
    manga_id = Search.get_manga_id(ARGS.manga, COOKIE_FILE)
    manga = Manga(manga_id)
    #
    # nothing has been downloaded before this point
    proc_download(manga)
    # download completed
    next_manga()


def search_another():
    """Call this function to stop current process and search another file."""
    horizontal_rule()
    manga_title = input('Search for a manga: ')
    manga_id = Search.get_manga_id(manga_title, COOKIE_FILE)
    manga = Manga(manga_id)
    proc_download(manga)

    next_manga()


def next_manga(skip_choice=False):
    """Used to keep app running after a single download concludes."""
    while True:
        horizontal_rule(new_line=0)
        next_option()
        manga_title = input('Search for a manga: ')
        manga_id = Search.get_manga_id(manga_title, COOKIE_FILE)
        manga = Manga(manga_id)
        proc_download(manga)


def proc_download(manga):
    """Downloads everything."""
    fs = FileSys(manga.title)
    manga.download_chapters(fs,
                            ARGS.language,
                            ARGS.saver,
                            ARGS.ratelimit,
                            ARGS.novolume,
                            ARGS.vollen,
                            ARGS.all)
    if not ARGS.novolume:
        fs.create_volumes(manga.downloaded)
    manga.print_bad_chapters()
    logger.info(
        f'{manga.title} has finished downloading - see the raw and archived files @ {fs.base_path}')


def next_option():
    """
    After download concludes, ask user if they'd like to download
    another manga or quit the app.
    """
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
