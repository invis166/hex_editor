import unittest

from modules.buffer import DataBuffer
from modules.filemodel import FileModel, FileRegion, EditedFileRegion

from filemodel_tests import convert_regions_to_tuples,\
    convert_tuples_to_regions


class DataBufferTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.buffer = DataBuffer(FileModel(0), None)
        self.buffer._file_model.file_regions = convert_tuples_to_regions(
            (0, 10), (10, 5), (15, 3), (18, 10), (28, 10), is_edited=True)
        '''
        EFR(start=0, end=9, data=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        EFR(start=10, end=14, data=[0, 1, 2, 3, 4])
        EFR(start=16, end=18, data=[0, 1, 2])
        EFR(start=20, end=29, data=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        EFR(start=31, end=40, data=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        '''

    def test_read_nbytes_without_offset(self):
        self.assertListEqual(self.buffer.read_nbytes(0, 10), list(range(10)))
        self.assertListEqual(self.buffer.read_nbytes(0, 10), list(range(10)))
        self.assertListEqual(self.buffer.read_nbytes(0, 13),
                                 [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2])
        self.assertListEqual(self.buffer.read_nbytes(0, 15),
                                 [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4])

    def test_read_nbytes_with_offset(self):
        self.assertListEqual(self.buffer.read_nbytes(10, 3),
                             [0, 1, 2])
        self.assertListEqual(self.buffer.read_nbytes(10, 5),
                             [0, 1, 2, 3, 4])
        self.assertListEqual(self.buffer.read_nbytes(10, 6),
                             [0, 1, 2, 3, 4, 0])
        self.assertListEqual(self.buffer.read_nbytes(10, 8),
                             [0, 1, 2, 3, 4, 0, 1, 2])
        self.assertListEqual(self.buffer.read_nbytes(5, 5),
                             [5, 6, 7, 8, 9])
        self.assertListEqual(self.buffer.read_nbytes(10, 1), [0])


class DataBufferTestCaseOnRealFile(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
