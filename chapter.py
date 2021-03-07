import os
import shutil
import requests
import asyncio
import aiohttp
import aiofiles
from typing import Optional, Union, Dict, List, Tuple, Iterator

from helpers import api_get, safe_mkdir
from constants import API_BASE


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

    def __init__(self, id: Union[str, int], api_base=API_BASE):
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

        async def get_page(session: aiohttp.ClientSession, url: str):
            resp = await session.get(url)
            raw_resp = await resp.raw
            return raw_resp

        async def save_image(session: aiohttp.ClientSession, url: str, page_path: str):
            raw_resp = await get_page(session, url)
            async with aiofiles.open(page_path, 'wb') as out_file:
                await out_file.write(raw_resp)

        async def download_all(page_links):
            async with aiohttp.ClientSession() as session:
                tasks = []
                for link in page_links:
                    page_path = os.path.join(chapter_path, link.split('/')[-1])
                    tasks.append(save_image(session, link, page_path))
                await asyncio.gather(*tasks)

        asyncio.run(download_all(self.page_links))

        print(f'Chapter {self.chapter_num} downloaded (~˘▾˘)~')
