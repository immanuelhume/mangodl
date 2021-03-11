import requests
import asyncio
import aiohttp
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable
from pathlib import Path

from .helpers import get_json, chunk, RateLimitedSession, gather_with_semaphore
from .chapter import Chapter
from .config import mango_config

# load config
config = mango_config.read_config()
API_BASE = config['links']['api_base']


class Manga:
    """Manga objects.

    Initialize with manga id and mangadex's api base url.

    Main attributes:
        title (str)         : Title of manga.
        data (dict)         : Data portion of json obtained from api.
        chapters_data (list): List containing raw chapter dictionaries.

    Methods:
        download_chapters   : Downloads chapters asynchronously for the manga.
        compile_volume_info : Checks and assigns volume numbers to all chapters.
    """

    def __init__(self, id: Union[str, int]):
        self.url = API_BASE + f'manga/{id}'
        self.data = get_json(self.url)

        self.chapters_data = get_json(self.url + '/chapters')['chapters']
        self.chapters_data.reverse()

        self.title = self.data['title']

    def download_chapters(self, raw_path: Path) -> Dict[float, int]:
        """Downloads chapters into `raw_path`. Calls `compile_volume_info` when done.

        For now, it only downloads english chapters.

        Arguments:
            raw_path (str): Path to folder for raw images. Must already exist.

        Returns:
            Dict mapping chapter numbers (float) to their respective volumes (int).
            This is from calling `compile_volume_info`.

        """
        def __is_english(chapter: Dict) -> bool:
            return chapter['language'] == 'gb'

        def __is_new(chapter: Dict) -> bool:
            return chapter['chapter'] not in added

        async def check_server_and_download(session: RateLimitedSession,
                                            chapter: Chapter) -> Awaitable:
            if chapter:
                await chapter.load(session)
                if chapter.page_links:
                    await chapter.download(session, raw_path)
                else:  # chapter has no server - find a good chapter
                    bad_chapters.append(chapter)
                    check_server_and_download(session, find_another(chapter))
            else:
                print(
                    f'Could not find any valid servers for chapter {chapter["chapter"]} ಥ_ಥ')

        def find_another(bad_chapter: Chapter) -> Dict:
            # find another instance of the chapter from self.chapter_data
            wanted_num = bad_chapter.chapter_num
            for raw_chapter in self.chapters_data:
                num = raw_chapter['chapter']
                if __is_english(raw_chapter) and num == wanted_num and raw_chapter not in bad_chapters:
                    return raw_chapter
            return None  # return None if no other chapter found

        async def main_download(to_download: List[Chapter]) -> Awaitable:
            downloads = []
            async with aiohttp.ClientSession() as session:
                session = RateLimitedSession(session, 20, 20)
                for chapter in to_download:
                    downloads.append(
                        check_server_and_download(session, chapter))
                    downloaded.append(chapter)
                await gather_with_semaphore(2, *downloads)

        added: List[str] = []
        to_download: List[Chapter] = []
        downloaded: List[Chapter] = []
        bad_chapters: List[Chapter] = []

        # stage chapters for download
        for raw_chapter in self.chapters_data:
            if __is_english(raw_chapter) and __is_new(raw_chapter):
                chapter = Chapter(raw_chapter['id'])
                to_download.append(chapter)
                added.append(raw_chapter['chapter'])

        asyncio.run(main_download(to_download))

        return self.compile_volume_info(downloaded)

    @staticmethod
    def compile_volume_info(chapters: List[Chapter]) -> Dict[float, int]:
        """Attempts to assign a volume number to each chapter.

        Not every chapter comes with volume info. The function will read and
        use whatever info is available first. For chapters without volume 
        data, we 1) slot them into existing volumes if they fit or 2) create 
        new volumes for them.

        If not a single chapter has volume info, defaults to 10 chapters per
        volume.

        Arguments:
            chapters (list): List of Chapter objects.

        Returns:
            Dict mapping chapter number (float) to the assigned volume number (int).
        """

        contents: Dict[int, List[float]] = {}
        chap_to_vol: Dict[float, int] = {}
        orphaned_chapters: List(float) = []

        # assign volumes for chapters which carry volume data
        for chapter in chapters:
            try:
                volume_num = int(chapter.volume_num)
            except ValueError:
                volume_num = ''
            # chapter number is a float
            chapter_num = float(chapter.chapter_num)

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
                        # volume_num is the first volume
                        lower_bound = contents[volume_num][0] - 1
                    try:
                        next_index = volume_numbers.index(volume_num) + 1
                        next_volume = volume_numbers[next_index]
                        upper_bound = contents[next_volume][0]
                    except IndexError:
                        # volume_num is the last volume
                        upper_bound = contents[volume_num][-1] + 0.5

                    if lower_bound <= orphan <= upper_bound:
                        orphan_index = orphaned_chapters.index(orphan)
                        contents[volume_num].append(
                            orphaned_chapters.pop(orphan_index))
                        contents[volume_num].sort()
                        chap_to_vol.update({orphan: volume_num})

            if orphaned_chapters:
                # compute average length of volumes detected so far
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


if __name__ == '__main__':
    pass
