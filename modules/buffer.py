from modules.filemodel import FileRegion, EditedFileRegion, FileModel


class DataBuffer:
    def __init__(self, file_model: FileModel, fp):
        self._buffer_max_length = 16 * 16 * 4
        self.buffer = []

        self._file_model = file_model
        self._initial_region: FileRegion = None
        self._current_region: FileRegion = None

        self._fp = fp

        self.offset: int = 0

    def read_nbytes(self, offset: int, count: int) -> list:
        """Возвращает count байт текущего состояния файла со смещения offset
        и записывает их в буффер"""
        # TODO
        # нужны какие-то оптимизации, чтобы не считывать все заново в буффер,
        # если это возможно
        self.buffer = []
        self.offset = offset
        self._initial_region = self._file_model.search_region(offset)
        self._current_region = self._initial_region

        read_total = 0
        while read_total < count:  # read_total есть len(buffer)
            to_read = min(self._current_region.length, count - read_total)
            start = max(0, offset - self._current_region.start)
            if isinstance(self._current_region, EditedFileRegion):
                # текущий регион был изменен и лежит в памяти
                self.buffer.extend(self._current_region.get_nbytes(start,
                                                                   to_read))
            else:
                # текущий регион лежит на диске
                self._fp.seek(self._current_region.original_start)
                self.buffer.extend(self._fp.read(to_read))
            read_total += to_read

            if self._current_region < offset + count:
                # идем к следующему региону
                self._current_region = \
                    self._file_model.file_regions[self._current_region.index + 1]

        return self.buffer

    @property
    def length(self):
        return len(self.buffer)

    def replace_byte(self):
        pass


if __name__ == '__main__':
    pass

