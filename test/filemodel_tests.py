import unittest

from modules.filemodel import FileRegion, EditedFileRegion, FileModel


def convert_tuples_to_regions(*regions, is_edited=False):
    if is_edited:
        return [EditedFileRegion(region[0], list(range(region[1])), index)
                for index, region in enumerate(regions)]
    return [FileRegion(*region, index) for index, region in enumerate(regions)]


def convert_regions_to_tuples(regions):
    return [(region.start, region.end) for region in regions]


class FileModelTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.model = FileModel(0)

    def test_search(self):
        self.model.file_regions = convert_tuples_to_regions(
            (0, 5), (6, 10), (11, 17), (18, 30))

        self._test_search([(0, 5)], 1)
        self._test_search([(0, 5)], 2)
        self._test_search([(0, 5)], 3)
        self._test_search([(0, 5)], 4)
        self._test_search([(0, 5)], 5)

        self._test_search([(11, 17)], 11)
        self._test_search([(11, 17)], 12)
        self._test_search([(11, 17)], 13)
        self._test_search([(11, 17)], 14)
        self._test_search([(11, 17)], 15)

        self._test_search([(0, 5)], 0)
        self._test_search([(0, 5)], 0)
        self._test_search([(0, 5)], 0)

        self._test_search([(0, 5), (6, 10)], 0)
        self._test_search([(0, 5), (6, 10)], 4)
        self._test_search([(6, 10), (11, 17), (18, 30)], 10)
        self._test_search([(0, 5), (6, 10), (11, 17), (18, 30)], 0)

    def _test_search(self, expected, offset):
        result = convert_regions_to_tuples(
            self.model.search_region(offset))
        self.assertSequenceEqual(expected, result)


class FileRegionTestCase(unittest.TestCase):
    def test_eq(self):
        self.assertTrue(FileRegion(1, 10, 0) == 1)
        self.assertTrue(FileRegion(1, 10, 0) == 5)
        self.assertTrue(FileRegion(1, 10, 0) == 10)

        self.assertTrue(FileRegion(5, 10, 0) != 4)
        self.assertTrue(FileRegion(5, 10, 0) != 11)

    def test_gt(self):
        self.assertTrue(FileRegion(8, 10, 0) > 7)

        self.assertFalse(FileRegion(8, 10, 0) > 8)
        self.assertFalse(FileRegion(8, 10, 0) > 9)
        self.assertFalse(FileRegion(8, 10, 0) > 10)

    def test_lt(self):
        self.assertTrue(FileRegion(5, 10, 0) < 11)

        self.assertFalse(FileRegion(5, 10, 0) < 10)
        self.assertFalse(FileRegion(5, 10, 0) < 5)
        self.assertFalse(FileRegion(5, 10, 0) < 4)
        self.assertFalse(FileRegion(5, 10, 0) < 7)


if __name__ == '__main__':
    unittest.main()

