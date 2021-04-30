from functools import total_ordering


@total_ordering
class FileRegion:
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

    @property
    def end(self):
        return self._end

    def truncate_end(self, value: int) -> None:
        if value < 0:
            raise ValueError

        self.__original_end -= value
        self._end -= value

    @property
    def original_start(self) -> int:
        return self.__original_start

    @property
    def original_end(self) -> int:
        return self.__original_end

    def split(self, pos: int) -> tuple:
        """Разбивает текущий регион на два по позиции pos так, что конец левого
        региона в pos - 1, начало правого в pos, индекс левого равен индексу
        исходного региона, индекс правого на единицу больше индекса левого"""
        left = FileRegion(self.start, pos - 1, self.index)
        left.__set_original_bounds(self.__original_start,
                                   self.__original_end - (self._end - pos) - 1)
        right = FileRegion(pos, self.end, self.index + 1)
        right.__set_original_bounds(self.__original_end - (self._end - pos),
                                    self.__original_end)

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

    def truncate_start(self, value: int) -> None:
        if value < self._start:
            raise ValueError

        self.data = self.data[value:]
        self._start += value

    def truncate_end(self, value: int) -> None:
        if value > self._start:
            raise ValueError

        self.data = self.data[:len(self.data) - value]
        self._end -= value

    def split(self, pos: int) -> tuple:
        return EditedFileRegion(self.start,
                                self.data[:pos - self.start],
                                self.index), \
               EditedFileRegion(pos,
                                self.data[pos - self.start:],
                                self.index + 1)

    def get_nbytes(self, offset: int, count: int) -> bytes:
        return self.data[offset:offset + count]

    def __repr__(self):
        return f'EditedFileRegion({self.start}, {self.end}, {self.data})'
