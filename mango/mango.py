# TODO how the fuck do i package and interface?
# TODO handle connection and server erros !!!
# TODO AUTHENTICATION???
# TODO handle the other command line args
# TODO add choice for how many chapters per volume default, volumize or not
# TODO CHAPTER NUMBER CAN BE '' APPARENTLY!!!
# TODO pytest

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

    logger.warning(
        f'end of program - see the raw and archived files @ {fs.base_path}')
