import requests
from bs4 import BeautifulSoup as bs
import lxml
import pickle
import sys
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable
from pathlib import Path
from .config import mango_config
from .helpers import horizontal_rule, prompt_for_int

import logging
logger = logging.getLogger(__name__)

# set up from config
SEARCH_URL: str = mango_config.get_search_url()


class Search:
    """Search objects are used to login to mangadex and search
    for the id for a manga.

    Attributes:
        cookie_file: Absolute path to pickle file with login cookies.

    Instance methods:
        get_manga_id: Returns manga id for manga_title.
    """

    def __init__(self, cookie_file: Path):
        self.cookie_file = cookie_file

    @staticmethod
    def get_manga_id(self, manga_title: str) -> Optional[str]:
        """Searches mangadex for `manga_title`. Calls sys.exit() 
        if not found. If `manga_title` is found, will print out all 
        search results and prompt user for a choice.

        Returns id for manga selected.
        """
        with requests.Session() as session:
            with open(self.cookie_file, 'rb') as f:
                session.cookies.update(pickle.load(f))
            resp = session.get(SEARCH_URL + manga_title, timeout=20)
        if not resp.ok:
            logger.critical(
                f'got HTTP status code {resp.status_code} (╯°□°）╯︵ ┻━┻')
            sys.exit()
        soup = bs(resp.text, 'lxml')
        manga_entries = soup.find_all('div', class_='manga-entry')
        if manga_entries:
            logger.info(
                f'got {len(manga_entries)} result(s) for search-string {manga_title} ')
            horizontal_rule()
            for i, manga_entry in enumerate(manga_entries):
                manga_title = manga_entry.find(
                    'a', class_='manga_title').string
                print(f'{i}: {manga_title}')

            if len(manga_entries) == 1:
                print(f'↑ {len(manga_entries)} result on mangadex ↑')
            else:
                print(f'↑ {len(manga_entries)} results on mangadex ↑')

            index = prompt_for_int(
                len(manga_entries) - 1, 'Enter the index of the manga you want to download: ')
            link = manga_entries[index].find(
                'a', class_='manga_title').attrs['href']
            id = link.split('/')[2]
            return id
        else:
            logger.critical(
                f'could not find {manga_title} on mangadex (╯°□°）╯︵ ┻━┻')
            sys.exit()
