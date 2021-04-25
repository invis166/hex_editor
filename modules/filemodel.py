import bisect
from functools import total_ordering


@total_ordering
class FileRegion:
    def __init__(self, start: int, end: int, index: int):
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
    def __init__(self, start: int, data: list, index: int):
        super().__init__(start, len(data) + start - 1, index)
        self.data = data

    def get_nbytes(self, offset: int, count: int) -> list:
        return self.data[offset:offset + count]

    def __repr__(self):
        return f'EditedFileRegion({self.start}, {self.end}, {self.data})'


class FileModel:
    def __init__(self, file_size: int):
        self.size = file_size
        self.file_regions = [FileRegion(0, self.size - 1, 0)]

    def search_region(self, offset: int) -> FileRegion:
        """Возвращает FileRegion, который находится по смещению offset"""
        return self.file_regions[bisect.bisect_left(self.file_regions, offset)]

    def replace(self, offset: int, data: list) -> None:
        # должна быть оптимизация, когда изменяются смежные байты

        # находим первый и последний регионы
        first_region = last_region = self.search_region(offset)
        total_bytes = last_region.length
        while total_bytes < len(data):
            last_region = self.file_regions[last_region.index + 1]
            total_bytes += last_region.length

        # меняем хвосты
        new_region = EditedFileRegion(offset - 1, data, first_region.index + 1)
        first_region.end = new_region.start - 1
        last_region.start = new_region.end + 1

        # вставляем
        self.file_regions.insert(new_region.index, new_region)

        # переиндексируем
        map(lambda rg: rg.index + 1, self.file_regions[last_region.index:])








# TODO
# 1. linked list?
