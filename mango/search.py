import requests
from bs4 import BeautifulSoup as bs
import lxml
import sys
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable
import mango_config

# set up config variables
config = mango_config.read_config()
LOGIN_URL: str = config['links']['login_url']
SEARCH_URL: str = config['links']['search_url']
USERNAME: str = config['user info']['username']
PASSWORD: str = config['user info']['password']


class Search:
    """Search objects are used to login to mangadex and search
    for the id for a manga. Tries to log into mangadex when instantiated. 
    If login fails, program stops.

    Main attributes:
        session : Current logged-in session.

    Instance methods:
        get_manga_id: Returns manga id for manga_title.
    """

    def __init__(self):

        self.__login()

    def __login(self) -> None:
        """Tries logging into mangadex. If the login failed, calls
        sys.exit()"""
        self.session = requests.Session()
        payload = {'login_username': USERNAME,
                   'login_password': PASSWORD,
                   'remember_me': 1
                   }
        p = self.session.post(LOGIN_URL, data=payload, timeout=20)
        if p.ok:
            # check if login succeeded
            soup = bs(p.text, 'lxml')
            if soup.title.string != 'Home - MangaDex':
                print('Login failed (╥﹏╥)')
                print('Please check your username and password.')
                sys.exit()
            else:
                print(f'Logged in as {USERNAME} ♪~ ᕕ(ᐛ)ᕗ')
        else:
            print(
                f'Unable to reach mangadex (╥﹏╥)...got {p.status_code} error.')
            sys.exit()

    def get_manga_id(self, manga_title: str) -> Optional[str]:
        """Searches mangadex for `manga_title`. Calls sys.exit() 
        if not found. If `manga_title` is found, will print out all 
        search results and prompt user for a choice.

        Returns id for manga selected.
        """
        resp = self.session.get(SEARCH_URL + manga_title, timeout=20)
        if not resp.ok:
            print(f'Got error code {resp.status_code} (╯°□°）╯︵ ┻━┻')
            sys.exit()
        soup = bs(resp.text, 'lxml')
        manga_entries = soup.find_all('div', class_='manga-entry')
        if manga_entries:
            for manga_entry in manga_entries:
                manga_title = manga_entry.find(
                    'a', class_='manga_title').string
                print(f'{manga_entries.index(manga_entry)}: {manga_title}')
            print('These are the results obtained.')
            index = int(
                input('Enter the index of the manga you want to download: '))
            link = manga_entries[index].find(
                'a', class_='manga_title').attrs['href']
            id = link.split('/')[2]
            return id
        else:
            print(f'Could not find {manga_title} (╯°□°）╯︵ ┻━┻')
            sys.exit()
