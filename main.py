# TODO progress bar?
# TODO multi threading?
# TODO how the fuck do i package and interface?

from chapter import Chapter
from manga import Manga
from search import Search
from fs import Fs
from constants import login_url, search_url, api_base
import os
import time


if __name__ == '__main__':
    start_time = time.time()

    username = 'immanuelhume'
    password = 'XnQAtrRmsW3ddF'
    manga_name = 'tokyo ghoul'

    search = Search(username, password, login_url, search_url)
    manga_id = search.get_manga_id(manga_name)

    manga = Manga(manga_id, api_base)
    chapter_id_list = manga.get_ids()

    fs = Fs('/mnt/d/tmp', manga)

    print('Preparing to download...')
    for chapter_id in chapter_id_list:
        Chapter(chapter_id, api_base).download(fs.raw_path)

    fs.create_volumes()

    duration = time.time() - start_time

    print(f'Took {duration / 60} minutes.')
