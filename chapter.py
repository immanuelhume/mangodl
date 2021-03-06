import os
import shutil
import requests
from typing import Optional, Union, Dict, List, Tuple, Iterator

from helpers import api_get, safe_mkdir
from constants import api_base


class Chapter:
    """Chapter objects represent one chapter of the manga.

    Main attributes:
        hash (str)          : Hash of this chapter.
        id (str)            : Id of this chapter.
        chapter_num (str)   : The chapter number.
        volume_num (str)    : Volume number given for this chapter. Might
                              be empty string.

    Instance methods:
        download: Downloads chapter into folder raw_path.
    """

    def __init__(self, id: Union[str, int], api_base=api_base):
        self.url = api_base + f'chapter/{id}'
        self.data = api_get(self.url)
        data = self.data

        self.hash = data['hash']
        self.id = data['id']
        self.chapter_num = data['chapter']
        self.volume_num = data['volume']

    def get_page_links(self) -> List[str]:
        try:
            server_base = self.data['server'] + f'{self.hash}/'
            self.page_links = [server_base +
                               page for page in self.data['pages']]
            print(
                f'Data server found for id {self.id} (chapter {self.chapter_num}) ~(˘▾˘~)')
            return True
        except KeyError:
            print(
                f'No data server for id {self.id} (chapter {self.chapter_num}) ლ(ಠ益ಠლ)')
            return False

    def download(self, raw_path: str) -> None:
        """Creates a folder for this chapter inside `raw_path` and saves
        all images into the new folder."""
        session = requests.Session()
        chapter_path = os.path.join(raw_path, self.chapter_num)
        safe_mkdir(chapter_path)
        for link in self.page_links:
            page_path = os.path.join(chapter_path, link.split('/')[-1])
            resp = session.get(link, stream=True)
            with open(page_path, 'wb') as out_file:
                shutil.copyfileobj(resp.raw, out_file)

        print(f'Chapter {self.chapter_num} downloaded (~˘▾˘)~')
