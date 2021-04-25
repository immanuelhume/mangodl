"""Main app logic."""

# BUG there are still random network errors unhandled
# TODO more automated tests
# TODO add a timer?
# TODO options for file format?
# TODO automatically search another site
# TODO add more emojis!!! - and refactor them to another file

import logging
import os
import sys

from .cli import ARGS
from .filesys import FileSys
from .helpers import _Getch, horizontal_rule, say_goodbye
from .login import login
from .manga import Manga
from .mangodl_logging import mangodl_logging
from .search import get_manga_id

logger = logging.getLogger(__name__)

getch = _Getch()


def main():
    """This function is the program's entry point."""

    # download via url - no login
    if ARGS.url:
        for url in ARGS.url:
            logger.info(f'downloading manga at {url}')
            manga_id = url.split('/')[-2]
            manga = Manga(manga_id)
            proc_download(manga)
        sys.exit()

    # login and save cookies to file
    global COOKIE_FILE
    COOKIE_FILE = login()

    # search for manga
    manga_id = get_manga_id(ARGS.manga, COOKIE_FILE)
    manga = Manga(manga_id)
    # nothing has been downloaded before this point

    # now commence download
    proc_download(manga)
    # download completed

    # let user decide whether to quit or download another one
    next_manga()


def proc_download(manga: Manga) -> None:
    """Downloads everything."""
    fs = FileSys(manga.title)
    manga.download_chapters(fs,
                            ARGS.language,
                            ARGS.saver,
                            ARGS.ratelimit,
                            ARGS.novolume,
                            ARGS.vollen,
                            ARGS.all)

    # archive to volumes
    if not ARGS.novolume:
        fs.create_volumes(manga.downloaded)

    manga.print_bad_chapters()
    logger.info(
        f'{manga.title} has finished downloading - see the raw and archived files @ {fs.base_path}')


def next_manga() -> None:
    """
    Implements a loop so app can download a second manga if
    user decides to.
    """
    while True:
        horizontal_rule(new_line=0)

        next_option()

        manga_title = input('Search for a manga: ')
        manga_id = get_manga_id(manga_title, COOKIE_FILE)
        manga = Manga(manga_id)
        proc_download(manga)


def search_another() -> None:
    """
    Calling this function will abort the current process 
    and search another manga.
    """
    horizontal_rule()
    manga_title = input('Search for a manga: ')
    manga_id = get_manga_id(manga_title, COOKIE_FILE)
    manga = Manga(manga_id)
    proc_download(manga)

    next_manga()


def next_option():
    """
    After download concludes, ask user if they'd like to download
    another manga or quit the app.
    """
    print('[a] - download another manga')
    print('[q] - quit application')

    r = getch()

    if r.lower() == 'a':
        logger.info(f'got input \'{r}\' - search for next manga')
    elif r.lower() == 'q':
        logger.info(f'got input \'{r}\' - quitting application')
        say_goodbye()
    else:
        logger.warning(f'input \'{r}\' is invalid')
        return next_option()
