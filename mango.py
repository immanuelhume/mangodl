import requests
import os
import sys
import shutil
from bs4 import BeautifulSoup as bs
import lxml
from typing import Optional, Union, Dict, List, Tuple
import helpers
from helpers import api_get, to_string_list, chunk

api_base = 'https://api.mangadex.org/v2/'
search_url = 'https://mangadex.org/search?tag_mode_exc=any&tag_mode_inc=all&title='
login_url = 'https://mangadex.org/ajax/actions.ajax.php?function=login&nojs=1'


class Manga:
    """Manga objects.

    Initialize with manga id.

    Main attributes:
        title (str)             : Title of manga.
        volume_count (str/None) : Total number of volumes.
                                  None if info doesn't exist.
        chapter_count (str/None): Total number of chapters.
                                  None if info doesn't exist.
        self.eng_chapters (list): List of english chapters. Each
                                  chapter is a dict.
        self.chap_to_vol (dict) : Dict mapping chapter number (float) to
                                  volume number (int).
    """

    def __init__(self, id: Union[str, int]):
        self.url = api_base + f'manga/{id}'
        self.data = api_get(self.url)
        self.chapters_data = api_get(self.url + '/chapters')['chapters']
        self.chapters_data.reverse()

        data = self.data
        self.title = data['title']
        self.volume_count = data['lastVolume']
        self.chapter_count = data['lastChapter']
        self.eng_chapters = self.__get_eng_chapters()
        self.chap_to_vol = self.__compile_volume_info()

    def __get_eng_chapters(self) -> list:
        """Returns list of dictionaries. Each dictionary contains
        info for one chapter.

        All chapters are english, and chapter numbers do not repeat.
        """
        chapters = self.chapters_data

        eng_chapters = []
        chapters_added = []
        for chapter in chapters:
            language = chapter['language']
            chapter_number = chapter['chapter']
            if chapter_number not in chapters_added and language == 'gb':
                eng_chapters.append(chapter)
                chapters_added.append(chapter_number)
        del chapters_added

        return eng_chapters

    def __compile_volume_info(self) -> Dict[float, int]:
        """Attempts to assign a volume number to each chapter. Returns
        a dict mapping chapter number to volume number.

        Not every chapter comes with volume info. The function will read and 
        use whatever info is available first. This leaves the chapters with
        no volume info.

        For these chapters, we 1) slot them into existing volumes if they fit 
        or 2) create new volumes for them.

        If not a single chapter has volume info, default to 10 chapters per 
        volume.
        """

        contents: Dict[int, List[float]] = {}
        chap_to_vol: Dict[float, int] = {}
        orphaned_chapters: List(float) = []

        for chapter in self.eng_chapters:
            try:
                volume_num = int(chapter['volume'])
            except ValueError:
                volume_num = ''
            # chapter number is a float
            chapter_num = float(chapter['chapter'])
            if volume_num != '':
                if volume_num in contents:
                    contents[volume_num].append(chapter_num)
                else:
                    contents.update({volume_num: [chapter_num]})
            else:
                orphaned_chapters.append(chapter_num)
            chap_to_vol.update({chapter_num: volume_num})

        for volume in contents:
            contents[volume].sort()
        orphaned_chapters.sort()
        volume_numbers = sorted(contents)

        if orphaned_chapters and contents:
            for orphan in orphaned_chapters.copy():
                for volume_num in volume_numbers:
                    # generate lower and upper bounds
                    try:
                        previous_index = volume_numbers.index(volume_num) - 1
                        previous_volume = volume_numbers[previous_index]
                        lower_bound = contents[previous_volume][-1]
                    except IndexError:
                        # this means volume_num is the first volume
                        lower_bound = contents[volume_num][0] - 1
                    try:
                        next_index = volume_numbers.index(volume_num) + 1
                        next_volume = volume_numbers[next_index]
                        upper_bound = contents[next_volume][0]
                    except IndexError:
                        # this means volume_num is the last volume
                        upper_bound = contents[volume_num][-1] + 0.5

                    if lower_bound <= orphan <= upper_bound:
                        orphan_index = orphaned_chapters.index(orphan)
                        contents[volume_num].append(
                            orphaned_chapters.pop(orphan_index))
                        contents[volume_num].sort()
                        chap_to_vol.update({orphan: volume_num})

            if orphaned_chapters:
                chapter_lengths = [len(chapter_list)
                                   for chapter_list in contents.values()]
                average_length = round(
                    sum(chapter_lengths) / len(chapter_lengths))

                first_chapter = contents[volume_numbers[0]][0]
                last_chapter = contents[volume_numbers[-1]][-1]

                below = [
                    orphan for orphan in orphaned_chapters if orphan < first_chapter]
                below.reverse()
                above = [
                    orphan for orphan in orphaned_chapters if orphan > last_chapter]

                if below:
                    for new_volume in chunk(below, average_length):
                        new_volume_num = volume_numbers[0] - 1
                        volume_numbers.insert(0, new_volume_num)
                        for chap in new_volume:
                            chap_to_vol.update({chap: new_volume_num})
                if above:
                    for new_volume in chunk(above, average_length):
                        new_volume_num = volume_numbers[-1] + 1
                        volume_numbers.append(new_volume_num)
                        for chap in new_volume:
                            chap_to_vol.update({chap: new_volume_num})

        elif not contents:  # no volume info whatsoever
            for new_volume in chunk(orphaned_chapters, 10):
                new_volume_num = len(volume_numbers) + 1
                volume_numbers.append(new_volume_num)
                for chap in new_volume:
                    chap_to_vol.update({chap: new_volume_num})

        return chap_to_vol


