import struct
from typing import List

from fat.constants import FileAttributes
from fat.exceptions import FATException
from fat.utils import split_by_chunks


class DirectoryTable:

    def __init__(self, cluster_number: int, data: bytes):
        self.cluster_number = cluster_number       # type: int
        self.entries = []                          # type: List[DirectoryEntry]

        self.parse(data)

    def add_entry(self, filename: str, extension: str, first_file_cluster: int, **kwargs):
        self.entries.append(
            DirectoryEntry(filename=filename, extension=extension, first_file_cluster=first_file_cluster, **kwargs)
        )

    def find_entry(self, filename: str, extension: str) -> 'DirectoryEntry' or None:
        found_entry = None
        for entry in self.entries:
            if entry.filename == filename and entry.extension == extension:
                found_entry = entry
                break
        return found_entry

    def parse(self, data: bytes):
        self.entries.clear()
        for entry_bytes in split_by_chunks(data, DirectoryEntry.SIZE):
            entry = DirectoryEntry()
            entry.parse(entry_bytes)
            self.entries.append(entry)

    def serialize(self) -> bytes:
        return b''.join(entry.serialize() for entry in self.entries)

    def __repr__(self):
        return f"<DirectoryTable: {self.cluster_number}>"


class DirectoryEntry:

    FORMAT = '<8s3sBHH'
    SIZE = 32

    def __init__(self, **kwargs):
        self.filename = kwargs.get('filename', None)                            # type: str
        self.extension = kwargs.get('extension', None)                          # type: str
        self.attributes = kwargs.get('attributes', FileAttributes.DEFAULT)      # type: int
        self.first_file_cluster = kwargs.get('first_file_cluster', None)        # type: int
        self.file_size = None                                                   # type: int
        self.last_modified_time = None                                          # type: int
        self.last_modified_date = None                                          # type: int

        self._validation()

    def _validation(self):
        if self.filename and len(self.filename) > 8:
            raise FATException(f'Validation error: filename is too long: {len(self.filename)}')
        if self.extension and len(self.extension) > 3:
            raise FATException(f'Validation error: extension is too long: {len(self.extension)}')
        if self.is_dir() and self.extension:
            raise FATException('Validation error: directory has to have not specified extension')

    @property
    def fullname(self):
        fullname = self.filename
        if self.extension:
            fullname += f'.{self.extension}'
        return fullname

    def is_dir(self) -> bool:
        """Returns True if the entry has the directory attribute, False otherwise
        """
        return bool(self.attributes & FileAttributes.DIRECTORY)

    def parse(self, data: bytes):
        # if len(data) != self.SIZE: TODO: ?
        if len(data) > self.SIZE:
            raise FATException(f'data has to have length={self.SIZE}')
        data = data[:16]  # FIXME: remove it. It's here while we don't save all entry fields

        (self.filename,
         self.extension,
         self.attributes,
         high_first_cluster,
         low_first_cluster) = struct.unpack(self.FORMAT, data)

        self.filename = self.filename.rstrip(b'\x00').decode()
        self.extension = self.extension.rstrip(b'\x00').decode()
        self.first_file_cluster = (high_first_cluster << 16) | low_first_cluster

    def serialize(self) -> bytes:
        # TODO: first_file_cluster has to be serialized like this:
        # - save low high 2 bytes of first cluster at 0x14 offset
        # - save low two 2 bytes of first cluster at 0x1A offset
        # more info at https://en.wikipedia.org/wiki/Design_of_the_FAT_file_system#Directory_entry

        high_first_cluster, low_first_cluster = divmod(self.first_file_cluster, 2**16)
        return struct.pack(
            self.FORMAT,
            self.filename.encode(),
            self.extension.encode(),
            self.attributes,
            high_first_cluster,
            low_first_cluster,
        )
