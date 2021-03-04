import requests
import os
import shutil
from bs4 import BeautifulSoup as bs
import lxml
from typing import Optional, Union
import helpers
from helpers import api_get

api_base = 'https://api.mangadex.org/v2/'
search_url = 'https://mangadex.org/search?tag_mode_exc=any&tag_mode_inc=all&title='
login_url = 'https://mangadex.org/ajax/actions.ajax.php?function=login&nojs=1'


class Manga:
    """Manga objects.

    Init with manga id.

    Attributes:
        url (str)               : Url to main manga API page.
        title (str)             : Title of manga.
        volume_count (str/None) : Total number of volumes. 
                                  None if info doesn't exist.
        chapter_count (str/None): Total number of chapters. 
                                  None if info doesn't exist.
        self.eng_chapters (list): List of english chapters. Each 
                                  chapter is a dict.
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

    def __get_eng_chapters(self) -> list:
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

    def compile_volume_info(self):
        def chapters_are_continuous(chapters):
            chapters_float = [float(chapter_num) for chapter_num in chapters]
            for chapter in chapters_float:
                next_chapter = chapters_float[chapters_float.index(
                    chapter) + 1]
                if next_chapter - chapter > 1:
                    return False
            return True

        def volumes_are_continuous(volumes):
            string_volumes = list(volumes.keys())
            volumes = []
            for volume in string_volumes:
                volumes.append(int(volume))
            volumes.sort()
            first_vol = volumes[0]
            last_vol = volumes[-1]
            return volumes == list(range(first_vol, last_vol + 1))

        all_chapters = []
        contents = {}
        orphaned_chapters = []

        for chapter in self.eng_chapters:
            volume_num = chapter['volume']
            chapter_num = chapter['chapter']
            all_chapters.append(chapter_num)
            if volume_num != '':
                if volume_num in contents:
                    contents[volume_num].append(chapter_num)
                else:
                    contents.update({volume_num: [chapter_num]})
            else:
                orphaned_chapters.append(chapter_num)

        # get average number of chapters in one volume
        if contents:
            chapter_lengths = [len(chapter_list)
                               for chapter_list in contents.values()]
            average_length = round(sum(chapter_lengths) / len(chapter_lengths))

        if orphaned_chapters and contents:
            for orphan in orphaned_chapters.copy():
                for volume_num, chapter_list in contents.items():
                    first_chap = float(chapter_list[0])
                    last_chap = float(chapter_list[-1])
                    if (first_chap - 1) <= float(orphan) <= last_chap:
                        orphan_index = orphaned_chapters.index(orphan)
                        chapter_list.append(
                            orphaned_chapters.pop(orphan_index))
            # separate into below and above volumes
            if chapters_are_continuous(orphaned_chapters):
                pass

        elif not contents:
            pass
        return contents, orphaned_chapters


class Chapter:
    def __init__(self, id: Union[str, int]):
        self.url = api_base + f'chapter/{id}'
        self.data = api_get(self.url)
        data = self.data
        self.hash = data['hash']
        self.volume = data['volume']
        self.chapter = data['chapter']
        self.chapter_title = data['title']
        self.page_links = self.__get_page_links()

    def __get_page_links(self) -> list:
        server_base = self.data['server'] + f'{self.hash}/'
        return [server_base + page for page in self.data['pages']]

    def download(self, base_path: str):
        chapter_path = os.path.join(base_path, f'Chapter {self.chapter}')
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
        self.session.post(self.login_url, data=payload)

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
    manga_id = 19434
    chapter_id = 20220
    #manga = Manga(manga_id)
    # print(manga.compile_volume_info())
    search = Search('immanuelhume', 'XnQAtrRmsW3ddF', login_url, search_url)
    print(search.get_manga_id('kaguya sama'))
