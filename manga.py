import requests
from bs4 import BeautifulSoup as bs
import lxml
from typing import Optional, Union, Dict, List, Tuple
from helpers import api_get, chunk
from constants import api_base


class Manga:
    """Manga objects.

    Initialize with manga id and mangadex's api base url.

    Main attributes:
        title (str)             : Title of manga.
        eng_chapters (list)     : List of english chapters. Each chapter is 
                                  a dict.
        chap_to_vol (dict)      : Dict mapping chapter number (float) to
                                  volume number (int).
        volumes (list)          : List of all volume numbers (int).

    Instance methods:
        get_ids: Returns list of ids for english chapters founds.
    """

    def __init__(self, id: Union[str, int], api_base: str):
        self.url = api_base + f'manga/{id}'
        self.data = api_get(self.url)
        self.chapters_data = api_get(self.url + '/chapters')['chapters']
        self.chapters_data.reverse()

        data = self.data
        self.title = data['title']
        self.volume_count = data['lastVolume']
        self.chapter_count = data['lastChapter']
        self.eng_chapters = self.__get_eng_chapters()
        self.chap_to_vol, self.volumes = self.__compile_volume_info()

    def __get_eng_chapters(self) -> List[Dict]:
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

        print(f'Found {len(eng_chapters)} chapters for {self.title}.')

        return eng_chapters

    def get_ids(self) -> List[str]:
        chapters = self.eng_chapters
        return [chapter['id'] for chapter in chapters]

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

        return chap_to_vol, volume_numbers


if __name__ == '__main__':
    manga_id = 26610
    chapter_id = 20220
