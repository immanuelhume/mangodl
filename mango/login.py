import requests
from bs4 import BeautifulSoup as bs
import lxml
import pickle
import sys
import os
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable
from .config import mango_config
from .helpers import horizontal_rule

import logging
logger = logging.getLogger(__name__)

# set up from config
LOGIN_URL: str = mango_config.get_login_url()
USERNAME: str = mango_config.get_username()
PASSWORD: str = mango_config.get_password()


class Login:
    """Tries logging into mangadex and stores cookies as pickle file
     if successful.

    Attributes:
        cookie_file : Absolute path to pickle file with cookies
                      received from login.
    """

    def __init__(self):
        self.cookie_file = self.login()

    @staticmethod
    def login() -> None:
        with requests.Session() as session:
            payload = {'login_username': USERNAME,
                       'login_password': PASSWORD,
                       'remember_me': 1
                       }
            logger.info(f'attempting login to mangadex as {USERNAME}')
            p = session.post(LOGIN_URL, data=payload, timeout=20)
            with open('login-cookies', 'wb') as f:
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
                from .mango import main
                main()
            else:
                logger.info(f'logged in as {USERNAME} ♪~ ᕕ(ᐛ)ᕗ')
                return os.path.abspath('login-cookies')
        else:
            logger.critical(
                f'unable to reach mangadex (╥﹏╥)...got HTTP {p.status_code} status code')
            sys.exit()
