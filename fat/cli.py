from fat.core import FAT


def mkdir(path_name: str):
    fat = FAT()
    fat.create_file(path_name, is_dir=True)
    fat.save()


def rmdir(path_name: str):
    pass


def touch(path_name: str):
    fat = FAT()
    fat.create_file(path_name)
    fat.save()


def write(path_name: str, data: str):
    fat = FAT()
    file_number = fat.find_file(path_name)
    fat.write_file(file_number, data.encode())
    fat.save()


def read(path_name: str):
    fat = FAT()
    file_number = fat.find_file(path_name)
    print(fat.read_file(file_number).decode())
