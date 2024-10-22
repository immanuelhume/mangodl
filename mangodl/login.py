"""Used for login to mangadex."""

import requests
from requests.exceptions import RequestException
from urllib3.exceptions import MaxRetryError
from bs4 import BeautifulSoup as bs
import lxml
import pickle
import sys
import os
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
from .helpers import horizontal_rule, _Getch, mount_retries

import logging
logger = logging.getLogger(__name__)

getch = _Getch()

# set up from config
LOGIN_URL: str = mangodl_config.get_login_url()
USERNAME: str = mangodl_config.get_username()
PASSWORD: str = mangodl_config.get_password()


def login() -> Path:
    """
    Logs into mangadex. Username and password are globals obtained from config file.
    If login succeeds, returns path to pickled cookie file.
    """
    #cookie_file = os.path.join(os.path.dirname(__file__), 'login_cookies')
    cookie_file = Path(__file__).parent / 'login_cookies'

    def enter_credentials():
        u = input('Mangadex username: ')
        p = input('Mangadex password: ')
        mangodl_config.set_username(u)
        mangodl_config.set_password(p)
        global USERNAME
        USERNAME = u
        global PASSWORD
        PASSWORD = p

    with requests.Session() as session:
        session = mount_retries(session, 'https://mangadex.org')
        payload = {'login_username': USERNAME,
                   'login_password': PASSWORD,
                   'remember_me': 0}

        logger.info(f'attempting login to mangadex as {USERNAME}')
        try:
            p = session.post(LOGIN_URL, data=payload, timeout=20)
            with open(cookie_file, 'wb') as f:
                pickle.dump(session.cookies, f)
        except (MaxRetryError, RequestException):
            logger.error('looks like mangadex is down right now (╥﹏╥)')
            sys.exit()

    # check if login succeeded
    soup = bs(p.text, 'lxml')
    if soup.title.string != 'Home - MangaDex':
        # this means login failed
        # delete username and password in config
        mangodl_config.set_username('')
        mangodl_config.set_password('')

        horizontal_rule()
        logger.critical(f'login as {USERNAME} failed (╥﹏╥)')
        logger.info('either mangadex is down, or your credentials are wrong')
        logger.info('you can reset your username and password with the -u and -p flags, or just log in again')
        print('[l] - login again    [q] - quit application')
        c = getch()

        if c.lower() == 'l':
            enter_credentials()
            return login()
        elif c.lower() == 'q':
            sys.exit()
        else:
            sys.exit()
    else:
        logger.info(f'logged in as {USERNAME} ♪~ ᕕ(ᐛ)ᕗ')
        return cookie_file
