# TODO progress bar?
# TODO multi threading?
# TODO how the fuck do i package and interface?

from chapter import Chapter
from manga import Manga
from search import Search
from fs import Fs
import os
import time


if __name__ == '__main__':

    username = 'immanuelhume'
    password = 'XnQAtrRmsW3ddF'
    manga_name = 'tokyo ghoul'

    search = Search(username, password)
    manga_id = search.get_manga_id(manga_name)

    manga = Manga(manga_id)
    fs = Fs('/mnt/d/tmp', manga.title)

    start_time = time.time()

    chapter_mappings = manga.download_chapters(fs.raw_path)

    duration = time.time() - start_time
    print(f'Took {round(duration / 60)} minutes.')

    fs.create_volumes(chapter_mappings)
