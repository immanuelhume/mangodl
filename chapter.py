import os
import shutil
import requests
import asyncio
import aiohttp
from typing import Optional, Union, Dict, List, Tuple, Iterator

from helpers import api_get, safe_mkdir
from constants import api_base


class Chapter:
    """Chapter objects represent one chapter of the manga.

    Main attributes:
        hash (str)          : Hash of this chapter.
        id (str)            : Id of this chapter.
        chapter_num (str)   : The chapter number.
        volume_num (str)    : Volume number given for this chapter. Might
                              be empty string.

    Instance methods:
        download: Downloads chapter into folder raw_path.
    """

    def __init__(self, id: Union[str, int], api_base=api_base):
        self.url = api_base + f'chapter/{id}'
        self.data = api_get(self.url)
        data = self.data

        self.hash = data['hash']
        self.id = data['id']
        self.chapter_num = data['chapter']
        self.volume_num = data['volume']

    def get_page_links(self) -> List[str]:
        """Checks if chapter has a valid server. If server if found,
        creates `self.page_links` list."""
        try:
            server_base = self.data['server'] + f'{self.hash}/'
            self.page_links = [server_base +
                               page for page in self.data['pages']]
            print(
                f'Data server found for id {self.id} (chapter {self.chapter_num}) ~(˘▾˘~)')
            return True
        except KeyError:
            print(
                f'No data server for id {self.id} (chapter {self.chapter_num}) ლ(ಠ益ಠლ)')
            return False

    def download(self, raw_path: str) -> None:
        """Creates a folder for this chapter inside `raw_path` and saves
        all images into the new folder."""
        chapter_path = os.path.join(raw_path, self.chapter_num)
        safe_mkdir(chapter_path)

        async def download_page(session: aiohttp.ClientSession,
                                url: str,
                                page_path: str) -> None:
            async with session.get(url) as resp:
                with open(page_path, 'wb') as out_file:
                    shutil.copyfileobj(resp.raw, out_file)

        async def download_all_pages(page_links):
            async with aiohttp.ClientSession() as session:
                tasks = []
                for link in page_links:
                    page_path = os.path.join(chapter_path, link.split('/')[-1])
                    task = asyncio.ensure_future(
                        download_page(session, link, page_path))
                    tasks.append(task)
                await asyncio.gather(*tasks, return_exceptions=True)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(download_all_pages(self.page_links))

        '''
        session = requests.Session()
        for link in self.page_links:
            page_path = os.path.join(chapter_path, link.split('/')[-1])
            resp = session.get(link, stream=True)
            with open(page_path, 'wb') as out_file:
                shutil.copyfileobj(resp.raw, out_file)
        '''
        print(f'Chapter {self.chapter_num} downloaded (~˘▾˘)~')
