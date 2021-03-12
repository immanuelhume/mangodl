# TODO how the fuck do i package and interface?
# TODO CHECK FOR MISSING CHAPTERS!!!
# TODO print out list of chapters avail first
# TODO handle connection and server erros !!!
# TODO PRINT OR LOG?
# TODO ARG PARSING + INTEGRATE WITH CONFIG WRITING
# TODO INITIAL LAUNCH - NEEDS TO ASK FOR PASSWORD

__version__ = "0.1.0"

from .mango_logging import mango_logging
from .cli import ARGS

from .chapter import Chapter
from .manga import Manga
from .search import Search
from .fs import Fs

import sys
import logging
logger = logging.getLogger(__name__)


def main():
    # search for manga
    search = Search()
    manga_id = search.get_manga_id(ARGS.manga)
    # if manga is available on mangadex, proceed with download
    manga = Manga(manga_id)

    confirm_download(manga.title)

    fs = Fs(manga.title)
    chapter_mappings = manga.download_chapters(fs.raw_path)
    fs.create_volumes(chapter_mappings)

    logger.info('end of program')


def confirm_download(manga: str):
    print(f'{"=" * 36}')
    print(f'Proceed with download of - {manga}?')
    print('[y] - yes    [n] - no')
    check = input()
    if check.lower() == 'n':
        logger.info(f'received input - {check} - exiting program')
        sys.exit()
    elif check.lower() == 'y':
        print('(~˘▾˘)~ okay, starting download now ~(˘▾˘~)')
    else:
        logger.warning(f'invalid input - {check}')
        confirm_download(manga)
