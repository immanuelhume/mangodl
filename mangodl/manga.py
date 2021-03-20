"""
This module contains the Manga class, used to represent
whatever manga is to be downloaded.
"""

import requests
import asyncio
import aiohttp
import sys
from collections import defaultdict
from tqdm import tqdm
import pprint
from typing import (Optional,
                    Union,
                    Dict,
                    List,
                    Tuple,
                    Iterator,
                    Awaitable,
                    Set)
from pathlib import Path

from .cli import ARGS
from .chapter import Chapter
from .filesys import FileSys
from .config import mangodl_config
from .helpers import (get_api_data,
                      chunk,
                      RateLimitedSession,
                      gather_with_semaphore,
                      safe_to_int,
                      horizontal_rule,
                      find_int_between,
                      parse_range_input,
                      _Getch,
                      extract_nums,
                      say_goodbye)

import logging
logger = logging.getLogger(__name__)


# set up logging prefixes for use in tqdm.write
WARNING_PREFIX = f'{__name__} | [WARNING]: '
ERROR_PREFIX = f'{__name__} | [ERROR]: '
CRITICAL_PREFIX = f'{__name__} | [CRITICAL]: '

# load from config file
API_BASE = mangodl_config.get_api_base()

getch = _Getch()


class Manga:
    """
    Manga objects represent a single manga. Mostly contains attributes
    to handle the download process.

    Parameters
    ----------
    id : str or int
        Mangadex id for the manga.

    Attributes
    ----------
    url : str
    title : str
    data : dict
        The 'data' section of JSON string returned by API.
    chs_data : list
        Raw chapter dictionaries.
    p_downloads : list
        All chapters which can be downloaded.
    s_downloads : list
        Chapters selected by user for download.
    missing : list
        Chapters missing from mangadex.
    serverless : list
        Chapters listed on mangadex but without an image server.
    """

    def __init__(self, id: Union[str, int]):
        logger.debug('creating Manga object')
        self.url = API_BASE + f'manga/{id}'

        self.data = get_api_data(self.url)
        self.chs_data = get_api_data(self.url + '/chapters')['chapters']
        self.chs_data.reverse()  # api gives chapters from last to first
        self.title = self.data['title']

        self.p_downloads: List[Dict] = []  # 'possible' downloads
        self.s_downloads: List[Dict] = []  # selected downloads (by user)
        self.downloaded: List[Chapter] = []  # downloaded chapters
        self.missing: List[int] = []  # missing chapters
        self.serverless: List[Union[float, int]] = []  # chapters listed but no server

    def download_chapters(self,
                          fs: FileSys,
                          lang: str,
                          saver: bool,
                          rate_limit: int,
                          no_volume: bool,
                          vol_len: int,
                          no_prompt: bool = False):
        """
        Saves all chapters into a folder.

        Parameters
        ----------
        fs : filesys.FileSys instance
        lang : str
            Manga language.
        saver : bool
            Lower quality images if set to True.
        rate_limit : int
            Used to construct a `RateLimitedSession` instance.
        no_volume : bool
            Automatically converts into volume if False.
        vol_len : int
            Default length per volume if not provided by mangadex.
        no_prompt : bool, default False
            If set to True, will download every chapter found without prompting user.

        Returns
        -------
        None
        """
        added: List[str] = []  # chapter numbers staged for download
        bad_chs: List[str] = []  # chapter ids with no server

        def is_right_lang(raw_ch: Dict) -> bool:
            return raw_ch['language'] == lang

        # check if we've already queued a chapter for download
        def is_new(raw_ch: Dict) -> bool:
            return raw_ch['chapter'] not in added

        async def check_server_and_download(session: RateLimitedSession,
                                            raw_ch: Optional[Dict]) -> Awaitable:
            """Downloads one chapter."""
            if raw_ch:
                chapter = Chapter(raw_ch['id'], saver)
                await chapter.load(session)
                if chapter.page_links:
                    # chapter has image server - proceed with download
                    await chapter.download(session, fs.raw_path)
                    self.downloaded.append(chapter)
                else:
                    # chapter has no server - find another
                    bad_chs.append(raw_ch['id'])
                    await check_server_and_download(session, find_another(raw_ch))
            else:
                # searched all uploads of this chapter and still no servers
                self.serverless.append(safe_to_int(raw_ch['chapter']))
                tqdm.write(f'{CRITICAL_PREFIX}could not find any valid servers for chapter {raw_ch["chapter"]} ಥ_ಥ')

        def find_another(bad_ch: Dict) -> Optional[Dict]:
            # find another instance of the chapter from self.chapter_data
            wanted_num = bad_ch['chapter']
            tqdm.write(f'finding another server for chapter {wanted_num}')
            for raw_ch in self.chs_data:
                num = raw_ch['chapter']
                ch_id = raw_ch['id']
                if is_right_lang(raw_ch) and num == wanted_num and ch_id not in bad_chs:
                    tqdm.write(f'found another instance of chapter {wanted_num} (id {raw_ch["id"]})')
                    return raw_ch

            # return None if no other chapter found
            return None

        async def main_download() -> Awaitable:
            tasks = []
            async with aiohttp.ClientSession() as session:
                session = RateLimitedSession(session, rate_limit, rate_limit)
                for raw_ch in self.s_downloads:
                    tasks.append(check_server_and_download(session, raw_ch))
                await gather_with_semaphore(2, *tasks)

        # stage chapters for download by adding to `self.p_downloads`
        for raw_ch in self.chs_data:
            if is_right_lang(raw_ch) and is_new(raw_ch):
                self.p_downloads.append(raw_ch)
                added.append(raw_ch['chapter'])

        if not self.p_downloads:
            logger.critical(f'no chapters found for {self.title}')
            if ARGS.url:
                logger.info(f'quitting application')
                sys.exit()
            from .mangodl import next_manga
            next_manga()

        if no_prompt:
            self.s_downloads = self.p_downloads
        else:
            # show some info to the user and get input
            self._display_chs()

        # prepare folders for download
        fs.setup_folders()

        asyncio.run(main_download())
        logger.info('all chapters downloaded (ᵔᴥᵔ)')

        # ensure every chapter has a volume
        if not no_volume:
            self._compile_volume_info(vol_len)

    def _display_chs(self):
        """Print out some info about the chapters found and solicits user input
        before commencing download."""

        # separate the valid chapter numbers from invalid ones
        _ch_nums = [safe_to_int(ch['chapter']) for ch in self.p_downloads]
        ch_nums, ch_str_nums = extract_nums(_ch_nums)
        ch_nums.sort()

        horizontal_rule()
        print(f'Found {len(self.p_downloads)} chapter(s) for {self.title}')
        if len(ch_nums) == 1:
            print(f'Chapter {ch_nums[0]} can be downloaded.')
        else:
            print(f'    First chapter: {ch_nums[0]}')
            print(f'    Last chapter: {ch_nums[-1]}')

        # check for missing chapters in between
        self.missing = find_int_between(ch_nums)
        if self.missing:
            n = len(self.missing)
            logger.critical(f'\033[91m{n} chapter appears to be missing:')
            pprint.pprint([ch for ch in self.missing],
                          compact=True,
                          width=min(len(self.missing), 80))
            print('\033[0m', end='')

        # prompt user for download range
        selection = self._get_download_range(ch_nums)
        self.s_downloads = [ch for ch in self.p_downloads if ch['chapter'] in selection]

        # now deal with those without any chapter numbers
        if ch_str_nums:
            nameless_chs = [ch for ch in self.p_downloads if isinstance(safe_to_int(ch['chapter']), str)]
            horizontal_rule()
            self._handle_nameless(nameless_chs)

        # if not all chapters were selected
        if len(self.s_downloads) < len(self.p_downloads):
            self._confirm_download()

    def _get_download_range(self, ch_nums: List[Union[float, int]]) -> Set[str]:
        """
        Prompts user to select a range of chapters to download.
        Returns a set of chapter numbers in str form.
        """
        s: Set[str] = set()

        def collect_range_input() -> None:
            """Manages user input for a range of chapters."""
            r = input('Specify a range: ')
            parsed = parse_range_input(r)
            if parsed:
                for sect in parsed:
                    b = sect.split('-')
                    lower = safe_to_int(min(b))
                    upper = safe_to_int(max(b))
                    for ch_num in ch_nums:
                        if lower <= ch_num <= upper:
                            s.add(str(ch_num))
                            logger.info(f'chapter {ch_num} queued for download')
                        else:
                            logger.info(f'chapter {ch_num} will not be downloaded')
                if not s:
                    # nothing selected!
                    logger.critical(f'input of {r} did not correspond to any chapters')
                    return self._get_download_range(ch_nums)
            else:
                logger.error(f'invalid input - {r}')
                return collect_range_input()

        print('Which chapters to download?')

        if ARGS.url:
            # don't print the 'search another manga' option
            print('[a] - download all chapters')
            print('[r] - select custom range')
            print('[q] - quit app')
            c = getch()

            if c.lower() == 'a':
                logger.info(f'input \'{c}\' - download all chapters available')
                return {str(_) for _ in ch_nums}
            elif c.lower() == 'r':
                logger.info(f'input \'{c}\' - select custom range')
                collect_range_input()
            elif c.lower() == 'q':
                logger.info(f'input \'{c}\' - quitting application')
                say_goodbye()
                sys.exit()
            else:
                logger.error(f'invalid input - \'{c}\'')
                return self._get_download_range(ch_nums)
        else:
            print('[a] - download all chapters')
            print('[r] - select custom range')
            print('[s] - search for another manga instead')
            print('[q] - quit app')
            c = getch()

            if c.lower() == 'a':
                logger.info(f'input \'{c}\' - download all chapters available')
                return {str(_) for _ in ch_nums}
            elif c.lower() == 'r':
                logger.info(f'input \'{c}\' - select custom range')
                collect_range_input()
            elif c.lower() == 's':
                logger.warning(
                    f'input \'{c}\' - abandoning the manga {self.title}')
                from .mangodl import search_another
                search_another()
            elif c.lower() == 'q':
                logger.info(f'input \'{c}\' - quitting application')
                say_goodbye()
                sys.exit()
            else:
                logger.error(f'invalid input - \'{c}\'')
                return self._get_download_range(ch_nums)

        return s

    def _confirm_download(self) -> None:
        """Allows user to check the chapters queued for download before continuing."""
        horizontal_rule()

        selected_nums = [safe_to_int(c['chapter']) for c in self.s_downloads]
        print('These chapters will be downloaded:')
        ch_count = len(self.s_downloads)
        pprint.pprint(selected_nums,
                      compact=True,
                      width=min(ch_count, 80))
        print(f'Proceed to download {ch_count} chapter(s) of {self.title}?')

        if ARGS.url:
            print('[y] - yes, confirm download')
            print('[r] - choose range again')
            print('[q] - quit app')
            check = getch()

            if check.lower() == 'y':
                logger.info('(~˘▾˘)~ okay, starting download now ~(˘▾˘~)')
            elif check.lower() == 'r':
                return self._display_chs()
            elif check.lower() == 'q':
                logger.info(f'received input \'{check}\' - quitting application')
                sys.exit()
            else:
                logger.warning(f'invalid input - \'{check}\'')
                return self._confirm_download()
        else:
            print('[y] - yes, confirm download')
            print('[r] - choose range again')
            print('[s] - search for another manga instead')
            print('[q] - quit app')
            check = getch()

            if check.lower() == 'y':
                logger.info('(~˘▾˘)~ okay, starting download now ~(˘▾˘~)')
            elif check.lower() == 'r':
                return self._display_chs()
            elif check.lower() == 's':
                logger.warning(f'abandoning manga -> {self.title}')
                from .mangodl import search_another
                search_another()
            elif check.lower() == 'q':
                logger.info(f'received input \'{check}\' - quitting application')
                sys.exit()
            else:
                logger.warning(f'invalid input - \'{check}\'')
                return self._confirm_download()

    def _handle_nameless(self, nameless_chs: List) -> None:
        """Lets user decide what to do with chapters which have no chapter number."""
        print(f'Found {len(nameless_chs)} chapter(s) with no chapter number ಠ_ಠ')
        ch_titles = [ch['title'] for ch in nameless_chs]
        print(f'Title(s):', ', '.join(ch_titles))
        print('↑ download or ignore? ↑')
        print('[y] - download as well    [n] - ignore')
        c = getch()

        if c.lower() == 'y':
            logger.info(f'got input - {c}, will include in downloads')
            self.s_downloads += nameless_chs
        elif c.lower() == 'n':
            logger.info(f'got input - {c}, will ignore')
        else:
            # reject input and try again
            logger.error(f'got invalid input -{c}')
            return self._handle_nameless(nameless_chs)

    def _compile_volume_info(self, vol_len: int) -> None:
        """Assigns a volume number to all downloaded mangas via their 
        respective Chapter instances."""
        logger.info('figuring out which chapter belongs to which volume')

        orphans: Chapter = []  # those chapters without volumes
        prelim_map = defaultdict(list)  # maps volume to its chapters

        for ch in self.downloaded:
            if ch.ch_num == '_':
                # bad news! a chapter without a chapter number
                logger.warning(f'chapter id {ch.id} has no chapter number')
            elif ch.vol_num == '':
                logger.info(f'chapter {ch.ch_num} has no volume number')
                orphans.append(ch)
            else:
                prelim_map[ch.vol_num].append(ch.ch_num)

        vol_nums = sorted(prelim_map)  # list of volume numbers so far

        def fit_between():
            """
            Sees if the orphans can fit into existing volumes
            by checking the lower and upper bounds for each volume.
            """
            for i, orphan in enumerate(orphans[:]):
                for j, vol_num in enumerate(vol_nums):
                    try:
                        previous_vol = vol_nums[j - 1]
                        lower_bound = prelim_map[previous_vol][-1]
                    except IndexError:
                        # vol_num is the first volume
                        lower_bound = prelim_map[vol_num][0] - 1
                    try:
                        next_vol = vol_nums[j + 1]
                        upper_bound = prelim_map[next_vol][0]
                    except IndexError:
                        # vol_num is the last vol
                        upper_bound = prelim_map[vol_num][-1] + 0.5

                    if lower_bound <= orphan.ch_num <= upper_bound:
                        # orphaned chapter can be fit into currently existing volume!
                        orphan.vol_num = vol_num
                        prelim_map[vol_num].append(orphans.pop(i).ch_num)  # remove the orphan
                        prelim_map[vol_num].sort()
                        logger.debug(f'chapter {orphan.ch_num} -> volume {vol_num}')

        def extrapolate():
            """Create new volumes by extrapolating from current ones."""
            # compute average length of volumes detected so far
            ch_lens = [len(vol) for vol in prelim_map.values()]
            avg_len = round(sum(ch_lens) / len(ch_lens))

            first_chapter = prelim_map[vol_nums[0]][0]
            last_chapter = prelim_map[vol_nums[-1]][-1]

            below: Chapter = []  # chapter falls below range of current volumes
            above: Chapter = []  # chapter is above range of current volumes

            for orphan in orphans:
                if orphan.ch_num < first_chapter:
                    below.append(orphan)
                elif orphan.ch_num > last_chapter:
                    above.append(orphan)
                else:
                    # I don't think this is possible
                    logger.warning(f'chapter {orphan.ch_num} is a rogue chapter!')
                    pass

            below.reverse()  # we want from highest to lowest

            if below:
                for new_vol in chunk(below, avg_len):
                    new_vol_num = vol_nums[0] - 1
                    vol_nums.insert(0, new_vol_num)
                    logger.debug(f'creating volume {new_vol_num}')

                    for ch in new_vol:
                        prelim_map[new_vol_num].append(ch.ch_num)
                        ch.vol_num = new_vol_num
                        logger.debug(f'chapter {ch.ch_num} -> volume {new_vol_num}')
            if above:
                for new_vol in chunk(above, avg_len):
                    new_vol_num = vol_nums[-1] + 1
                    vol_nums.append(new_vol_num)
                    logger.debug(f'creating volume {new_vol_num}')

                    for ch in new_vol:
                        prelim_map[new_vol_num].append(ch.ch_num)
                        ch.vol_num = new_vol_num
                        logger.debug(f'chapter {ch.ch_num} -> volume {new_vol_num}')

        def from_scratch(vol_len):
            """Call this if there is no volume info whatsoever. Makes volumes of a set length."""
            logger.warning(f'no volume info found - defaulting to {vol_len} chapters per volume')

            for new_vol in chunk(orphans, vol_len):
                new_vol_num = len(vol_nums) + 1
                logger.info(f'creating new volume - vol. {new_vol_num}')
                vol_nums.append(new_vol_num)
                for ch in new_vol:
                    prelim_map[new_vol_num].append(ch.ch_num)
                    ch.vol_num = new_vol_num
                    logger.debug(f'chapter {ch.ch_num} -> volume {new_vol_num}')

        if orphans and vol_nums:
            fit_between()
            if orphans:
                extrapolate()
        elif not vol_nums:
            from_scratch(vol_len)
        else:
            # all chapters already have volumes assigned
            logger.info('all chapters come naturally with volume info')

        logger.info('all chapters have been assigned to a volume ^_^')

    def print_bad_chapters(self):
        """Prints all chapters for which no server was found."""
        if self.serverless:
            horizontal_rule()
            print('These chapters were not downloaded because no image server could be found: ')
            pprint.pprint(self.serverless,
                          compact=True,
                          width=min(len(self.serverless), 80))
