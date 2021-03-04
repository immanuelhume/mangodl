import requests
from requests.exceptions import RequestException
import time
from typing import List


class DictX(dict):
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


def api_get(url) -> dict:
    """Expects a JSON response from `url`. Returns the data section."""
    while True:
        try:
            resp = requests.get(url)
            if resp.status_code != 200:
                time.sleep(0.5)
                continue
            else:
                return resp.json()['data']
        except RequestException:
            print(f'Unable to reach {url} D:')


def to_string_list(l: List[float]) -> List[str]:
    return [str(int(j)) if int(j) == j else str(j) for j in l]


def chunk(lst: List, n: int) -> List:
    chunked = []
    q = len(lst) // n
    for i in range(q - 1):
        chunked.append(lst[i * n:i * n + n])
    chunked.append(lst[(q - 1) * n:])
    return chunked


if __name__ == '__main__':
    print(chunk([1, 2, 3, 4, 5], 3))
