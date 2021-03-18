"""helpers.py contains helper functions and classes for use in the mangodl app."""

import os
import sys
import time
import math
import re
from typing import (Optional, Union, Dict, List,
                    Tuple, Iterator, Awaitable)
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import RequestException
from urllib3.exceptions import MaxRetryError
from itertools import zip_longest
import asyncio
from aiohttp import ClientSession

from .config import mangodl_config
API_BASE = mangodl_config.get_api_base()

import logging
logger = logging.getLogger(__name__)


def get_json_data(url: str, time_out: int = 10, max_tries: int = 10) -> Dict:
    """
    Sends a GET request to the API url. Expects a JSON response, and returns
    the 'data' section of JSON string as a dict.

    Parameters
    ----------
    url : str
        API url to request.
    time_out : int, default 30
        How many seconds to wait before throwing Timeout error.
    max_tries : int, default 10
        Maximum number of requests to send before throwing MaxRetryError.

    Returns
    -------
    dict
        Dict representation of 'data' section in the JSON string.
    """
    # retry = Retry(total=max_tries,
    #               status_forcelist=[429, 500, 502, 503, 504],
    #               method_whitelist=["HEAD", "GET", "OPTIONS"],
    #               backoff_factor=1)
    # adapter = HTTPAdapter(max_retries=retry)
    with requests.Session() as s:
        s = retry_session(s, API_BASE, max_tries)
        #s.mount(API_BASE, adapter)
        try:
            resp = s.get(url, timeout=time_out)
            return resp.json()['data']
        except (MaxRetryError, RequestException) as e:
            logger.error(e, exc_info=True)
            sys.exit()


def retry_session(session, domain: str, max_tries: int = 10, backoff: int = 1):
    """Mounts adapter to a session, configuring retries."""
    retry = Retry(total=max_tries,
                  status_forcelist=[429, 500, 502, 503, 504],
                  method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
                  backoff_factor=backoff)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount(domain, adapter)
    return session


def chunk(lst: List, n: int) -> List:
    """
    Performs greedy chunking. Divides a list into chunks of n items. The last
    chunk will have at least n items.
    """
    chunked = []
    q = len(lst) // n
    for i in range(q - 1):
        chunked.append(lst[i * n:i * n + n])
    chunked.append(lst[(q - 1) * n:])
    return chunked


def safe_mkdir(p: Path) -> None:
    """Creates directory and handles FileExistsError."""
    try:
        os.mkdir(p)
    except FileExistsError:
        pass


def safe_to_int(j):
    """
    Tries converting the argument to int. If that fails, tries converting to float.
    And if that fails too, return the argument as is.
    """
    try:
        i = float(j)
    except ValueError:
        return j
    else:
        return int(i) if int(i) == i else i


def horizontal_rule(char: str = '=', length: int = 36, new_line=1) -> None:
    """
    Draws a horizontal line in stdout.

    Parameters
    ----------
    char : str
        Character to use for the rule.
    length : int, default 36
        Number of characters in rule.
    new_line : int, default 1
        How many empty lines to print above the actual rule.

    Returns
    -------
    None
    """
    for _ in range(new_line):
        print()
    print(f'{char*length}')


# recipe from https://gist.github.com/pquentin/5d8f5408cdad73e589d85ba509091741
class RateLimitedSession():
    """
    Wrapper class for `aiohttp.ClientSession` objects. Injects
    a rate limit on the number of calls per second by maintaining a bucket
    of 'tokens'.

    Parameters
    ----------
    session : session instance
        Can be a requests.Session or aiohttp.ClientSession instance.
    rate, max_tokens : int, optional
        `rate` describes the number of tokens produced per second. `max_tokens`
        is the size of the bucket. (Both values default to 20.)

    Attributes
    ----------
    tokens : int
        Number of tokens in the bucket at any time.
    updated_at : float
        Time when the bucket was last updated.
    """

    def __init__(self, session: ClientSession, rate: int = 20, max_tokens: int = 20):
        self.session = session
        self.rate = rate
        self.max_tokens = max_tokens

        logger.debug(f'created rate-limited client at {rate} calls per second')

        self.tokens = self.max_tokens
        self.updated_at = time.monotonic()

    async def get(self, *args, **kwargs):
        await self.consume_token()
        return self.session.get(*args, **kwargs)

    async def consume_token(self):
        while self.tokens < 1:
            self.add_new_tokens()
            await asyncio.sleep(0.1)
        self.tokens -= 1

    def add_new_tokens(self):
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.rate
        if self.tokens + new_tokens >= 1:
            self.tokens = min(self.tokens + new_tokens, self.max_tokens)
            self.updated_at = now


async def gather_with_semaphore(n: int, *tasks) -> Awaitable:
    """Wrapper function for aiohttp.gather, but injects a semaphore."""
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))


def find_int_between(c_lst) -> List[int]:
    """Parses a list of numbers and finds all missing integers."""
    missing = []
    for i, c in enumerate(c_lst):
        try:
            nc = c_lst[i + 1]
            for _ in range(math.ceil(c), math.ceil(nc)):
                if c != _:
                    missing.append(_)
        except IndexError:
            # reached the last number
            pass

    return missing


def parse_range_input(astr: str) -> List[str]:
    """
    Uses regex to parse strings like this:

    >>> parse_range_input('1-20, 25, 31-40')
    ['1-20', '25', '31-40']
    """

    p = re.compile(r'\d+\.*\d*\s*-?\s*\d*\.*\d*')
    m = p.findall(astr)
    m_ = [re.sub(r'\s+', '', _) for _ in m]  # strip all whitespace
    return m_


def prompt_for_int(ceil: int, msg: str) -> int:
    """
    Prompts for user input and only accepts integers within
    a given range.
    """
    r = input(msg)
    try:
        r_ = int(r)
    except ValueError:
        logger.error(f'input was {r} - only digits are accepted')
        return prompt_for_int(ceil, msg)
    else:
        if r_ > ceil or r_ < 0:
            logger.error(f'input {r} is of range - number must be <= {ceil}')
            return prompt_for_int(ceil, msg)
        else:
            return r_


# recipe from https://code.activestate.com/recipes/134892/
class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""

    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty
        import sys

    def __call__(self):
        import sys
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def sep_num_and_str(lst: List) -> Tuple:
    nums = []
    strs = []
    for _ in lst:
        if isinstance(_, (int, float)):
            nums.append(_)
        else:
            strs.append(_)
    return nums, strs


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()
