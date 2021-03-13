from .chapter import Chapter
from .manga import Manga
from .search import Search
from .fs import Fs
from .helpers import horizontal_rule

import logging
logger = logging.getLogger(__name__)


def main():
    logger.info('initiating new search')
    horizontal_rule()

    search = Search(login_cookies=True)
    m = input('Search for a new manga: ')
    manga_id = search.get_manga_id(m)
    # if manga is available on mangadex, proceed with download
    manga = Manga(manga_id)
    fs = Fs(manga.title)
    chapter_mappings = manga.download_chapters(fs.raw_path)
    fs.create_volumes(chapter_mappings)

    manga.print_bad_chapters()

    logger.info(
        f'end of program - see the raw and archived files @ {fs.base_path}')
