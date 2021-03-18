"""Contains the Chapter class."""

import os
import asyncio
import aiohttp
import aiofiles
from aiohttp.client_exceptions import ClientPayloadError, ServerDisconnectedError, ClientConnectorError
from tqdm import tqdm
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable
from pathlib import Path

from .helpers import safe_mkdir, safe_to_int
from .config import mangodl_config
from .cli import ARGS

import logging
logger = logging.getLogger(__name__)

# set up logging prefixes for use in tqdm.write
WARNING_PREFIX = f'{__name__} | [WARNING]: '
ERROR_PREFIX = f'{__name__} | [ERROR]: '
CRITICAL_PREFIX = f'{__name__} | [CRITICAL]: '

API_BASE = mangodl_config.get_api_base()


class Chapter:
    """
    Chapter objects represent one chapter of the manga. 
    Facilitates asynchronous download.

    Parameters
    ----------
    id : str or int
        Chapter id obtained from mangadex.
    saver : bool
        Opt to use low quality images.

    Attributes
    ----------
    id : str or int
    url : str
    hash : str
    ch_num : str or int or float
    vol_num : str or int or float
    ch_title : str
    page_links : list
        Image URLs for each page.
    ch_path : str
        Absolute path to the chapter's folder on disk.
    """

    def __init__(self, id: Union[str, int], saver: bool):
        if saver:
            self.url = API_BASE + f'chapter/{id}?saver=true'
        else:
            self.url = API_BASE + f'chapter/{id}'
        self.id = id

    async def load(self, session) -> Awaitable:
        """Sends GET request to collect chapter info. Compiles page links at the end."""

        tqdm.write(f'sending GET request to {self.url}')

        async with await session.get(self.url) as resp:
            self.data = await resp.json(content_type=None)

        self.data = self.data['data']
        data = self.data  # make local reference
        self.hash = data['hash']
        self.ch_num = safe_to_int(data['chapter'])
        self.vol_num = safe_to_int(data['volume'])
        self.ch_title = data['title']

        if isinstance(self.ch_num, str):
            # chapter number is probably '' on mangadex
            # will not include it in any volume
            self.ch_num = '_'

        tqdm.write(f'info loaded for chapter {self.ch_num} (id {self.id})')

        self._get_page_links()

    def _get_page_links(self) -> None:
        """
        Checks if chapter has a valid server. 
        If server info is found, stores them in `self.page_links`.
        """
        try:
            server_base = self.data['server'] + f'{self.hash}/'
            self.page_links = [server_base +
                               page for page in self.data['pages']]
            tqdm.write(
                f'server OK for chapter {self.ch_num} with {len(self.page_links)} pages')
        except KeyError:
            tqdm.write(
                f'{WARNING_PREFIX}no image servers for chapter id {self.id} (chapter {self.ch_num}) - KeyError')
            self.page_links = False

    async def download(self, session, raw_path: Path) -> Awaitable:
        """
        Creates a folder for this chapter inside `raw_path` and saves
        all images into the new folder.
        """
        folder_name = f'ch {self.ch_num} ({self.ch_title})' if self.ch_title else f'ch {self.ch_num}'
        self.ch_path = os.path.join(raw_path, folder_name)
        safe_mkdir(self.ch_path)

        async def download_one(session,
                               url: str,
                               page_path: Path) -> Awaitable:
            try:
                async with await session.get(url) as resp:
                    data = await resp.read()
                    async with aiofiles.open(page_path, 'wb') as out_file:
                        await out_file.write(data)
                        tqdm.write(f'saved -> {page_path}')
            except (ServerDisconnectedError, ClientPayloadError, ClientConnectorError) as e:
                tqdm.write(f'{ERROR_PREFIX}chapter {self.ch_num} - {repr(e)}')
                # just try again
                asyncio.sleep(1)
                return download_one(session, url, page_path)

        async def download_all(session, urls: str) -> Awaitable:
            tasks = []
            for i, url in enumerate(urls):
                page_path = os.path.join(
                    self.ch_path, f'{i+1}.{url.split(".")[-1]}')
                tasks.append(download_one(session, url, page_path))
            return [await task for task in tqdm(asyncio.as_completed(tasks),
                                                total=len(tasks),
                                                desc=f'Chapter {self.ch_num}',
                                                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}',
                                                ncols=80,
                                                leave=False)]

        await download_all(session, self.page_links)
