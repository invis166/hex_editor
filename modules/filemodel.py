import bisect
from functools import total_ordering


@total_ordering
class FileRegion:
    # TODO: вместо сеттеров к start и end сделать методы truncate_start,
    # truncate_end
    def __init__(self, start: int, end: int, index: int):
        self._start = start
        self._end = end
        self.index = index

        # нужны, чтобы сохранить взаимно однозначное соответствие между
        # FileRegion и местом на диске
        self.__original_start = self.start
        self.__original_end = self.end

    def move(self, count: int) -> None:
        """Сдвигает обе границы FileRegion на count, не изменяя original_end
        и original_start"""
        self._start += count
        self._end += count

    @property
    def start(self):
        return self._start

    def truncate_start(self, value: int) -> None:
        if value < 0:
            raise ValueError

        self.__original_start += value
        self._start += value

    @start.setter
    def start(self, value):
        if value < self.start:
            raise ValueError

        self.__original_start += value - self._start
        self._start = value

    @property
    def end(self):
        return self._end

    def truncate_end(self, value: int) -> None:
        if value < 0:
            raise ValueError

        self.__original_end -= value
        self._end -= value

    @end.setter
    def end(self, value):
        if value > self._end:
            raise ValueError

        self.__original_end += value - self._end
        self._end = value

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
        # TODO: разбивка original_end и original_start (IMPORTANT!!!!)
        left = FileRegion(self.start, pos - 1, self.index)
        left.__set_original_bounds(self.__original_start,
                                   self.__original_end - (self._end - pos) - 1)
        right = FileRegion(pos, self.end, self.index + 1)
        right.__set_original_bounds(self.__original_end - (self._end - pos),
                                    self.__original_end)
        right.start += offset

        return left, right

    @property
    def length(self) -> int:
        return self.end - self.start + 1

    def __set_original_bounds(self, start, end):
        self.__original_end = end
        self.__original_start = start

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
        super().__init__(start, max(len(data) + start - 1, 0), index)
        self.data = data

    @FileRegion.start.setter
    def start(self, value: int):
        if value < self._start:
            raise ValueError

        self.data = self.data[value - self._start:]
        self._start = value

    @FileRegion.end.setter
    def end(self, value: int):
        if value > self._end:
            raise ValueError

        self.data = self.data[:-(self._end - value)]
        self._end = value

    def split(self, pos: int, offset: int = 0) -> tuple:
        return EditedFileRegion(self.start,
                                self.data[:pos - self.start],
                                self.index),\
               EditedFileRegion(pos + offset,
                                self.data[pos - self.start:],
                                self.index + 1)

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
        left, right = self._remove_intermediate_regions(offset,
                                                        offset + len(data) - 1)
        if not self.file_regions:
            # граничный случай, был заменен весь файл
            self.file_regions = [EditedFileRegion(0, data, 0)]
            return 0

        if offset == left.start:
            new_region_index = left.index
        else:
            new_region_index = left.index + 1
        new_region = EditedFileRegion(offset, data, new_region_index)

        # корректируем границы смежных с новым регионов
        if left == right and new_region.start == left.start:
            # изменения с начала региона
            left.start = new_region.end + 1
        elif left == right and new_region.end == right.end:
            # изменения до конца региона
            left.end = new_region.start - 1
        elif left == right:
            # изменения в середине региона
            head, tail = left.split(new_region.start, new_region.length)
            self.file_regions.insert(tail.index, tail)
            left.end = head.end
        else:
            # изменения больше, чем в одном регионе
            left.end = new_region.start - 1
            right.start = new_region.end + 1

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

    def _remove_intermediate_regions(self, start: int, end: int) -> tuple:
        """Удаляет регионы, целиком находящиеся в отрезке [start; end].
        Возвращает первый и последний регионы, что не были удалены.
        Если бы удален весь файл, возвращает None, None"""
        left = self.search_region(start)
        to_delete = left.index
        while (to_delete < len(self.file_regions)
               and end >= self.file_regions[to_delete].end):
            if start <= self.file_regions[to_delete].start:
                self.file_regions.pop(to_delete)
            else:
                to_delete += 1
        if not self.file_regions:
            return None, None

        return left, self.file_regions[to_delete]

    def remove(self, offset: int, count: int) -> None:
        remove_end = max(offset + count - 1, 0)
        left, right = self._remove_intermediate_regions(offset, remove_end)
        if not self.file_regions:
            # граничный случай, был удален весь файл
            self.file_regions = [EditedFileRegion(0, b'', 0)]
            return
        is_left_removed = offset <= left.start and left.end <= remove_end

        is_left_truncated = False
        # корректируем границы смежных с новым регионов
        if left == right and offset == left.start:
            # изменения с начала региона
            is_left_truncated = True
            left.start += count
        elif left == right and remove_end == right.end:
            # изменения до конца региона
            left.end -= count
        elif left == right:
            # изменения в середине региона
            head, tail = left.split(offset, count)
            self.file_regions.insert(tail.index, tail)
            left.end = head.end
        else:
            # изменения больше, чем в одном регионе
            left.end = offset - 1
            right.start = offset + count

        # исправляем границы и индексы
        if is_left_removed or is_left_truncated:
            start_from = left.index
        else:
            start_from = left.index + 1
        for i in range(start_from, len(self.file_regions)):
            self.file_regions[i].move(-count)
            self.file_regions[i].index = i


# TODO
# 1. linked list?
