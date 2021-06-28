import os.path
from modules.buffer import DataBuffer
from modules.filemodel import FileModel, FileRegion, EditedFileRegion


class HexEditor:
    def __init__(self, filename: str, is_readonly=False):
        self.filename = filename
        if is_readonly:
            self._fp = open(filename, 'rb')
        else:
            self._fp = open(filename, 'r+b')
        self._model = FileModel(os.path.getsize(filename))
        self._buffer = DataBuffer(self._model, self._fp)

        self.__chunk_size = 1024

    def get_nbytes(self, offset: int, count: int) -> bytes:
        return bytes(self._buffer.read_nbytes(offset, count))

    def replace(self, offset: int, data: bytes) -> None:
        self._model.replace(offset, data)

    def insert(self, offset: int, data: bytes) -> None:
        self._model.insert(offset, data)

    def remove(self, offset: int, count: int) -> None:
        self._model.remove(offset, count)

    def save_changes(self, filename: str):
        if filename != self.filename:
            # сохраняем в другой файл
            fp = open(filename, 'wb')
        else:
            fp = self._fp
        for region in self._model.file_regions:
            if isinstance(region, EditedFileRegion):
                fp.seek(region.start)
                fp.write(region.data)
            elif (region.original_start != region.start
                  or region.original_end != region.end):
                previous = region.start
                for i in range(region.length // self.__chunk_size):
                    data = self.get_nbytes(previous, self.__chunk_size)
                    fp.seek(previous)
                    fp.write(data)
                    previous += self.__chunk_size
                fp.write(self.get_nbytes(previous, region.length % self.__chunk_size))
        fp.flush()
        fp.truncate(self.file_size)

        if filename != self.filename:
            fp.close()
        else:
            self._model = FileModel(self._model.file_size)
            self._buffer._file_model = self._model

    def search(self, query: bytes) -> int:
        """Поиск подстроки в строке через полиномиальный хэш"""
        # нет проверки на длину входных данных
        p = 1000
        max_power = p ** (len(query) - 1)
        query_hash = 0
        substring_hash = 0
        for i in range(len(query)):
            query_hash = query_hash * p + query[i]
            substring_hash = substring_hash * p + self.get_nbytes(i, 1)[0]

        for i in range(len(query), self.file_size + 1):
            if query_hash == substring_hash:
                if query == self.get_nbytes(i - len(query), len(query)):
                    return i - len(query)
            if i == self.file_size:
                return -1
            substring_hash -= max_power * self.get_nbytes(i - len(query), 1)[0]
            substring_hash = substring_hash * p + self.get_nbytes(i, 1)[0]

        return -1

    def exit(self):
        self._fp.close()

    @property
    def file_size(self) -> int:
        return self._model.file_size

    def __del__(self):
        self.exit()


if __name__ == '__main__':
    pass
