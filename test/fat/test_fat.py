"""Main tests for File Allocation Table
"""

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pathlib import PosixPath

from fat import constants as const
from fat.core import FAT


@pytest.fixture(scope='function', autouse=True)
def global_mocks(monkeypatch: MonkeyPatch, tmp_path: PosixPath):
    """Gathers all mocks that should be applied to all tests in the file
    """
    monkeypatch.setattr(const, 'DATA_PATH', tmp_path.as_posix())


class TestFAT:
    """Main tests for File Allocation Table:
    - create/save FAT
    - file API
    """

    fat: FAT

    def setup_method(self):
        """Common initialization for every test
        """
        self.fat = FAT()

    def test_root_init(self):
        """Test the root directory initialization
        """
        assert self.fat.root.cluster_number == const.ROOT_FILE_NUM
        assert len(self.fat.root.entries) == 0
        assert self.fat.entries[const.ROOT_FILE_NUM] == const.EOC

    def test_create_file(self):
        """Test creating a new file in the root
        """
        assert len(self.fat.root.entries) == 0

        file_number = self.fat.create_file('/test.txt')
        assert len(self.fat.root.entries) == 1
        assert self.fat.entries[file_number] == const.EOC

        dir_entry = self.fat.root.entries[0]
        assert dir_entry.filename == 'test'
        assert dir_entry.extension == 'txt'

        # check the saved dir entry in the cluster
        with open(self.fat.volume_path, 'rb') as volume:
            volume.seek(self.fat.get_cluster_position(self.fat.root.cluster_number))
            saved_entry = volume.read(dir_entry.SIZE)
        assert saved_entry == b'test\x00\x00\x00\x00txt\x00\x00\x00\x03\x00'

    def test_write_file(self):
        """Test write data to a new created file
        """
        assert len(self.fat.root.entries) == 0
        # write data
        file_number = self.fat.create_file('/test.txt')
        data = b'some dummy data for the test'
        self.fat.write_file(file_number, data)
        # check the saved data
        with open(self.fat.volume_path, 'rb') as volume:
            volume.seek(self.fat.get_cluster_position(file_number))
            file_cluster = volume.read(self.fat.cluster_size)
        assert file_cluster == data

    def test_create_dir(self):
        """Test creating a new dir in the root
        """
        assert len(self.fat.root.entries) == 0

        file_number = self.fat.create_file('/data', is_dir=True)
        assert len(self.fat.root.entries) == 1
        assert self.fat.entries[file_number] == const.EOC

        dir_entry = self.fat.root.entries[0]
        assert dir_entry.filename == 'data'
        assert dir_entry.extension == ''
        assert dir_entry.is_dir()

        # check the saved dir entry in the cluster
        with open(self.fat.volume_path, 'rb') as volume:
            volume.seek(self.fat.get_cluster_position(self.fat.root.cluster_number))
            saved_entry = volume.read(dir_entry.SIZE)
        assert saved_entry == b'data\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x03\x00'

    def test_find_dir(self):
        """Test finding a directory by its path
        """
        assert len(self.fat.root.entries) == 0

        self.fat.create_file('/data', is_dir=True)
        dir_path = '/data/some'
        directory = self.fat.create_file(dir_path, is_dir=True)

        found_dir = self.fat.find_dir(dir_path)
        assert found_dir.cluster_number == directory

    def test_find_file(self):
        """Test finding a file by its path
        """
        assert len(self.fat.root.entries) == 0

        # create dirs for the test file
        self.fat.create_file('/data', is_dir=True)
        self.fat.create_file('/data/some', is_dir=True)
        # create the file itself
        file_path = '/data/some/text.txt'
        file_number = self.fat.create_file(file_path)

        found_file = self.fat.find_file(file_path)
        assert found_file == file_number
