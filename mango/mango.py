# TODO how the fuck do i package and interface?
# TODO CHECK FOR MISSING CHAPTERS!!!
# TODO print out list of chapters avail first
# TODO select range for chapter download
# TODO handle connection and server erros !!!
# TODO INITIAL LAUNCH - NEEDS TO ASK FOR PASSWORD

__version__ = "0.1.0"

from .mango_logging import mango_logging
from .cli import ARGS

from .chapter import Chapter
from .manga import Manga
from .search import Search
from .fs import Fs
from .helpers import horizontal_rule

import sys
import logging
logger = logging.getLogger(__name__)


def main():
    # search for manga
    search = Search()
    manga_id = search.get_manga_id(ARGS.manga)
    # if manga is available on mangadex, proceed with download
    manga = Manga(manga_id)

    fs = Fs(manga.title)
    chapter_mappings = manga.download_chapters(fs.raw_path)
    fs.create_volumes(chapter_mappings)

    manga.print_bad_chapters()

    logger.warning('end of program')
