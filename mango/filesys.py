import os
import shutil
from distutils.dir_util import copy_tree
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable
from pathlib import Path
from .config import mango_config
from .helpers import safe_mkdir
from .chapter import Chapter

import logging
logger = logging.getLogger(__name__)

# set up from config
ROOT_DIR: Path = mango_config.get_root_dir()


class FileSys:
    """FileSys objects handle file system related tasks when downloading
    manga. Init with root directory and Manga title.

    Attributes:
        manga_title (str)   : Title of manga.
        base_path (str)     : Absolute path to directory where the current
                              manga is to be downloaded.
        raw_path (str)      : A folder within `base_path` which holds the raw
                              image files of each chapter.

    Methods:
        to_cbz          : Creates a .cbz archive for a folder.
        create_volumes  : Archives chapters into respective volumes.
    """

    def __init__(self, manga_title: str):
        self.manga_title = manga_title
        self.base_path = os.path.join(ROOT_DIR, self.manga_title)
        self.raw_path = os.path.join(self.base_path, 'raw')

    def setup_folders(self):
        safe_mkdir(self.base_path)
        safe_mkdir(self.raw_path)

    def create_volumes(self, downloaded: List[Chapter]) -> None:
        """Archives chapters into respective volumes.

        Creates a new folder `vols_path` at `base_path`. Volume folders 
        are created inside `vols_path`. Once zipped, the unzipped folder
        is removed.

        Arguments:
            ch_map (dict): Dict mapping chapter number to its volume number.
        """
        logger.info('(っ˘ڡ˘ς) preparing to compile into volumes...')

        # make a new folder to store compiled volumes
        vols_path = os.path.join(self.base_path, self.manga_title)
        safe_mkdir(vols_path)

        for ch in downloaded:
            new_ch_path = os.path.join(
                vols_path, f'{ch.vol_num}', str(ch.ch_num))
            copy_tree(ch.ch_path, new_ch_path)
            logger.debug(f'copied {ch.ch_path} -> {new_ch_path}')

        for vol in os.scandir(vols_path):
            old_name = vol.path
            new_name = os.path.join(os.path.split(vol.path)[
                                    0], f'{self.manga_title}, Vol. {vol.name}')
            os.rename(old_name, new_name)

            self.to_cbz(os.path.join(vols_path, new_name), vols_path)

            # delete the non-archived folder
            shutil.rmtree(new_name)
            logger.debug(f'{new_name} deleted')

    @staticmethod
    def to_cbz(dir_to_zip: Path, destination: Path) -> None:
        """Creates .cbz file for folder `dir_to_zip`.

        Arguments:
            dir_to_zip (str)  : Absolute path to folder to zip.
            destination (str) : Directory to store the new .cbz file. Should
                                already exist. 
        """

        os.chdir(dir_to_zip)
        archive_name = os.path.split(dir_to_zip)[-1]
        archive_path = os.path.join(destination, archive_name)
        shutil.make_archive(base_name=archive_path, format='zip')
        logger.debug(f'made .zip archive -> {archive_path}')

        new_volume_path = os.path.join(destination, f'{archive_name}.zip')
        base_name = os.path.splitext(new_volume_path)[0]
        final_name = base_name + '.cbz'
        os.rename(new_volume_path, final_name)

        logger.debug(f'{new_volume_path} renamed -> {final_name}')
        logger.info(f'( ^_^）o自  {archive_name} compiled  自o（^_^ )')
