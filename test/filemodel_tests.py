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
        self.model.file_regions = convert_tuples_to_regions(
            (0, 5), (6, 10), (11, 17), (18, 30))

    def test_search(self):
        self._test_search((0, 5), 1)
        self._test_search((0, 5), 2)
        self._test_search((0, 5), 3)
        self._test_search((0, 5), 4)
        self._test_search((0, 5), 5)

        self._test_search((11, 17), 11)
        self._test_search((11, 17), 12)
        self._test_search((11, 17), 13)
        self._test_search((11, 17), 14)
        self._test_search((11, 17), 15)

        self._test_search((18, 30), 18)
        self._test_search((18, 30), 19)
        self._test_search((18, 30), 20)

    def _test_search(self, expected, offset):
        result = convert_regions_to_tuples([self.model.search_region(offset)])[0]
        self.assertSequenceEqual(expected, result)

    def test_replace_single_from_start(self):
        self.model.replace(0, [1, 2, 3, 4])
        self._basic_test(region_index=0, offset=0,
                         data=[1, 2, 3, 4], expected_length=5)
        new = self.model.file_regions[0]
        self._check_adjacent_borders(new, right_end=5)
        self._check_indices()

    def test_replace_full_region(self):
        self.model.replace(0, [1, 2, 3, 4, 5, 6])
        new = self.model.file_regions[0]
        self._basic_test(region_index=0, offset=0,
                         data=[1, 2, 3, 4, 5, 6], expected_length=4)
        self._check_adjacent_borders(new, right_end=10)
        self._check_indices()

    def test_replace_many_regions_1(self):
        self.model.replace(6, list(range(20)))
        new = self.model.file_regions[1]
        self._basic_test(region_index=1, offset=6,
                         data=list(range(20)), expected_length=3)
        self._check_adjacent_borders(new, left_start=0, right_end=30)
        self._check_indices()

    def test_replace_many_regions_2(self):
        self.model.replace(0, list(range(11)))
        new = self.model.file_regions[0]
        self._basic_test(region_index=0, offset=0,
                         data=list(range(11)), expected_length=3)
        self._check_adjacent_borders(new, right_end=17)
        self._check_indices()

    def test_replace_single_in_middle(self):
        self.model.replace(2, [1, 2, 3])
        new = self.model.file_regions[1]
        self._basic_test(region_index=1, offset=2,
                         data=[1, 2, 3], expected_length=6)
        self._check_adjacent_borders(new, left_start=0, right_end=5)
        self._check_indices()

    def test_replace_single_to_end(self):
        self.model.replace(7, list(range(4)))
        new = self.model.file_regions[2]
        self._basic_test(region_index=2, offset=7,
                         data=list(range(4)), expected_length=5)
        self._check_adjacent_borders(new, left_start=6, right_end=17)
        self._check_indices()

    def test_replace_many_from_middle(self):
        self.model.replace(2, list(range(13)))
        new = self.model.file_regions[1]
        self._basic_test(region_index=1, offset=2,
                         data=list(range(13)), expected_length=4)
        self._check_adjacent_borders(new, left_start=0, right_end=17)
        self._check_indices()

    def test_replace_all(self):
        self.model.replace(0, list(range(31)))
        new = self.model.file_regions[0]
        self.assertEqual(new.start, 0)
        self.assertEqual(new.end, 0)
        self.assertEqual(new.data, b'')
        self.assertEqual(len(self.model.file_regions), 1)

    def _check_indices(self):
        for index, region in enumerate(self.model.file_regions):
            self.assertEqual(region.index, index)

    def _basic_test(self, region_index, offset, data, expected_length):
        new = self.model.file_regions[region_index]
        self.assertIsInstance(new, EditedFileRegion)
        self.assertEqual(len(self.model.file_regions), expected_length)
        self.assertEqual(new.start, offset)
        self.assertEqual(new.end, max(offset + len(data) - 1, 0))
        self.assertListEqual(data, new.data)

    def _check_adjacent_borders(self, region, left_start=None, right_end=None):
        if (region.index != len(self.model.file_regions)
                and right_end is not None):
            self.assertEqual(self.model.file_regions[region.index + 1].start,
                             region.end + 1)
            self.assertEqual(self.model.file_regions[region.index + 1].end,
                             right_end)

        if region.index != 0 and left_start is not None:
            self.assertEqual(self.model.file_regions[region.index - 1].start,
                             left_start)
            self.assertEqual(self.model.file_regions[region.index - 1].end,
                             region.start - 1)

    def test_insert_in_beginning_1(self):
        self.model.insert(0, [1, 2, 3])
        self._basic_test(region_index=0, offset=0,
                         data=[1, 2, 3], expected_length=5)
        self._check_bounds()

    def test_insert_in_beginning_2(self):
        self.model.insert(6, [1, 2, 3, 4])
        self._basic_test(region_index=1, offset=6,
                         data=[1, 2, 3, 4], expected_length=5)
        self._check_bounds()

    def test_inserting_in_middle_1(self):
        self.model.insert(2, [1, 2, 3])
        self._basic_test(region_index=1, offset=2,
                         data=[1, 2, 3], expected_length=6)
        self._check_bounds()

    def test_inserting_in_middle_2(self):
        self.model.insert(7, [1, 2, 3])
        self._basic_test(region_index=2, offset=7,
                         data=[1, 2, 3], expected_length=6)
        self._check_bounds()

    def _check_bounds(self):
        self.assertEqual(self.model.file_regions[0].start, 0)
        for i in range(1, len(self.model.file_regions)):
            self.assertEqual(self.model.file_regions[i].start,
                             self.model.file_regions[i - 1].end + 1)


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
