# TODO how the fuck do i package and interface?
# TODO CHECK FOR MISSING CHAPTERS!!!
# TODO handle connection and server erros !!!


from .chapter import Chapter
from .manga import Manga
from .search import Search
from .fs import Fs
import os
import time
import argparse
from pathlib import Path

__version__ = "0.1.0"

# argparser = argparse.ArgumentParser()
# argparser.add_argument('manga', action='store',
#                     help='Name of the manga to download.', type=str)
# argparser.add_argument('-p', '--path', action='store', type=PathLike, default=?,
#                     help='Absolute path download folder.')
# argparser.add_argument('-l', '--language', action='store',
#                     choices=['gb', 'ru', 'it', 'th',
#                              'sa', 'id', 'br', 'tr',
#                              'il', 'es', 'hu', 'ph'],
#                     default='gb', help='Select manga language.')
# argparser.add_argument('-s', '--saver', action='store_true',
#                     help='Use low quality images.')


def main():
    manga_name = 'kaguya sama'

    search = Search()
    manga_id = search.get_manga_id(manga_name)

    manga = Manga(manga_id)
    fs = Fs(manga.title)

    start_time = time.time()

    chapter_mappings = manga.download_chapters(fs.raw_path)

    duration = time.time() - start_time
    print(f'Took {duration / 60:.2f} minutes.')

    fs.create_volumes(chapter_mappings)


if __name__ == '__main__':
    main()
