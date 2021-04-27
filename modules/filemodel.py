import bisect
from functools import total_ordering


@total_ordering
class FileRegion:
    def __init__(self, start: int, end: int, index: int):
        self.start = start
        self.end = end
        self.index = index

    def split(self, pos: int, offset: int = 0) -> tuple:
        """Разбивает текущий регион на два по позиции pos так, что конец левого
        региона в pos - 1, начало правого в pos, индекс левого равен индексу
        исходного региона, индекс правого на единицу больше индекса левого.
        Добавляет к началу правого региона offset, если он передан."""
        return FileRegion(self.start, pos - 1, self.index),\
            FileRegion(pos + offset, self.end, self.index + 1)

    @property
    def length(self) -> int:
        return self.end - self.start + 1

    def __eq__(self, other):
        if isinstance(other, int):
            return self.start <= other <= self.end
        if isinstance(other, FileRegion):
            return self.start == other.start and self.end == other.end

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
        """Заменяет байты со смещения offset на data"""
        # TODO: должна быть оптимизация, когда изменяются смежные байты

        # находим первый и последний регионы, что были задействованы
        first_region = last_region = self.search_region(offset)
        total_bytes = last_region.length
        while total_bytes < len(data):
            last_region = self.file_regions[last_region.index + 1]
            total_bytes += last_region.length

        if offset == first_region.start:
            new_region_index = first_region.index
        else:
            new_region_index = first_region.index + 1
        new_region = EditedFileRegion(offset, data, new_region_index)

        # удаляем регионы, что были перезаписаны
        to_delete = first_region.index
        while (new_region.start <= self.file_regions[to_delete].start
               and new_region.end >= self.file_regions[to_delete].end):
            self.file_regions.pop(to_delete)

        # исправляем границы регионов
        if (first_region == last_region
                and new_region.start == first_region.start):
            # замена была с начала региона
            last_region.start = new_region.end + 1
        elif first_region == last_region and new_region.end == last_region.end:
            # замена была до конца региона
            first_region.end = new_region.start - 1
        elif first_region == last_region:
            # замена была в середине региона
            head, tail = first_region.split(offset, new_region.length)
            self.file_regions.insert(tail.index, tail)
            first_region.end = head.end
        else:
            # замена была больше, чем в одном регионе
            first_region.end = new_region.start - 1
            last_region.start = new_region.end + 1

        self.file_regions.insert(new_region.index, new_region)

        # исправляем индексы
        for i in range(new_region.index + 1, len(self.file_regions)):
            self.file_regions[i].index = i

    def insert(self, offset: int, data: list) -> None:
        """Вставляет data по смещению offset"""
        previous = self.search_region(offset)

        if offset == previous.start:
            # вставка будет перед предыдущим регионом
            new_region_index = previous.index
            new_region_start = previous.start
        else:
            # вставка будет в середине предыдущего региона
            new_region_index = previous.index + 1
            new_region_start = offset
            head, tail = previous.split(offset)
            previous.end = head.end
            self.file_regions.insert(tail.index, tail)
        new_region = EditedFileRegion(new_region_start,
                                      data,
                                      new_region_index)

        self.file_regions.insert(new_region.index, new_region)

        # исправляем границы и индексы
        for i in range(new_region.index + 1, len(self.file_regions)):
            self.file_regions[i].start += new_region.length
            self.file_regions[i].end += new_region.length
            self.file_regions[i].index = i

# TODO
# 1. linked list?
