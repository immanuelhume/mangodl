import os
import shutil
import requests
import asyncio
import aiohttp
import aiofiles
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable

from helpers import get_json, safe_mkdir, RateLimitedSession
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
        self.id = id
        # self.data = get_json(self.url)
        # data = self.data

        # self.hash = data['hash']
        # self.id = data['id']
        # self.chapter_num = data['chapter']
        # self.volume_num = data['volume']

    async def load(self, session: RateLimitedSession) -> Awaitable:
        async with await session.get(self.url) as resp:
            self.data = await resp.json()
        data = self.data

        # store variables
        self.hash = data['hash']
        #self.id = data['id']
        self.chapter_num = data['chapter']
        self.volume_num = data['volume']

        self.get_page_links()

    def get_page_links(self) -> None:
        """Checks if chapter has a valid server. If server if found,
        creates `self.page_links` list."""
        try:
            server_base = self.data['server'] + f'{self.hash}/'
            self.page_links = [server_base +
                               page for page in self.data['pages']]
            print(
                f'Data server found for id {self.id} (chapter {self.chapter_num}) ~(˘▾˘~)')
            # return self.page_links
        except KeyError:
            print(
                f'No data server for id {self.id} (chapter {self.chapter_num}) ლ(ಠ益ಠლ)')
            self.page_links = False

    async def download(self, session, raw_path: str) -> Awaitable:
        """Creates a folder for this chapter inside `raw_path` and saves
        all images into the new folder."""

        chapter_path = os.path.join(raw_path, self.chapter_num)
        safe_mkdir(chapter_path)

        async def download_one(session: RateLimitedSession, url: str, page_path: str) -> Awaitable:
            resp = await session.get(url)
            data = await resp.read()
            async with aiofiles.open(page_path, 'wb') as out_file:
                await out_file.write(data)

        async def download_all(session: RateLimitedSession, urls: str) -> Awaitable:
            tasks = []
            for url in urls:
                page_path = os.path.join(chapter_path, url.split('/')[-1])
                tasks.append(download_one(session, url, page_path))
            await asyncio.gather(*tasks)

        await download_all(session, self.page_links)
        '''
        async def get_page(session: RateLimitedSession, url: str):
            async with await session.get(url) as resp:
                if resp.ok:
                    return await resp.read()

        async def save_image(session: RateLimitedSession, url: str, page_path: str):
            raw_resp = await get_page(session, url)
            async with aiofiles.open(page_path, 'wb') as out_file:
                await out_file.write(raw_resp)

        async def download_all_pages(page_links):
            async with aiohttp.ClientSession() as session:
                session = RateLimitedSession(session, 20, 20)
                tasks = []
                for link in page_links:
                    page_path = os.path.join(chapter_path, link.split('/')[-1])
                    tasks.append(save_image(session, link, page_path))
                await asyncio.gather(*tasks)

        await download_all_pages(self.page_links)
        # asyncio.run(download_all_pages(self.page_links))
        '''
        print(f'Chapter {self.chapter_num} downloaded (~˘▾˘)~')


if __name__ == '__main__':
    id = 1223893
    chapter = Chapter(1223893)
    chapter.get_page_links()
    with open('experimental/page-links', 'a') as out_file:
        out_file.write('\n'.join(chapter.page_links))
