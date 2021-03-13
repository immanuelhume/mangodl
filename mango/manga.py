import requests
import asyncio
import aiohttp
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable, Set
import sys
from pathlib import Path
import tqdm
import math
import pprint
import copy

from .helpers import (get_json, chunk, RateLimitedSession,
                      gather_with_semaphore, safe_to_int, horizontal_rule,
                      find_int_between, parse_range_input)
from .chapter import Chapter
from .config import mango_config

import logging
logger = logging.getLogger(__name__)
# set up logging prefixes for use in tqdm.tqdm.write
INFO_PREFIX = f'{__name__} | [INFO]: '
DEBUG_PREFIX = f'{__name__} | [DEBUG]: '
WARNING_PREFIX = f'{__name__} | [WARNING]: '
ERROR_PREFIX = f'{__name__} | [ERROR]: '
CRITICAL_PREFIX = f'{__name__} | [CRITICAL]: '

# load config
API_BASE = mango_config.get_api_base()


class Manga:
    """Manga objects.

    Initialize with manga id and mangadex's api base url.

    Main attributes:
        title (str)         : Title of manga.
        data (dict)         : Data portion of json obtained from api.
        chapters_data (list): List containing raw chapter dictionaries.
        serverless_chapters (list) : List of chapters w/o image servers.
        to_download (list)  : List of chapters staged for d/l.

    Methods:
        download_chapters   : Downloads chapters asynchronously for the manga.
        compile_volume_info : Checks and assigns volume numbers to all chapters.
    """

    def __init__(self, id: Union[str, int]):
        logger.debug('creating Manga object')
        self.url = API_BASE + f'manga/{id}'
        self.data = get_json(self.url)

        self.chapters_data = get_json(self.url + '/chapters')['chapters']
        self.chapters_data.reverse()

        self.title = self.data['title']
        self.p_downloads: List[Dict] = []
        self.s_downloads: List[Dict] = []
        self.serverless_chapters: List[str] = []

    def download_chapters(self, raw_path: Path) -> Dict[float, int]:
        """Downloads chapters into `raw_path`. Calls `compile_volume_info` when done.

        For now, it only downloads english chapters.

        Arguments:
            raw_path (str): Path to folder for raw images. Must already exist.

        Returns:
            Dict mapping chapter numbers (float) to their respective volumes (int).
            This is from calling `compile_volume_info`.

        """
        added: List[str] = []  # chapter numbers staged for download
        bad_chapters: List[str] = []  # chapter ids with no server
        downloaded: List[Dict] = []

        def is_english(chapter: Dict) -> bool:
            return chapter['language'] == 'gb'

        def is_new(chapter: Dict) -> bool:
            return chapter['chapter'] not in added

        async def check_server_and_download(session: RateLimitedSession,
                                            raw_chapter: Dict) -> Awaitable:
            if raw_chapter:
                chapter = Chapter(raw_chapter['id'])
                await chapter.load(session)
                if chapter.page_links:  # chapter has image server
                    await chapter.download(session, raw_path)
                else:  # chapter has no server - find a good chapter
                    bad_chapters.append(raw_chapter['id'])
                    await check_server_and_download(
                        session, find_another(raw_chapter))
            else:  # tried our best and still no servers
                self.serverless_chapters.append(raw_chapter['chapter'])
                tqdm.tqdm.write(
                    f'{CRITICAL_PREFIX}could not find any valid servers for chapter {raw_chapter["chapter"]} ಥ_ಥ')

        def find_another(bad_chapter: Dict) -> Optional[Chapter]:
            # find another instance of the chapter from self.chapter_data
            wanted_num = bad_chapter['chapter']
            tqdm.tqdm.write(
                f'{DEBUG_PREFIX}finding another server for chapter {wanted_num}')
            for raw_chapter in self.chapters_data:
                num = raw_chapter['chapter']
                chap_id = raw_chapter['id']
                if is_english(raw_chapter) and num == wanted_num and chap_id not in bad_chapters:
                    tqdm.tqdm.write(
                        f'{DEBUG_PREFIX}found another instance of chapter {wanted_num} (id {raw_chapter["id"]})')
                    return raw_chapter
            return None  # return None if no other chapter found

        async def main_download() -> Awaitable:
            downloads = []
            async with aiohttp.ClientSession() as session:
                session = RateLimitedSession(session, 20, 20)
                for raw_chapter in self.s_downloads:
                    downloads.append(
                        check_server_and_download(session, raw_chapter))
                    downloaded.append(raw_chapter)
                await gather_with_semaphore(2, *downloads)

        # stage chapters for download
        # this is just a first pass, will not account for missing servers
        for raw_chapter in self.chapters_data:
            if is_english(raw_chapter) and is_new(raw_chapter):
                self.p_downloads.append(raw_chapter)
                added.append(raw_chapter['chapter'])

        if not self.p_downloads:
            logger.critical(f'nothing to download for {self.title}')
            sys.exit()

        # prompt user here
        self._display_chapters()

        asyncio.run(main_download())

        logger.info('all chapters downloaded (ᵔᴥᵔ)')
        return self.compile_volume_info(downloaded)

    def _display_chapters(self):
        l = [safe_to_int(chap['chapter']) for chap in self.p_downloads]
        l.sort()
        missing_chaps = find_int_between(l)
        self.missing_chapters: List[str] = [str(_) for _ in missing_chaps]
        horizontal_rule()
        print(f'Found {len(l)} chapters for {self.title} \\ (•◡•) /')
        if len(l) == 1:
            print(f'Chapter {l[0]} can be downloaded.')
        else:
            print(f'    First chapter: {l[0]}')
            print(f'    Last chapter: {l[-1]}')
        if self.missing_chapters:
            mc = ', '.join(self.missing_chapters)
            logger.critical(f'these chapter(s) appear to be missing: {mc}')

        selection = self._get_download_range(l)

        self.s_downloads = [
            c for c in self.p_downloads if c['chapter'] in selection]

        if len(self.s_downloads) < len(self.p_downloads):
            self._confirm_download()

    def _get_download_range(self, chap_nums: List[Union[float, int]]) -> Set[str]:
        s: Set[str] = set()

        print('Which chapters to download?')
        print('You may select a range by using \',\' and \'-\' e.g. this entire string -> 1-10,15,20-33')
        print('↓ or just use one of these options ↓')
        # consider adding more options
        print('[a] - download all    [q] - quit app')

        r = input().strip()

        if r.lower() == 'a':
            return {str(_) for _ in chap_nums}
        elif r.lower() == 'q':
            logger.info(f'input {r} - quitting application')
            sys.exit()

        pr = parse_range_input(r)
        if pr:
            for ar in pr:
                b = ar.split('-')
                lower = safe_to_int(min(b))
                upper = safe_to_int(max(b))
                for c_num in chap_nums:
                    if lower <= c_num <= upper:
                        s.update([str(c_num)])
                        logger.info(f'chapter {c_num} queued for download')
                    else:
                        pass
            if not s:
                # nothing selected!
                logger.critical(
                    f'input of {r} did not correspond to any chapters45')
                return self._get_download_range(chap_nums)
        else:
            logger.error(f'invalid input - {r}')
            return self._get_download_range(chap_nums)

        return s

    def _confirm_download(self):
        selected_nums = [safe_to_int(c['chapter']) for c in self.s_downloads]
        print('These chapters will be downloaded:')
        c_count = len(self.s_downloads)
        pprint.pprint(selected_nums, compact=True,
                      width=min(c_count, 80))
        if c_count > 1:
            print(
                f'Proceed to download {c_count} chapters of {self.title}?')
        else:
            print(
                f'Proceed to download {c_count} chapter of {self.title}?')
        print('[y] - yes    [n] - select again    [q] - quit app')
        check = input().strip()
        if check.lower() == 'q':
            logger.info(f'received input \'{check}\' - exiting program')
            sys.exit()
        elif check.lower() == 'n':
            return self._display_chapters()
        elif check.lower() == 'y':
            print('(~˘▾˘)~ okay, starting download now ~(˘▾˘~)')
        else:
            logger.warning(f'invalid input - {check}')
            return self._confirm_download()

    def print_bad_chapters(self):
        if self.serverless_chapters:
            horizontal_rule()
            print(
                'These chapters were not downloaded because no image server could be found: ')
            print(', '.join(self.serverless_chapters))
        if self.missing_chapters:
            print(
                'These chapters were completely missing from mangadex:')
            print(', '.join(self.missing_chapters))

    @ staticmethod
    def compile_volume_info(chapters: List[Dict]) -> Dict[float, int]:
        """Attempts to assign a volume number to each chapter.

        Not every chapter comes with volume info. The function will read and
        use whatever info is available first. For chapters without volume
        data, we 1) slot them into existing volumes if they fit or 2) create
        new volumes for them.

        If not a single chapter has volume info, defaults to 10 chapters per
        volume.

        Arguments:
            chapters (list): List of raw chapter dictionaries.

        Returns:
            Dict mapping chapter number (float) to the assigned volume number (int).
        """

        logger.info('figuring out which chapter belongs to which volume')

        contents: Dict[int, List[float]] = {}
        chap_to_vol: Dict[float, int] = {}
        orphaned_chapters: List(float) = []

        # assign volumes for chapters which carry volume data
        for chapter in chapters:
            try:
                volume_num = int(chapter["volume"])
            except ValueError:
                volume_num = ''
                logger.warning(
                    f'no volume info for chapter {chapter["chapter"]}')
            else:
                logger.info(
                    f'chapter {chapter["chapter"]} -> volume {chapter["volume"]}')

            # chapter number is a float
            chapter_num = float(chapter["chapter"])

            if volume_num != '':
                if volume_num in contents:
                    contents[volume_num].append(chapter_num)
                else:
                    contents.update({volume_num: [chapter_num]})
            else:
                orphaned_chapters.append(chapter_num)
            chap_to_vol.update({chapter_num: volume_num})

        # sort the lists just to be safe
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

                        logger.debug(
                            f'chapter {safe_to_int(orphan)} -> volume {volume_num}')

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
                        logger.debug(f'creating volume {new_volume_num}')
                        volume_numbers.insert(0, new_volume_num)
                        for chap in new_volume:
                            chap_to_vol.update({chap: new_volume_num})
                            logger.debug(
                                f'chapter {safe_to_int(chap)} -> volume {new_volume_num}')
                if above:
                    for new_volume in chunk(above, average_length):
                        new_volume_num = volume_numbers[-1] + 1
                        logger.debug(f'creating volume {new_volume_num}')
                        volume_numbers.append(new_volume_num)
                        for chap in new_volume:
                            chap_to_vol.update({chap: new_volume_num})
                            logger.debug(
                                f'chapter {safe_to_int(chap)} -> volume {new_volume_num}')

        elif not contents:  # no volume info whatsoever
            logger.warning(
                f'no volume info found...defaulting to 10 chapters per volume')
            for new_volume in chunk(orphaned_chapters, 10):
                new_volume_num = len(volume_numbers) + 1
                volume_numbers.append(new_volume_num)
                for chap in new_volume:
                    chap_to_vol.update({chap: new_volume_num})
                    logger.debug(
                        f'chapter {safe_to_int(chap)} -> volume {new_volume_num}')

        logger.info('all chapters have been assigned to a volume')
        return chap_to_vol


if __name__ == '__main__':
    pass
