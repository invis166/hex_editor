import unittest

from modules.fileregion import FileRegion


class MyTestCase(unittest.TestCase):
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
