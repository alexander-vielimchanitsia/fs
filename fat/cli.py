from fat.core import FAT


def mkdir(path_name: str):
    with FAT() as fat:
        fat.create_file(path_name, is_dir=True)


def rmdir(path_name: str):
    pass


def touch(path_name: str):
    with FAT() as fat:
        fat.create_file(path_name)


def write(path_name: str, data: str):
    with FAT() as fat:
        file_number = fat.find_file(path_name)
        fat.write_file(file_number, data.encode())


def read(path_name: str):
    fat = FAT()
    file_number = fat.find_file(path_name)
    print(fat.read_file(file_number).decode())
