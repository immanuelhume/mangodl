import requests
from bs4 import BeautifulSoup as bs
import lxml
import pickle
import sys
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable
from .config import mango_config
from .helpers import horizontal_rule

import logging
logger = logging.getLogger(__name__)

# set up config variables
SEARCH_URL: str = mango_config.get_search_url()
LOGIN_URL: str = mango_config.get_login_url()
USERNAME: str = mango_config.get_username()
PASSWORD: str = mango_config.get_password()


class Search:
    """Search objects are used to login to mangadex and search
    for the id for a manga. Tries to log into mangadex when instantiated. 
    If login fails, program stops.

    Main attributes:
        session : Current logged-in session.

    Instance methods:
        get_manga_id: Returns manga id for manga_title.
    """

    def __init__(self, login_cookies=None):
        if not login_cookies:
            self.__login()

    def __login(self) -> None:
        """Tries logging into mangadex. If the login failed, calls
        sys.exit()"""
        with requests.Session() as session:
            payload = {'login_username': USERNAME,
                       'login_password': PASSWORD,
                       'remember_me': 1
                       }
            logger.info(f'attempting login to mangadex as {USERNAME}')
            p = session.post(LOGIN_URL, data=payload, timeout=20)
            with open('./login-cookies', 'wb') as f:
                pickle.dump(session.cookies, f)
        if p.ok:
            # check if login succeeded
            soup = bs(p.text, 'lxml')
            if soup.title.string != 'Home - MangaDex':  # not the best checking
                mango_config.set_username('')
                mango_config.set_password('')

                horizontal_rule()
                logger.critical(f'login as {USERNAME} failed (╥﹏╥)')
                logger.info('please check your username and password')
                logger.info(
                    'you can reset your username and password with the -u and -p flags, or just log in again')
                from .mango import main
                return main()
            else:
                logger.info(f'logged in as {USERNAME} ♪~ ᕕ(ᐛ)ᕗ')
        else:
            logger.critical(
                f'unable to reach mangadex (╥﹏╥)...got HTTP {p.status_code} status code')
            sys.exit()

    @staticmethod
    def get_manga_id(manga_title: str) -> Optional[str]:
        """Searches mangadex for `manga_title`. Calls sys.exit() 
        if not found. If `manga_title` is found, will print out all 
        search results and prompt user for a choice.

        Returns id for manga selected.
        """
        with requests.Session() as session:
            with open('./login-cookies', 'rb') as f:
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
                f'got {len(manga_entries)} results for search-string {manga_title} ')
            horizontal_rule()
            for manga_entry in manga_entries:
                manga_title = manga_entry.find(
                    'a', class_='manga_title').string
                print(
                    f'{manga_entries.index(manga_entry)}: {manga_title}')

            if len(manga_entries) == 1:
                print(f'↑ {len(manga_entries)} result on mangadex ↑')
            else:
                print(f'↑ {len(manga_entries)} results on mangadex ↑')

            index = int(
                input('Enter the index of the manga you want to download: '))
            link = manga_entries[index].find(
                'a', class_='manga_title').attrs['href']
            id = link.split('/')[2]
            return id
        else:
            logger.critical(
                f'could not find {manga_title} on mangadex (╯°□°）╯︵ ┻━┻')
            from .mango_lite import main_lite
            return main_lite()
