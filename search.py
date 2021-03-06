import requests
from bs4 import BeautifulSoup as bs
import lxml
from typing import Optional
import sys
from constants import login_url, search_url


class Search:
    """Search objects are used to log into mangadex and search
    for the id for a manga. Tries to log into mangadex when instantiated. 
    If login fails, program stops.

    Main attributes:
        username: Username to mangadex.
        password: Password for username.
        session : Current logged-in session.

    Instance methods:
        get_manga_id: Returns manga id for manga_title.
    """

    def __init__(self,
                 username: str,
                 password: str,
                 login_url=login_url,
                 search_url=search_url):

        self.login_url = login_url
        self.search_url = search_url
        self.username = username
        self.password = password
        self.__login()

    def __login(self) -> None:
        """Tries logging into mangadex. If the login failed, calls
        sys.exit()"""
        self.session = requests.Session()
        payload = {'login_username': self.username,
                   'login_password': self.password,
                   'remember_me': 1
                   }
        p = self.session.post(self.login_url, data=payload)
        # check if login succeeded
        soup = bs(p.text, 'lxml')
        if soup.title.string != 'Home - MangaDex':
            print('Login failed (╥﹏╥)')
            print('Please check your username and password.')
            sys.exit()
        else:
            print(f'Logged in as {self.username} ♪~ ᕕ(ᐛ)ᕗ')

    def get_manga_id(self, manga_title: str) -> Optional[str]:
        """Searches mangadex for `manga_title`. Calls sys.exit() 
        if not found. If `manga_title` is found, will print out all 
        search results and prompt user for a choice.

        Returns id for manga selected.
        """
        resp = self.session.get(self.search_url + manga_title)
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
