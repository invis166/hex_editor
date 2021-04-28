import bisect
from functools import total_ordering


@total_ordering
class FileRegion:
    def __init__(self, start: int, end: int, index: int):
        self.start = start
        self.end = end
        self.index = index

        # при вставке приходится сдвигать регионы, из за чего пропадает
        # взаимно однозначное соответствие между регионом и его местом в файле
        self.__original_start = self.start
        self.__original_end = self.end

    def move(self, count: int) -> None:
        self.start += count
        self.end += count

    @property
    def original_start(self) -> int:
        return self.__original_start

    @property
    def original_end(self) -> int:
        return self.__original_end

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
    def __init__(self, start: int, data: bytes, index: int):
        # super().__init__(start, len(data) + start - 1, index)
        self.index = index
        self.__start = start
        self.__end = max(len(data) + start - 1, 0)
        self.data = data

    @property
    def start(self):
        return self.__start

    @start.setter
    def start(self, value: int):
        if value < self.__start:
            raise ValueError

        self.data = self.data[value - self.__start:]
        self.__start = value

    @property
    def end(self):
        return self.__end

    @end.setter
    def end(self, value: int):
        if value > self.__end:
            raise ValueError

        self.data = self.data[:-(self.__end - value)]
        self.__end = value

    def split(self, pos: int, offset: int = 0) -> tuple:
        return EditedFileRegion(self.start,
                                self.data[:pos - self.start],
                                self.index),\
               EditedFileRegion(pos + offset,
                                self.data[pos - self.start:],
                                self.index + 1)

    def move(self, count: int) -> None:
        self.__start += count
        self.__end += count

    def get_nbytes(self, offset: int, count: int) -> bytes:
        return self.data[offset:offset + count]

    def __repr__(self):
        return f'EditedFileRegion({self.start}, {self.end}, {self.data})'


class FileModel:
    def __init__(self, file_size: int):
        self.file_regions = [FileRegion(0, file_size - 1, 0)]

    @property
    def file_size(self) -> int:
        return self.file_regions[-1].end + 1

    def search_region(self, offset: int) -> FileRegion:
        """Возвращает FileRegion, который соответствует смещению offset"""
        return self.file_regions[bisect.bisect_left(self.file_regions, offset)]

    def replace(self, offset: int, data: bytes) -> int:
        """Заменяет байты со смещения offset на data"""
        # TODO: должна быть оптимизация, когда изменяются смежные байты

        # находим первый и последний регионы, что были задействованы, попутно
        # удаляя перезаписанные
        first_region = self.search_region(offset)
        to_delete = first_region.index
        while to_delete < len(self.file_regions) and offset + len(data) - 1 >= self.file_regions[to_delete].end:
            if offset <= self.file_regions[to_delete].start:
                self.file_regions.pop(to_delete)
            else:
                to_delete += 1

        if not self.file_regions:
            # граничный случай, если перезаписали весь файл
            self.file_regions = [EditedFileRegion(0, b'', 0)]
            return 0
        last_region = self.file_regions[to_delete]

        if offset == first_region.start:
            new_region_index = first_region.index
        else:
            new_region_index = first_region.index + 1
        new_region = EditedFileRegion(offset, data, new_region_index)

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

        return new_region.index

    def insert(self, offset: int, data: bytes) -> int:
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
            self.file_regions[i].move(new_region.length)
            self.file_regions[i].index = i

        return new_region.index

# TODO
# 1. linked list?
