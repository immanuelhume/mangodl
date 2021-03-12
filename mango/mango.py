# TODO how the fuck do i package and interface?
# TODO CHECK FOR MISSING CHAPTERS!!!
# TODO print out list of chapters avail first
# TODO handle connection and server erros !!!
# TODO PRINT OR LOG?
# TODO ARG PARSING + INTEGRATE WITH CONFIG WRITING
# TODO INITIAL LAUNCH - NEEDS TO ASK FOR PASSWORD

__version__ = "0.1.0"

from .cli import safe_args as args

from .chapter import Chapter
from .manga import Manga
from .search import Search
from .fs import Fs
import os
import time
import argparse


def main():

    search = Search()
    manga_id = search.get_manga_id(args.manga)

    manga = Manga(manga_id)
    fs = Fs(manga.title)

    start_time = time.time()

    chapter_mappings = manga.download_chapters(fs.raw_path)

    duration = time.time() - start_time
    print(f'Took {duration / 60:.2f} minutes.')

    fs.create_volumes(chapter_mappings)


if __name__ == '__main__':
    main()
