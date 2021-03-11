import os
import sys
import requests
from requests.exceptions import RequestException
from itertools import zip_longest
import time
import asyncio
from aiohttp import ClientSession
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable
from pathlib import Path


def get_json(url: str, time_out: int = 30, max_tries: int = 10, session=False) -> Dict:
    """Sends get request to page. Expects a json response.

    Arguments:
        url (str)       : Url to get.
        time_out (int)  : How long to wait for response before giving up.
        max_tries (int) : How many times to try getting page if bad response.
        session         : A session instance. Can be requests.Session 
                          or aiohttp.ClientSession.

    Returns:
        A dictionary of the data portion of JSON response.
    """
    tries = 1
    while True:
        try:
            if session:  # use session if passed
                resp = session.get(url, timeout=time_out)
            else:
                resp = requests.get(url, timeout=time_out)

            if resp.ok:
                return resp.json()['data']
            elif tries == max_tries:
                print(
                    f'༼ つ ಥ_ಥ ༽つ {url} returned HTTP {resp.status_code} error...')
                sys.exit()
            else:
                time.sleep(0.5)
                tries += 1
                continue
        except RequestException:
            print(
                f'༼ つ ಥ_ಥ ༽つ Unable to reach {url} ...please try again later.')
            sys.exit()
        except ValueError:
            print('༼ つ ಥ_ಥ ༽つ Got an invalid response...please try again later.')
            sys.exit()


def to_string_list(l: List[float]) -> List[str]:
    """Converts list of numbers (float/int) into strings."""
    return [str(int(j)) if int(j) == j else str(j) for j in l]


def chunk(lst: List, n: int) -> List:
    """Greedy chunking. Divides `lst` into chunks of `n` items each. The last
    chunk will never have less than `n` items."""
    chunked = []
    q = len(lst) // n
    for i in range(q - 1):
        chunked.append(lst[i * n:i * n + n])
    chunked.append(lst[(q - 1) * n:])
    return chunked


def safe_mkdir(p: Path) -> None:
    try:
        os.mkdir(p)
    except FileExistsError:
        pass


class RateLimitedSession():
    """Wrapper class for `aiohttp.ClientSession` objects. Injects
    a limiter of `rate` HTTP calls per second.
    """

    def __init__(self, session: ClientSession, rate: int = 20, max_tokens: int = 20):
        self.session = session
        self.rate = rate
        self.max_tokens = max_tokens

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


async def gather_with_semaphore(n, *tasks):
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))


if __name__ == '__main__':
    pass
