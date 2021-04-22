from modules.filemodel import FileRegion, EditedFileRegion, FileModel


class DataBuffer:
    def __init__(self, file_model: FileModel, fp):
        self._buffer_max_length = 16 * 16 * 4
        self.buffer = []

        self._file_model: FileModel = file_model
        self._initial_region: FileRegion = None
        self._current_region: FileRegion = None

        self._fp = fp

        self.offset: int = 0

    def read_nbytes(self, offset: int, count: int) -> list:
        # TODO
        # нужны какие-то оптимизации, чтобы не считывать все заново в буффер,
        # если это возможно
        self.buffer = []
        self.offset = offset
        self._initial_region = self._file_model.search_region(offset)
        self._current_region = self._initial_region

        read_total = 0
        start = offset
        while read_total < count:  # возможно, read_total есть len(buffer)
            end = min(offset + count, self._current_region.end)
            start = max(start, self._current_region.start)
            if isinstance(self._current_region, EditedFileRegion):
                # текущий регион был изменен и лежит в памяти
                self.buffer.append(
                    self._current_region.get_nbytes(end - start))
            else:
                # текущий регион лежит на диске
                self._fp.seek(start)
                self.buffer.append(self._fp.read(end - start))

            read_total += end - start

            if self._current_region < offset + count:
                self._current_region = \
                    self._file_model[self._current_region.index + 1]

        return self.buffer

    @property
    def length(self):
        return len(self.buffer)

    def replace_byte(self):
        pass


if __name__ == '__main__':
    pass

