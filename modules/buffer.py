from fileregion import FileRegion


class DataBuffer:
    def __init__(self, regions):
        self._buffer_max_length = 16 * 16 * 4
        self._buffer: bytes
        self._regions = regions
        self._current_regions = []

        self.offset: int

    def read_nbytes(self, count: int, offset: int = None):
        if offset:
            self._current_regions = self._search_regions(count, offset)

    def _search_regions(self, count: int, offset: int):
        result = -1

        left = 0
        right = len(self._regions) - 1

        while left <= right:
            middle = (left + right) // 2

            if self._regions[middle] == offset:
                result = middle
                break
            elif self._regions[middle] > offset:
                right = middle - 1
            elif self._regions[middle] < offset:
                left = middle + 1

        regions = []
        if result != -1:
            # находим все нужные участки
            while self._regions[result] <= offset + count:
                print('here')
                regions.append(self._regions[result])
                result += 1

        return regions


if __name__ == '__main__':
    def convert(regions):
        result = []
        for region in regions:
            result.append(FileRegion(region[0], region[1]))

        return result


    regions = [(1, 5), (6, 10), (11, 20), (21, 50)]
    buffer = DataBuffer(convert(regions))
    print(buffer._search_regions(15, 3))
'''
Буффер должен взаимодействовать с FileModel, а не напрямую с файлом, чтобы
быть в курсеи зменений.
'''
