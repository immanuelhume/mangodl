import os
import sys
import requests
from requests.exceptions import RequestException
import time
from typing import List, Dict


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


def api_get(url: str, session=False) -> Dict:
    """Expects a JSON response from `url`. Returns the data section
    as dict."""
    while True:
        try:
            if session:
                resp = session.get(url)
            else:
                resp = requests.get(url)

            if resp.ok:
                return resp.json()['data']
            else:
                time.sleep(0.5)
                continue
        except RequestException:
            print(f'༼ つ ಥ_ಥ ༽つ Unable to reach {url}...')
            sys.exit()


def to_string_list(l: List[float]) -> List[str]:
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


if __name__ == '__main__':
    pass
