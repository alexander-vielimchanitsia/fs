
DATA_PATH = './fat/data'
VOLUME_FILENAME = 'volume'

SECTOR_SIZE = 0x200  # bytes
TOTAL_SECTORS = 65536
SECTORS_PER_CLUSTER = 32  # sectors

FAT_ENTRY_EMPTY = 0x00000000

FAT_ENTRY_CLUSTER_MIN = 0x00000002
FAT_ENTRY_CLUSTER_MAX = 0x0FFFFFEF
FAT_ENTRY_EOF = (0x0FFFFFF8, 0x0FFFFFFF)

# entry 0 holds the FAT ID
# entry 1 stores the end-of-cluster-chain marker
# entry 2 stores the root directory
FAT_CLUSTER_TO_USE_FROM = 0x00000003

EOF = object()
EOC = 0x0FFFFFFF  # end of cluster-chain

FAT_REGION_NUM = 0x00000001
ROOT_FILE_NUM = 0x00000002


class FATType:
    FAT12 = 'fat12'
    FAT16 = 'fat16'
    FAT32 = 'fat32'


class FileAttributes:
    """File Attributes for directory entries
    Length: 1 byte
    """
    DEFAULT = 0x0
    READ_ONLY = 0x01
    HIDDEN = 0x02
    SYSTEM = 0x04
    VOLUME_LABEL = 0x08
    DIRECTORY = 0x10
    ARCHIVE = 0x20
