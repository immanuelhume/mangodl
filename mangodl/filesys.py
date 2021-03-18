"""Contains the FileSys class for file operations."""

import os
import shutil
from distutils.dir_util import copy_tree
from typing import Optional, Union, Dict, List, Tuple, Iterator, Awaitable
from pathlib import Path
from tqdm import tqdm

from .config import mangodl_config
from .helpers import safe_mkdir
from .chapter import Chapter

import logging
logger = logging.getLogger(__name__)

# set up from config
ROOT_DIR: Path = mangodl_config.get_root_dir()

# set up logging prefixes for use in tqdm.tqdm.write
WARNING_PREFIX = f'{__name__} | [WARNING]: '
ERROR_PREFIX = f'{__name__} | [ERROR]: '
CRITICAL_PREFIX = f'{__name__} | [CRITICAL]: '


class FileSys:
    """
    FileSys objects handle file operations when downloading
    manga.

    Parameters
    ----------
    manga_title : str
        Title of manga downloaded. This will be used in naming the directories
        and files.

    Attributes
    ----------
    base_path : str
        Absolute path to base directory for this manga. This is inside the 
        root directory specified by the user and stored as the global `ROOT_DIR`.
    raw_path : str
        Folder within `base_path` to contain raw chapters.

    Methods
    -------
        create_volumes(downloaded)
            Archives chapters into respective volumes.
        to_cbz(dir_to_zip, destination)
            Creates a .cbz archive for a folder.
    """

    def __init__(self, manga_title: str):
        self.manga_title = manga_title
        self.base_path = os.path.join(ROOT_DIR, self.manga_title)
        self.raw_path = os.path.join(self.base_path, 'raw')

    def setup_folders(self):
        safe_mkdir(self.base_path)
        safe_mkdir(self.raw_path)

    def create_volumes(self, downloaded: List[Chapter]) -> None:
        """
        Archives chapters into respective volumes.

        Creates a new folder inside `self.base_path` and creates archives
        inside the new folder.

        Parameters
        ----------
        downloaded : array_like
            Chapter instances of downloaded chapters.

        Returns
        -------
        None
        """
        logger.info('(っ˘ڡ˘ς) preparing to compile into volumes...')

        # make a new folder to store compiled volumes
        vols_path = os.path.join(self.base_path, self.manga_title)
        safe_mkdir(vols_path)
        #
        # copy raw chapters
        for ch in tqdm(downloaded,
                       total=len(downloaded),
                       desc=f'Copying files',
                       bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}',
                       ncols=80,
                       leave=False):
            if ch.ch_num == '_':
                # has no volume number
                new_ch_path = os.path.join(vols_path, ch.ch_title)
            else:
                new_ch_path = os.path.join(
                    vols_path, f'{self.manga_title}, Vol. {ch.vol_num}', f'{ch.ch_num}')
            copy_tree(ch.ch_path, new_ch_path)
            tqdm.write(f'copied {ch.ch_path} -> {new_ch_path}')

        for raw_vol in tqdm(os.scandir(vols_path),
                            total=len(os.listdir(vols_path)),
                            desc=f'Archiving into volumes',
                            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}',
                            ncols=80,
                            leave=False):

            self.to_cbz(raw_vol.path, vols_path)
            #
            # delete the non-archived folder
            shutil.rmtree(raw_vol.path)

    @ staticmethod
    def to_cbz(dir_to_zip: Path, destination: Path) -> None:
        """
        Creates .cbz file.

        Parameters
        ----------
        dir_to_zip : str
            Absolute path to folder which we want to zip.
        destination : str
            Where to store the new archive.

        Returns
        -------
        None
        """
        os.chdir(dir_to_zip)
        archive_name = os.path.split(dir_to_zip)[-1]
        archive_path = os.path.join(destination, archive_name)
        shutil.make_archive(base_name=archive_path, format='zip')
        tqdm.write(f'created .zip archive -> {archive_path}')

        new_volume_path = os.path.join(destination, f'{archive_name}.zip')
        base_name = os.path.splitext(new_volume_path)[0]
        final_name = base_name + '.cbz'
        os.rename(new_volume_path, final_name)

        tqdm.write(f'renamed {new_volume_path} -> {final_name}')
        tqdm.write(f'>>>>>>( ^_^）o自  {archive_name} compiled  自o（^_^ )<<<<<<')
