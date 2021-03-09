import os
import sys
import requests
from requests.exceptions import RequestException
import time
import asyncio
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable


class DictX(dict):
    """Helper class which provides dictionaries with dot notation."""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __repr__(self):
        return '<DictX ' + dict.__repr__(self) + '>'


def get_json(url: str, session=False, time_out=20, MAX_TRIES: int = 10) -> Dict:
    """Expects a JSON response from `url`. Returns the data section
    as dict."""
    tries = 1
    while True:
        try:
            if session:  # use session if passed
                resp = session.get(url, timeout=time_out)
            else:
                resp = requests.get(url, timeout=time_out)

            if resp.ok:
                return resp.json()['data']
            elif tries == MAX_TRIES:
                print('༼ つ ಥ_ಥ ༽つ Got HTTP {resp.status_code} error...')
                sys.exit()
            else:
                time.sleep(0.5)
                tries += 1
                continue
        except RequestException:
            print(
                f'༼ つ ಥ_ಥ ༽つ Unable to reach {url}...please try again later.')
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


def safe_mkdir(p: str) -> None:
    try:
        os.mkdir(p)
    except FileExistsError:
        pass


class RateLimitedSession():
    """Wrapper class for `aiohttp.ClientSession` objects. Injects
    a limiter of `rate` HTTP calls per second.
    """

    def __init__(self, session, rate: int = 10, max_tokens: int = 10):
        self.session = session
        self.RATE = rate
        self.MAX_TOKENS = max_tokens

        self.tokens = self.MAX_TOKENS
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
        new_tokens = time_since_update * self.RATE
        if self.tokens + new_tokens >= 1:
            self.tokens = min(self.tokens + new_tokens, self.MAX_TOKENS)
            self.updated_at = now


if __name__ == '__main__':
    pass
