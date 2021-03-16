"""Used for login to mangadex."""

import requests
from bs4 import BeautifulSoup as bs
import lxml
import pickle
import sys
import os
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable

from .config import mango_config
from .helpers import horizontal_rule, _Getch

import logging
logger = logging.getLogger(__name__)

getch = _Getch()

# set up from config
LOGIN_URL: str = mango_config.get_login_url()
USERNAME: str = mango_config.get_username()
PASSWORD: str = mango_config.get_password()


class Login:
    """
    Tries logging into mangadex, and stores cookies as pickle file
    if successful.

    Parameters
    ----------
    None

    Attributes
    ----------
    cookie_file : str
        Absolute path to pickled file containing cookies received from login.
    """

    def __init__(self):
        self.cookie_file = self.login()

    @staticmethod
    def login() -> None:
        """Logs into mangadex. Username and password are globals obtained from config file."""
        def enter_credentials():
            u = input('Mangadex username: ')
            p = input('Mangadex password: ')
            mango_config.set_username(u)
            mango_config.set_password(p)
            global USERNAME
            USERNAME = u
            global PASSWORD
            PASSWORD = p

        with requests.Session() as session:
            payload = {'login_username': USERNAME,
                       'login_password': PASSWORD,
                       'remember_me': 1
                       }
            logger.info(f'attempting login to mangadex as {USERNAME}')
            p = session.post(LOGIN_URL, data=payload, timeout=20)
            with open('login_cookies', 'wb') as f:
                pickle.dump(session.cookies, f)
        if p.ok:
            # check if login succeeded
            soup = bs(p.text, 'lxml')
            if soup.title.string != 'Home - MangaDex':
                # this means login failed

                # reset username and password in config
                mango_config.set_username('')
                mango_config.set_password('')

                horizontal_rule()
                logger.critical(f'login as {USERNAME} failed (╥﹏╥)')
                logger.info('please check your username and password')
                logger.info(
                    'you can reset your username and password with the -u and -p flags, or just log in again')
                print('[l] - login again    [q] - quit application')
                c = getch()
                if c.lower() == 'l':
                    enter_credentials()
                    return Login.login()
                elif c.lower() == 'q':
                    sys.exit()
                else:
                    sys.exit()
            else:
                logger.info(f'logged in as {USERNAME} ♪~ ᕕ(ᐛ)ᕗ')
                return os.path.abspath('login_cookies')
        else:
            logger.critical(
                f'unable to reach mangadex (╥﹏╥)...got HTTP {p.status_code} status code')
            sys.exit()
