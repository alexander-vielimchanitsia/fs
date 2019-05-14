

class File:

    def __init__(self):
        self._pointer = 0

    @staticmethod
    def create(path_name: str):
        pass

    @staticmethod
    def open(path_name: str):
        return File()

    def close(self):
        pass

    def read(self):
        pass

    def write(self):
        pass

    def seek(self, value: int):
        self._pointer = value
