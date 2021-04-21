import unittest

from modules.filemodel import FileRegion, FileModel


def _convert_tuples_to_regions(*regions):
    return [FileRegion(*region) for region in regions]


def _convert_regions_to_tuples(regions):
    return [(region.start, region.end) for region in regions]


class FileModelTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.model = FileModel(0)

    def test_search(self):
        self.model.file_regions = _convert_tuples_to_regions(
            (0, 5), (6, 10), (11, 17), (18, 30))

        self._test_search([(0, 5)], 1, 0)
        self._test_search([(0, 5)], 2, 0)
        self._test_search([(0, 5)], 3, 0)
        self._test_search([(0, 5)], 4, 0)
        self._test_search([(0, 5)], 5, 0)

        self._test_search([(11, 17)], 11, 0)
        self._test_search([(11, 17)], 12, 0)
        self._test_search([(11, 17)], 13, 0)
        self._test_search([(11, 17)], 14, 0)
        self._test_search([(11, 17)], 15, 0)

        self._test_search([(0, 5)], 0, 3)
        self._test_search([(0, 5)], 0, 4)
        self._test_search([(0, 5)], 0, 5)

        self._test_search([(0, 5), (6, 10)], 0, 6)
        self._test_search([(0, 5), (6, 10)], 4, 6)
        self._test_search([(6, 10), (11, 17), (18, 30)], 10, 20)
        self._test_search([(0, 5), (6, 10), (11, 17), (18, 30)], 0, 30)

    def _test_search(self, expected, offset, count):
        result = _convert_regions_to_tuples(
            self.model.search_regions(offset, count))
        self.assertSequenceEqual(expected, result)


class FileRegionTestCase(unittest.TestCase):
    def test_eq(self):
        self.assertTrue(FileRegion(1, 10) == 1)
        self.assertTrue(FileRegion(1, 10) == 5)
        self.assertTrue(FileRegion(1, 10) == 10)

        self.assertTrue(FileRegion(5, 10) != 4)
        self.assertTrue(FileRegion(5, 10) != 11)

    def test_gt(self):
        self.assertTrue(FileRegion(8, 10) > 7)

        self.assertFalse(FileRegion(8, 10) > 8)
        self.assertFalse(FileRegion(8, 10) > 9)
        self.assertFalse(FileRegion(8, 10) > 10)

    def test_lt(self):
        self.assertTrue(FileRegion(5, 10) < 11)

        self.assertFalse(FileRegion(5, 10) < 10)
        self.assertFalse(FileRegion(5, 10) < 5)
        self.assertFalse(FileRegion(5, 10) < 4)
        self.assertFalse(FileRegion(5, 10) < 7)


if __name__ == '__main__':
    unittest.main()

