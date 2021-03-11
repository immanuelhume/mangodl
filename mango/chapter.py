import os
import asyncio
import aiohttp
import aiofiles
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable
from pathlib import Path
import tqdm

from .helpers import safe_mkdir, RateLimitedSession
from .config import mango_config

# load config
config = mango_config.read_config()
API_BASE = config['links']['api_base']


class Chapter:
    """Chapter objects represent one chapter of the manga.

    Main attributes:
        id (str)            : Id of this chapter.
        url (str)           : API url for this chapter.

        ===These are only available after calling self.load()===
        hash (str)              : Hash of this chapter.
        chapter_num (str)       : The chapter number.
        volume_num (str)        : Volume number given by API for 
                                  this chapter. Might be empty string.
        page_links (list/None)  : List of image urls.

    Instance methods:
        load    : Make async get request to collect chapter info.
        download: Downloads chapter into folder for raw images.
    """

    def __init__(self, id: Union[str, int]):
        self.url = API_BASE + f'chapter/{id}'
        self.id = id

    async def load(self, session: RateLimitedSession) -> Awaitable:
        """Sends get request to collect chapter info. Calls `get_page_links`
        at the end."""
        async with await session.get(self.url) as resp:
            self.data = await resp.json(content_type=None)
        self.data = self.data['data']
        data = self.data

        self.hash = data['hash']
        self.chapter_num = data['chapter']
        self.volume_num = data['volume']

        self.get_page_links()

    def get_page_links(self) -> None:
        """Checks if chapter has a valid server. If server info is found,
        creates `self.page_links` list."""
        try:
            server_base = self.data['server'] + f'{self.hash}/'
            self.page_links = [server_base +
                               page for page in self.data['pages']]
            # print(
            # f'Data server found for id {self.id} (chapter {self.chapter_num}) ~(˘▾˘~)')
        except KeyError:
            # print(
            # f'No data server for id {self.id} (chapter {self.chapter_num}) ლ(ಠ益ಠლ)')
            self.page_links = False

    async def download(self, session, raw_path: Path) -> Awaitable:
        """Creates a folder for this chapter inside `raw_path` and saves
        all images into the new folder."""

        chapter_path = os.path.join(raw_path, self.chapter_num)
        safe_mkdir(chapter_path)

        async def download_one(session: RateLimitedSession,
                               url: str,
                               page_path: Path) -> Awaitable:
            async with await session.get(url) as resp:
                data = await resp.read()
                async with aiofiles.open(page_path, 'wb') as out_file:
                    await out_file.write(data)

        async def download_all(session: RateLimitedSession, urls: str) -> Awaitable:
            tasks = []
            for url in urls:
                page_path = os.path.join(chapter_path, url.split('/')[-1])
                tasks.append(download_one(session, url, page_path))
            # await asyncio.gather(*tasks)
            return [await task for task in tqdm.tqdm(asyncio.as_completed(tasks),
                                                     total=len(tasks),
                                                     desc=f'Chapter {self.chapter_num}',
                                                     bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}')]

        await download_all(session, self.page_links)

        #print(f'Chapter {self.chapter_num} downloaded (~˘▾˘)~')


if __name__ == '__main__':
    pass