class Chapter:
    """Chapter objects represent one chapter of the manga.

    Main attributes:
        hash (str)          : Hash for this chapter.
        chapter_num (str)   : Number of this chapter.
        page_links (list)   : List of links to image src of each page.

    Instance methods:
        download(raw_path): Downloads chapter into folder raw_path.

    """

    def __init__(self, id: Union[str, int]):
        self.url = api_base + f'chapter/{id}'
        self.data = api_get(self.url)
        data = self.data
        self.hash = data['hash']
        self.chapter_num = data['chapter']
        self.chapter_title = data['title']
        self.page_links = self.__get_page_links()

    def __get_page_links(self) -> list:
        server_base = self.data['server'] + f'{self.hash}/'
        return [server_base + page for page in self.data['pages']]

    def download(self, raw_path: str):
        chapter_path = os.path.join(raw_path, f'Chapter {self.chapter_num}')
        try:
            os.mkdir(chapter_path)
        except FileExistsError:
            pass
        for link in self.page_links:
            page_path = os.path.join(chapter_path, link.split('/')[-1])
            resp = requests.get(link, stream=True)
            with open(page_path, 'wb') as out_file:
                shutil.copyfileobj(resp.raw, out_file)


class Search:
    def __init__(self, username, password, login_url, search_url):
        self.login_url = login_url
        self.search_url = search_url
        self.username = username
        self.password = password
        self.__login()

    def __login(self):
        self.session = requests.Session()
        payload = {'login_username': self.username,
                   'login_password': self.password,
                   'remember_me': 1
                   }
        p = self.session.post(self.login_url, data=payload)
        # check if login succeeded
        soup = bs(p.text, 'lxml')
        if soup.title.string != 'Home - MangaDex':
            print('Login failed :(')
            print('Please check your username and password.')
            sys.exit()
        else:
            print('Login successful!')

    def get_manga_id(self, manga_title):
        resp = self.session.get(self.search_url + manga_title)
        soup = bs(resp.text, 'lxml')
        # get first result
        manga_entries = soup.find_all('div', class_='manga-entry')
        if manga_entries:
            for manga_entry in manga_entries:
                manga_title = manga_entry.find(
                    'a', class_='manga_title').string
                print(f'{manga_entries.index(manga_entry)}: {manga_title}')
            print('These are the results obtained.')
            index = int(
                input('Enter the index of the manga you want to download: '))
            link = manga_entries[index].find(
                'a', class_='manga_title').attrs['href']
            id = link.split('/')[2]
            return id
        else:
            return None


if __name__ == '__main__':
    manga_id = 26610
    chapter_id = 20220
    manga = Manga(manga_id)
    print(manga.compile_volume_info())
    # search = Search('immanuelhume', 'XnQAtrRmsW3ddF', login_url, search_url)
    # print(search.get_manga_id('spice and wolf'))
