import bisect
from functools import total_ordering


@total_ordering
class FileRegion:
    def __init__(self, start, end, index):
        self.start = start
        self.end = end
        self.index = index

    @property
    def length(self):
        return self.end - self.start + 1

    def __eq__(self, other):
        if isinstance(other, int):
            return self.start <= other <= self.end

    def __gt__(self, other):
        if isinstance(other, int):
            return self.start > other

    def __lt__(self, other):
        if isinstance(other, int):
            return self.end < other

    def __repr__(self):
        return f'FileRegion({self.start}, {self.end})'


class EditedFileRegion(FileRegion):
    def __init__(self, start, data, index):
        super().__init__(start, len(data) + start - 1, index)
        self.data = data

    def get_nbytes(self, offset, count):
        return self.data[offset:offset + count]

    def __repr__(self):
        return f'EditedFileRegion({self.start}, {self.end}, {self.data})'


class FileModel:
    def __init__(self, file_size: int):
        self.size: int = file_size
        self.file_regions = [FileRegion(0, self.size - 1, 0)]

    def search_region(self, offset: int) -> FileRegion:
        """Возвращает FileRegion, который находится по смещению offset"""
        return self.file_regions[bisect.bisect_left(self.file_regions, offset)]


# TODO
# 1. linked list?
