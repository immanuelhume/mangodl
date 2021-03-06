import os
import shutil
from typing import Optional, Union, Dict, List, Tuple
import requests
from helpers import api_get
from constants import api_base


class Chapter:
    """Chapter objects represent one chapter of the manga.

    Main attributes:
        hash (str)          : Hash for this chapter.
        chapter_num (str)   : Number of this chapter.
        page_links (list)   : List of links to image src of each page.

    Instance methods:
        download: Downloads chapter into folder raw_path.
    """

    def __init__(self, id: Union[str, int], api_base):
        self.url = api_base + f'chapter/{id}'
        self.data = api_get(self.url)
        data = self.data

        self.hash = data['hash']
        self.chapter_num = data['chapter']
        self.chapter_title = data['title']
        self.page_links = self.__get_page_links()

    def __get_page_links(self) -> List[str]:  # TODO server might not exist
        server_base = self.data['server'] + f'{self.hash}/'
        return [server_base + page for page in self.data['pages']]

    def download(self, raw_path: str) -> None:
        """Creates a folder for this chapter inside <raw_path> and saves 
        all images into the new folder."""
        session = requests.Session()
        chapter_path = os.path.join(raw_path, self.chapter_num)
        try:
            os.mkdir(chapter_path)
        except FileExistsError:
            pass
        for link in self.page_links:
            page_path = os.path.join(chapter_path, link.split('/')[-1])
            resp = session.get(link, stream=True)
            with open(page_path, 'wb') as out_file:
                shutil.copyfileobj(resp.raw, out_file)

        print(f'Chapter {self.chapter_num} downloaded!')
