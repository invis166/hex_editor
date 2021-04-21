import bisect
from functools import total_ordering


@total_ordering
class FileRegion:
    def __init__(self, start, end, index, is_inserted=False):
        self.start = start
        self.end = end
        self.index = index
        self.is_inserted = is_inserted

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


class FileModel:
    def __init__(self, file_size: int):
        self.size = file_size
        self.file_regions = [FileRegion(0, self.size - 1, 0)]

    def search_region(self, offset: int) -> FileRegion:
        return bisect.bisect_left(self.file_regions, offset)


# TODO
# 1. linked list?
