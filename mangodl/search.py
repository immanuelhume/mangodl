"""search.py helps handle searching operations."""

import requests
from requests.exceptions import RequestException
from urllib3.exceptions import MaxRetryError
from bs4 import BeautifulSoup as bs
import lxml
import pickle
import sys
from typing import (Optional,
                    Union,
                    Dict,
                    List,
                    Tuple,
                    Iterator,
                    Awaitable,
                    Set)
from pathlib import Path

from .config import mangodl_config
from .helpers import (horizontal_rule,
                      prompt_for_int,
                      mount_retries)

import logging
logger = logging.getLogger(__name__)

# get stuff from config file
SEARCH_URL: str = mangodl_config.get_search_url()


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
        session = mount_retries(session, 'https://mangadex.org')
        with open(cookie_file, 'rb') as f:
            session.cookies.update(pickle.load(f))
        try:
            r = session.get(SEARCH_URL + manga_title, timeout=15)
        except (MaxRetryError, RequestException):
            logger.error('looks like mangadex is down right now ಥ_ಥ')
            sys.exit()

    soup = bs(r.text, 'lxml')
    manga_entries = soup.find_all('div', class_='manga-entry')

    if manga_entries:
        logger.info(f'got {len(manga_entries)} result(s) for \'{manga_title}\'')
        horizontal_rule()
        for i, manga_entry in enumerate(manga_entries):
            manga_title = manga_entry.find(
                'a', class_='manga_title').string
            print(f'{i}: {manga_title}')
        print(f'↑ {len(manga_entries)} result(s) on mangadex ↑')

        index = prompt_for_int(len(manga_entries) - 1,
                               'Enter the index of the manga you want to download: ')
        link = manga_entries[index].find('a', class_='manga_title').attrs['href']
        id = link.split('/')[2]
        return id
    else:
        logger.critical(f'could not find {manga_title} on mangadex (╯°□°）╯︵ ┻━┻')
        from .mangodl import next_manga
        next_manga()
