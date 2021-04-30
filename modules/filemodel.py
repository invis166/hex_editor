import bisect
from modules.fileregion import FileRegion, EditedFileRegion


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
        # TODO: оптимизация, когда изменяются смежные байты
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
            left.truncate_start(new_region.end - left.start + 1)
        elif left == right and new_region.end == right.end:
            # изменения до конца региона
            left.truncate_end(left.end - new_region.start + 1)
        elif left == right:
            # изменения в середине региона
            head, tail = left.split(new_region.start, new_region.length)
            self.file_regions.insert(tail.index, tail)
            left.truncate_end(left.end - head.start - 1)
        else:
            # изменения больше, чем в одном регионе
            left.truncate_end(left.end - new_region.start + 1)
            right.truncate_start(new_region.end - right.start + 1)

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
            previous.truncate_end(tail.length)
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
            left.truncate_start(count)
        elif left == right and remove_end == right.end:
            # изменения до конца региона
            left.truncate_end(count)
        elif left == right:
            # изменения в середине региона
            head, tail = left.split(offset, count)
            self.file_regions.insert(tail.index, tail)
            left.truncate_end(left.end - head.start)
        else:
            # изменения больше, чем в одном регионе
            left.truncate_end(left.end - offset + 1)
            right.truncate_start(offset + count - right.start)

        # исправляем границы и индексы
        if is_left_removed or is_left_truncated:
            start_from = left.index
        else:
            start_from = left.index + 1
        for i in range(start_from, len(self.file_regions)):
            self.file_regions[i].move(-count)
            self.file_regions[i].index = i

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


# TODO
# 1. linked list?
