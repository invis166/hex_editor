import unittest

from modules.filemodel import FileModel
from modules.fileregion import FileRegion, EditedFileRegion


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

    def test_replace_from_start(self):
        self.model.replace(0, [1, 2, 3, 4])
        self._basic_test(region_index=0, offset=0,
                         data=[1, 2, 3, 4], expected_length=5)
        new = self.model.file_regions[0]
        self._check_adjacent_borders(new, right_end=5)

    def test_replace_from_start_many(self):
        self.model.replace(6, list(range(20)))
        new = self.model.file_regions[1]
        self._basic_test(region_index=1, offset=6,
                         data=list(range(20)), expected_length=3)
        self._check_adjacent_borders(new, left_start=0, right_end=30)

    def test_replace_from_start_many_2(self):
        self.model.replace(0, list(range(11)))
        new = self.model.file_regions[0]
        self._basic_test(region_index=0, offset=0,
                         data=list(range(11)), expected_length=3)
        self._check_adjacent_borders(new, right_end=17)

    def test_replace_in_middle(self):
        self.model.replace(2, [1, 2, 3])
        new = self.model.file_regions[1]
        self._basic_test(region_index=1, offset=2,
                         data=[1, 2, 3], expected_length=6)
        self._check_adjacent_borders(new, left_start=0, right_end=5)

    def test_replace_to_end(self):
        self.model.replace(7, list(range(4)))
        new = self.model.file_regions[2]
        self._basic_test(region_index=2, offset=7,
                         data=list(range(4)), expected_length=5)
        self._check_adjacent_borders(new, left_start=6, right_end=17)

    def test_replace_from_middle_many(self):
        self.model.replace(2, list(range(13)))
        new = self.model.file_regions[1]
        self._basic_test(region_index=1, offset=2,
                         data=list(range(13)), expected_length=4)
        self._check_adjacent_borders(new, left_start=0, right_end=17)

    def test_replace_all(self):
        self.model.replace(0, list(range(31)))
        self._basic_test(region_index=0, offset=0,
                         data=list(range(31)), expected_length=1)

    def test_insert_in_beginning_1(self):
        self.model.insert(0, [1, 2, 3])
        self._basic_test(region_index=0, offset=0,
                         data=[1, 2, 3], expected_length=5)

    def test_insert_in_beginning_2(self):
        self.model.insert(6, [1, 2, 3, 4])
        self._basic_test(region_index=1, offset=6,
                         data=[1, 2, 3, 4], expected_length=5)

    def test_insert_in_middle_1(self):
        self.model.insert(2, [1, 2, 3])
        self._basic_test(region_index=1, offset=2,
                         data=[1, 2, 3], expected_length=6)

    def test_insert_in_middle_2(self):
        self.model.insert(7, [1, 2, 3])
        self._basic_test(region_index=2, offset=7,
                         data=[1, 2, 3], expected_length=6)

    def test_replace_full_region(self):
        self.model.replace(0, [1, 2, 3, 4, 5, 6])
        new = self.model.file_regions[0]
        self._basic_test(region_index=0, offset=0,
                         data=[1, 2, 3, 4, 5, 6], expected_length=4)
        self._check_adjacent_borders(new, right_end=10)

    def test_remove_all(self):
        self.model.remove(0, 31)
        self._basic_test(region_index=0, offset=0,
                         data=b'', expected_length=1,
                         is_removing=True)

    def test_remove_from_start(self):
        self.model.remove(0, 4)
        self._basic_test(region_index=0, offset=0,
                         data=list(range(2)), expected_length=4,
                         is_removing=True)

    def test_remove_from_start_many(self):
        self.model.remove(0, 15)
        self._basic_test(region_index=0, offset=0,
                         data=[4, 5, 6], expected_length=2,
                         is_removing=True)

    def test_remove_in_middle_1(self):
        self.model.remove(1, 3)
        self._basic_test(region_index=0, offset=0,
                         data=list(range(1)), expected_length=5,
                         is_removing=True)

    def test_remove_in_middle_2(self):
        # remove(3, 5)
        self.model.remove(8, 2)
        self._basic_test(region_index=1, offset=6,
                         data=[0, 1], expected_length=5,
                         is_removing=True)

    def test_remove_from_middle_many(self):
        self.model.remove(2, 13)
        self._basic_test(region_index=0, offset=0,
                         data=[0, 1], expected_length=3,
                         is_removing=True)

    def test_remove_to_end(self):
        self.model.remove(2, 4)
        self._basic_test(region_index=0, offset=0,
                         data=list(range(2)), expected_length=4,
                         is_removing=True)

    def test_remove_to_end_many(self):
        self.model.remove(3, 15)
        self._basic_test(region_index=0, offset=0,
                         data=list(range(3)), expected_length=2,
                         is_removing=True)

    def test_remove_whole_region(self):
        self.model.remove(0, 6)
        self._basic_test(region_index=0, offset=0,
                         data=list(range(5)), expected_length=3,
                         is_removing=True)

    def _check_indices(self):
        for index, region in enumerate(self.model.file_regions):
            self.assertEqual(region.index, index)

    def _test_search(self, expected, offset):
        result = convert_regions_to_tuples([self.model.search_region(offset)])[0]
        self.assertSequenceEqual(expected, result)

    def _basic_test(self, region_index, offset, data, expected_length, is_removing=False):
        new = self.model.file_regions[region_index]
        if is_removing:
            self.assertIsInstance(new, FileRegion)
        else:
            self.assertIsInstance(new, EditedFileRegion)
        self.assertEqual(len(self.model.file_regions), expected_length)
        self.assertEqual(new.start, offset)
        self.assertEqual(new.end, max(offset + len(data) - 1, 0))
        if not is_removing:
            self.assertListEqual(data, new.data)

        self._check_bounds()
        self._check_indices()

    def _check_bounds(self):
        self.assertEqual(self.model.file_regions[0].start, 0)
        for i in range(1, len(self.model.file_regions)):
            self.assertEqual(self.model.file_regions[i].start,
                             self.model.file_regions[i - 1].end + 1)

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


if __name__ == '__main__':
    unittest.main()
