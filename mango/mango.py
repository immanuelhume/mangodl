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

__version__ = "0.1.0"

from .mango_logging import mango_logging
from .cli import ARGS

from .manga import Manga, BadMangaError
from .search import Search
from .fs import Fs
from .helpers import horizontal_rule

import sys
import os
import logging
logger = logging.getLogger(__name__)


def main():
    # search for `ARGS.manga`
    manga_id = Search().get_manga_id(ARGS.manga)
    manga = Manga(manga_id)
    # nothing has been downloaded before this point
    proc_download(manga)
    print(os.getcwd())
    while True:
        try:
            print(os.getcwd())
            # forever prompt
            chk_nxt_act()
            # if sys.exit() wasn't called, proceed
            proc_download(search_another())
        except BadMangaError:
            continue


def chk_nxt_act():
    print('[q] - exit program')
    print('[a] - download another manga')
    r = input().strip()
    if r.lower() == 'q':
        logger.info(f'got input {r} - quitting application')
        sys.exit()
    elif r.lower() == 'a':
        logger.info(f'got input {r} - search for next manga')
        pass
    else:
        # don't accept the input
        logger.warning(f'input \'{r}\' is invalid')
        return chk_nxt_act()


def search_another():
    horizontal_rule()
    mt = input('Search for another manga: ')
    mg = Manga(Search(login_cookies=True).get_manga_id(mt))
    return mg


def proc_download(mg):
    fs = Fs(mg.title)
    chapter_mappings = mg.download_chapters(fs.raw_path)
    fs.create_volumes(chapter_mappings)
    mg.print_bad_chapters()
    logger.info(
        f'{mg.title} has finished downloading - see the raw and archived files @ {fs.base_path}')


class StartInterface():

    def __init__(self):
        self.next_action()

    def next_action(self):
        print('[q] - exit program')
        print('[a] - download another manga')
        r = input().strip()
        if r.lower() == 'q':
            logger.info(f'got input {r} - quitting application')
            sys.exit()
        elif r.lower() == 'a':
            logger.info(f'got input {r} - search for next manga')
            self.search_another()
        else:
            # don't accept the input
            logger.warning(f'input \'{r}\' is invalid')
            return self.next_action()

    def search_another(self):
        horizontal_rule()
        mt = input('Search for another manga: ')
        self.manga = Manga(Search(login_cookies=True).get_manga_id(mt))

        self.proc_download()

    def proc_download(self):
        fs = Fs(self.manga.title)
        chapter_mappings = self.manga.download_chapters(fs.raw_path)
        fs.create_volumes(chapter_mappings)
        self.manga.print_bad_chapters()
        logger.info(
            f'{self.manga.title} has finished downloading - see the raw and archived files @ {fs.base_path}')

        return self.next_action()


def main_lite():
    horizontal_rule()
    m = input('Search for a new manga: ')
    manga = Manga(Search(login_cookies=True).get_manga_id(m))
    # nothing has been downloaded before this point
    download_and_exit(manga)


def download_and_exit(mg: Manga):
    fs = Fs(mg.title)
    chapter_mappings = mg.download_chapters(fs.raw_path)
    fs.create_volumes(chapter_mappings)
    mg.print_bad_chapters()
    logger.info(
        f'{mg.title} has finished downloading - see the raw and archived files @ {fs.base_path}')
    sys.exit()


def choose_nxt():
    horizontal_rule()
    print('[q] - exit program')
    print('[a] - download another manga')
    r = input().strip()
    if r.lower() == 'q':
        logger.info(f'got input {r} - quitting application')
        sys.exit()
    elif r.lower() == 'a':
        logger.info(f'got input {r} - search for next manga')
        main_lite()
    else:
        # don't accept the input
        logger.warning(f'input \'{r}\' is invalid')
        choose_nxt()
