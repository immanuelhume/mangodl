import os
import asyncio
import aiohttp
import aiofiles
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable
from pathlib import Path
import tqdm

from .helpers import safe_mkdir, RateLimitedSession
from .config import mango_config

import logging
logger = logging.getLogger(__name__)

INFO_PREFIX = f'{__name__} | [INFO]: '
DEBUG_PREFIX = f'{__name__} | [DEBUG]: '
WARNING_PREFIX = f'{__name__} | [WARNING]: '
ERROR_PREFIX = f'{__name__} | [ERROR]: '
CRITICAL_PREFIX = f'{__name__} | [CRITICAL]: '


# load config
API_BASE = mango_config.get_api_base()


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
        tqdm.tqdm.write(
            f'{DEBUG_PREFIX}created Chapter instance for chapter id {id}')

    async def load(self, session: RateLimitedSession) -> Awaitable:
        """Sends get request to collect chapter info. Calls `get_page_links`
        at the end."""

        tqdm.tqdm.write(f'{DEBUG_PREFIX}sending GET request to {self.url}')

        async with await session.get(self.url) as resp:
            self.data = await resp.json(content_type=None)
        self.data = self.data['data']
        data = self.data

        self.hash = data['hash']
        self.chapter_num = data['chapter']
        self.volume_num = data['volume']

        tqdm.tqdm.write(
            f'{DEBUG_PREFIX}info loaded for chapter {self.chapter_num} (id {self.id})')

        self.get_page_links()

    def get_page_links(self) -> None:
        """Checks if chapter has a valid server. If server info is found,
        creates `self.page_links` list."""
        try:
            server_base = self.data['server'] + f'{self.hash}/'
            self.page_links = [server_base +
                               page for page in self.data['pages']]
            tqdm.tqdm.write(
                f'{DEBUG_PREFIX}found data server for chapter {self.chapter_num} with {len(self.page_links)} pages')
        except KeyError as e:
            tqdm.tqdm.write(e)
            tqdm.tqdm.write(
                f'{WARNING_PREFIX}could not find image servers for chapter id {self.id}')
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
                tqdm.tqdm.write(f'{DEBUG_PREFIX}sending GET request to {url}')
                data = await resp.read()
                async with aiofiles.open(page_path, 'wb') as out_file:
                    await out_file.write(data)
                    tqdm.tqdm.write(f'{INFO_PREFIX}saved -> {page_path}')

        async def download_all(session: RateLimitedSession, urls: str) -> Awaitable:
            tasks = []
            for url in urls:
                page_path = os.path.join(chapter_path, url.split('/')[-1])
                tasks.append(download_one(session, url, page_path))
            return [await task for task in tqdm.tqdm(asyncio.as_completed(tasks),
                                                     total=len(tasks),
                                                     desc=f'Chapter {self.chapter_num}',
                                                     bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}',
                                                     leave=False)]

        await download_all(session, self.page_links)


if __name__ == '__main__':
    pass
