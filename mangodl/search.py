"""search.py contains the Search class for handling searching operations."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import RequestException
from urllib3.exceptions import MaxRetryError
from bs4 import BeautifulSoup as bs
import lxml
import pickle
import sys
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable
from pathlib import Path

from .config import mangodl_config
from .helpers import horizontal_rule, prompt_for_int, retry_session

import logging
logger = logging.getLogger(__name__)

# set up from config
SEARCH_URL: str = mangodl_config.get_search_url()


class Search:
    """
    Search objects are responsible for any searching operations.

    Parameters
    ----------
    None

    Methods
    -------
    get_manga_id(manga_title, cookie_file)
        Search for the manga's id on mangadex.
    """

    def __init__(self):
        pass

    @staticmethod
    def get_manga_id(manga_title: str, cookie_file: Path) -> Optional[str]:
        """
        Searches mangadex for a manga, and tries to find the manga's id. Will 
        display all results and prompt user for a choice.

        Parameters
        ----------
        manga_title : str
            Title of manga to search.
        cookie_file : str
            Absolute path to pickle file containing cookies from last login.

        Returns
        -------
        id : str
            Mangadex id for the manga selected. Will call mangodl.next_manga() if 
            none found.
        """
        with requests.Session() as session:
            session = retry_session(session, 'https://mangadex.org')
            # retry = Retry(total=10,
            #               status_forcelist=[429, 500, 502, 503, 504],
            #               method_whitelist=["HEAD", "GET", "OPTIONS"],
            #               backoff_factor=1)
            # adapter = HTTPAdapter(max_retries=retry)
            # session.mount('https://mangadex.org/', adapter)
            with open(cookie_file, 'rb') as f:
                session.cookies.update(pickle.load(f))
            try:
                resp = session.get(SEARCH_URL + manga_title, timeout=15)
            except (MaxRetryError, RequestException) as e:
                logger.error(e, exc_info=True)
                logger.error('looks like mangadex is down right now')
                sys.exit()
        soup = bs(resp.text, 'lxml')
        manga_entries = soup.find_all('div', class_='manga-entry')
        if manga_entries:
            logger.info(
                f'got {len(manga_entries)} result(s) for \'{manga_title}\'')
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
            from .mangodl import next_manga
            next_manga()
