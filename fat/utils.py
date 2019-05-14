from typing import Iterable


def split_by_chunks(data: Iterable, chunk_length: int):
    read = 0
    while read < len(data):
        chunk = data[read:read + chunk_length]
        read += chunk_length
        yield chunk
