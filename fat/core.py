"""
File Allocation Table

https://en.wikipedia.org/wiki/Design_of_the_FAT_file_system
https://www.pjrc.com/tech/8051/ide/fat32.html

TODO:
- use BPB
- add cache
- add FS Information Sector
"""

import os
import struct
from typing import List

from fat import constants as const
from fat.dir import DirectoryTable
from fat.exceptions import FATException
from fat.utils import split_by_chunks


class FAT:
    """File Allocation Table
    """

    def __init__(self):
        self.cluster_size = None                                                                  # type: int
        self.max_clusters = None                                                                  # type: int
        self.entries = None                                                                       # type: List[int]
        self.volume_path = os.path.join(os.path.abspath(const.DATA_PATH), const.VOLUME_FILENAME)  # type: str
        self.type = const.FATType.FAT32

        self.root = None                                                                          # type: DirectoryTable

        self.load()

    def __create_new(self):
        self.cluster_size = const.SECTORS_PER_CLUSTER * const.SECTOR_SIZE
        self.max_clusters = int(const.TOTAL_SECTORS / const.SECTORS_PER_CLUSTER)
        self.entries = [0x0] * self.max_clusters

        # create an empty volume
        open(self.volume_path, 'a').close()

        # init root dir
        self.root = DirectoryTable(const.ROOT_FILE_NUM, b'')
        self.entries[const.ROOT_FILE_NUM] = const.EOC

    def is_cluster_number(self, number: int):
        """Check whether a number it's a valid cluster number
        """
        return const.FAT_ENTRY_CLUSTER_MIN <= number < self.max_clusters

    def get_cluster_position(self, number: int):
        """Get offset of a cluster in the volume by its entry number
        """
        if not self.is_cluster_number(number):
            raise FATException('Incorrect cluster position')
        return self.cluster_size * number

    def find_free_cluster(self, start_index: int=const.FAT_CLUSTER_TO_USE_FROM) -> int or const.EOF:
        """Try to find a free cluster, returns EOF if no any
        """
        if not self.is_cluster_number(start_index):
            raise FATException('Incorrect cluster position')

        for index, entry in enumerate(self.entries[start_index:], start=start_index):
            if entry == const.FAT_ENTRY_EMPTY:
                return index
        return const.EOF

    def find_dir(self, path: str) -> DirectoryTable or None:
        if not path.startswith('/'):
            raise FATException('path has to be absolute.')

        if len(path.strip()) == 1:
            return self.root

        _, *dirs = path.split('/')
        current_dir = self.root
        for directory in dirs:
            for dir_entry in current_dir.entries:
                if dir_entry.is_dir() and dir_entry.filename == directory:
                    current_dir = self.read_dir(dir_entry.first_file_cluster)
                    break
            # directory doesn't have the next subdirectory in the path
            else:
                return None

        return current_dir

    def find_file(self, path: str) -> int:
        dirname, fullname = os.path.split(path)
        file_dir = self.find_dir(dirname)
        if file_dir is None:
            raise FATException(f'{path} directory does not exist')

        filename, extension = os.path.splitext(fullname)
        extension = extension.lstrip('.')

        file_dir_entry = file_dir.find_entry(filename, extension)
        if not file_dir_entry:
            raise FATException(f'{path} file does not exist')

        if file_dir_entry.is_dir():
            raise FATException(f'{path} is a directory. Use `find_dir` instead.')

        return file_dir_entry.first_file_cluster

    def read_file(self, file_number: int) -> bytearray:
        if not self.is_cluster_number(file_number):
            raise FATException(f'Incorrect file_number: {file_number}')

        file_content = bytearray()

        fat_number = file_number
        with open(self.volume_path, 'rb') as volume:
            while self.is_cluster_number(fat_number):
                fat_entry = self.entries[fat_number]
                if fat_entry == const.FAT_ENTRY_EMPTY:
                    raise FATException(f'Cluster is empty for the fat_number={fat_number}, file_number={file_number}')

                # read cluster data
                cluster_position = self.get_cluster_position(fat_number)
                volume.seek(cluster_position)
                cluster_value = volume.read(self.cluster_size)
                file_content.extend(cluster_value)

                # go to the next cluster in the chain
                fat_number = fat_entry

        return file_content

    def read_dir(self, entry_number: int) -> DirectoryTable:
        file_content = self.read_file(entry_number)
        directory = DirectoryTable(entry_number, file_content)
        return directory

    def create_file(self, path: str, is_dir=False) -> int:
        """Create a new file or directory
        """
        dirname, fullname = os.path.split(path)

        file_dir = self.find_dir(dirname)
        if file_dir is None:
            raise FATException(f'{path} directory does not exist')

        filename, extension = os.path.splitext(fullname)
        extension = extension.lstrip('.')

        # does the file already exist?
        if file_dir.find_entry(filename, extension):
            raise FATException(f'{path} file already exists')

        # find a free cluster for the new file
        file_cluster = self.find_free_cluster()
        if file_cluster == const.EOF:
            raise FATException('There is not free space')
        self.entries[file_cluster] = const.EOC

        # create file entry
        additional_entry_options = {}
        if is_dir:
            additional_entry_options['attributes'] = const.FileAttributes.DIRECTORY
        file_dir.add_entry(filename, extension, file_cluster, **additional_entry_options)
        self.write_file(file_dir.cluster_number, file_dir.serialize())

        return file_cluster

    def write_file(self, file_number: int, data: bytes):
        if not self.is_cluster_number(file_number):
            raise FATException(f'Incorrect file_number: {file_number}')

        # TODO: oprimize it for contiguous clusters (don't need to split by chunks)

        # rewrire all clusters
        fat_number = file_number
        prev_number = None
        with open(self.volume_path, 'r+b') as volume:
            for data_chunk in split_by_chunks(data, self.cluster_size):
                # there's no enough size in the file? -> add a new cluster to the file
                if fat_number == const.EOC:
                    fat_number = self.find_free_cluster(prev_number)
                    if fat_number == const.EOF:
                        fat_number = self.find_free_cluster()
                        if fat_number == const.EOF:
                            raise FATException('There is not free space')
                    self.entries[prev_number] = fat_number

                fat_entry = self.entries[fat_number]
                if fat_entry == const.FAT_ENTRY_EMPTY:
                    raise FATException(f'Cluster is empty for the fat_number={fat_number}, file_number={file_number}')

                # write data
                cluster_position = self.get_cluster_position(fat_number)
                volume.seek(cluster_position)
                volume.write(data_chunk)

                # go to the next cluster in the chain
                prev_number = fat_number
                fat_number = fat_entry

        # free not used clusters
        # TODO
        pass

    def load(self):
        if not os.path.isfile(self.volume_path):
            return self.__create_new()

        # TODO: remove it (get from BPB instead)
        self.cluster_size = const.SECTORS_PER_CLUSTER * const.SECTOR_SIZE
        self.max_clusters = int(const.TOTAL_SECTORS / const.SECTORS_PER_CLUSTER)

        # self.volume.seek(0)
        # self.bpb = BPB(self.volume.read(const.SECTOR_SIZE))

        with open(self.volume_path, 'rb') as volume:
            volume.seek(self.cluster_size)  # go to cluster #1
            entries_data = volume.read(self.max_clusters*4)
        # 4 bytes - size of a fat entry
        self.entries = list(struct.unpack(f'<{len(entries_data)//4}I', entries_data))

        self.root = self.read_dir(const.ROOT_FILE_NUM)

    def save(self):
        # FAT region
        # TODO: use FAT#1 and FAT#2
        # FIXME: use real FAT algorithm
        serialized_entries = struct.pack(f'<{len(self.entries)}I', *self.entries)
        with open(self.volume_path, 'r+b') as volume:
            volume.seek(self.cluster_size)  # go to cluster #1
            volume.write(serialized_entries)

        # save root
        self.write_file(self.root.cluster_number, self.root.serialize())


class BPB:
    """BIOS Parameter Block
    """

    def __init__(self, data):
        self.bytes_per_sector = None     # type: int
        self.sectors_per_cluster = None  # type: int
        self.total_sectors = None        # type: int

        self.fat_numbers = 2  # not used yet

    def save(self):
        pass

    def load(self):
        pass
