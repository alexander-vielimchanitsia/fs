
class FATException(Exception):
    pass


class InvalidClusterError(FATException):
    pass


class EmptyClusterError(FATException):
    pass


class FileNotExistsError(FATException):
    pass


class DirNotExistsError(FileNotExistsError):
    pass
