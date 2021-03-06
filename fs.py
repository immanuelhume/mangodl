# TODO make directories - raw - volumized
import os
import shutil
from helpers import safe_mkdir
from distutils.dir_util import copy_tree
from manga import Manga
from constants import api_base


class Fs:
    """Fs objects handle file system related tasks when downloading
    manga. Init with root directory and Manga object.

    Main attributes:
        base_path (str) : Absolute path to directory where the current
                          manga is to be downloaded.
        raw_path (str)  : A folder within `base_path` which holds the raw
                          image files of each chapter.

    Methods:
        to_cbz          : Creates a .cbz archive for a folder.
        create_volumes  : Archives chapters into respective volumes.
    """

    def __init__(self, root_dir: str, manga: Manga):
        self.manga = manga
        self.base_path = os.path.join(root_dir, manga.title)
        safe_mkdir(self.base_path)
        # make directory for raw images
        self.raw_path = os.path.join(self.base_path, 'raw')
        safe_mkdir(self.raw_path)

    @classmethod
    def to_cbz(cls, dir_to_zip: str, destination: str) -> None:
        """Creates .cbz file for folder at <dir_to_zip>.

        Arguments:
            dir_to_zip (str)  : Absolute path to folder to zip.
            destination (str) : Directory to store the new .cbz file. 
                                This must already exist.
        """
        os.chdir(dir_to_zip)
        archive_name = os.path.split(dir_to_zip)[-1]
        archive_path = os.path.join(destination, archive_name)
        shutil.make_archive(base_name=archive_path, format='zip')

        new_volume_path = os.path.join(destination, f'{archive_name}.zip')
        base_name = os.path.splitext(new_volume_path)[0]
        os.rename(new_volume_path, base_name + '.cbz')

        print(f'{archive_name} compiled!')

    def create_volumes(self) -> None:
        """Archives chapters into respective volumes.

        Creates a new folder `volumes_path` at `base_path`. Volume folders 
        are created inside `volumes_path`. Once zipped, the unzipped folder
        is removed.
        """
        print('Preparing to compile into volumes...')

        volumes_path = os.path.join(self.base_path, self.manga.title)
        safe_mkdir(volumes_path)

        for chapter in os.scandir(self.raw_path):
            volume_num = self.manga.chap_to_vol[float(chapter.name)]
            new_chapter_path = os.path.join(
                volumes_path, f'{volume_num}', chapter.name)
            copy_tree(chapter.path, new_chapter_path)

        for volume in os.scandir(volumes_path):
            old_name = volume.path
            new_name = os.path.join(os.path.split(volume.path)[
                                    0], f'{self.manga.title} Vol. {volume.name}')
            os.rename(old_name, new_name)

            self.to_cbz(os.path.join(volumes_path,
                                     new_name), volumes_path)

            shutil.rmtree(new_name)


if __name__ == '__main__':
    pass
