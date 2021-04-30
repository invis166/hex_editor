import unittest

from modules.fileregion import FileRegion, EditedFileRegion


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

    def test_truncate_start(self):
        region = FileRegion(0, 10, 0)
        region.truncate_start(5)
        self.assertEqual(region.start, 5)
        self.assertEqual(region.original_start, 5)

    def test_truncate_end(self):
        region = FileRegion(0, 10, 0)
        region.truncate_end(5)
        self.assertEqual(region.end, 5)
        self.assertEqual(region.original_end, 5)

    def test_move(self):
        region = FileRegion(0, 10, 0)
        region.move(8)
        self.assertEqual(region.start, 8)
        self.assertEqual(region.end, 18)
        self.assertEqual(region.original_start, 0)
        self.assertEqual(region.original_end, 10)

    def test_split_without_offset(self):
        region = FileRegion(0, 10, 0)
        region.move(8)
        left, right = region.split(15)
        self.assertEqual(left.start, 8)
        self.assertEqual(left.end, 14)
        self.assertEqual(right.start, 15)
        self.assertEqual(right.end, 18)
        self.assertEqual(left.original_start, 0)
        self.assertEqual(left.original_end, 6)
        self.assertEqual(right.original_start, 7)
        self.assertEqual(right.original_end, 10)


if __name__ == '__main__':
    unittest.main()