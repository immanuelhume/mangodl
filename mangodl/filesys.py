"""Contains the FileSys class for file operations."""

import os
import shutil
from distutils.dir_util import copy_tree
from tqdm import tqdm
from typing import (Optional,
                    Union,
                    Dict,
                    List,
                    Tuple,
                    Iterator,
                    Awaitable,
                    Set)
from pathlib import Path

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
    base_path : Path
        Absolute path to base directory for this manga. This is inside the 
        root directory specified by the user and stored as the global `ROOT_DIR`.
    raw_path : Path
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
        self.base_path = Path(ROOT_DIR) / self.manga_title
        self.raw_path = self.base_path / 'raw'  # where we download the raw images

    def setup_folders(self) -> None:
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
        vols_path = self.base_path / self.manga_title
        safe_mkdir(vols_path)

        # copy raw chapters
        for ch in tqdm(downloaded,
                       total=len(downloaded),
                       desc=f'Copying files',
                       bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}',
                       ncols=80,
                       leave=False):
            if ch.ch_num == '_':
                # has no volume number
                new_ch_path = vols_path / ch.ch_title
            else:
                new_ch_path = vols_path / f'{self.manga_title}, Vol. {ch.vol_num}' / f'{ch.ch_num}'
            copy_tree(ch.ch_path, new_ch_path)
            tqdm.write(f'copied {ch.ch_path} -> {new_ch_path}')

        for raw_vol in tqdm(os.scandir(vols_path),
                            total=len(os.listdir(vols_path)),
                            desc=f'Archiving into volumes',
                            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}',
                            ncols=80,
                            leave=False):

            self.to_cbz(Path(raw_vol.path), vols_path)

            # delete the non-archived folder
            shutil.rmtree(raw_vol.path)

    @ staticmethod
    def to_cbz(dir_to_zip: Path, destination: Path) -> None:
        """
        Creates .cbz file. Both arguments must be pathlib.Path objects.

        Parameters
        ----------
        dir_to_zip : Path
            Absolute path to folder which we want to zip.
        destination : Path
            Where to store the new archive.

        Returns
        -------
        None
        """
        os.chdir(dir_to_zip)
        archive_name = dir_to_zip.stem
        archive_path = destination / archive_name
        new_vol_path = shutil.make_archive(base_name=archive_path, format='zip')
        new_vol_path = Path(new_vol_path)  # convert to pathlib.Path object
        tqdm.write(f'created archive {new_vol_path} <- {archive_name}')

        # change ext to .cbz
        with_cbz_ext = new_vol_path.with_suffix('.cbz')
        os.rename(new_vol_path, with_cbz_ext)

        tqdm.write(f'renamed {new_vol_path} -> {with_cbz_ext}')
        tqdm.write(f'>>>>>>( ^_^）o自  {archive_name} compiled  自o（^_^ )<<<<<<')
