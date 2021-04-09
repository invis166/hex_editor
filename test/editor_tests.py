import unittest
import os
import sys


sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
from hex_editor.editor import HexEditor


class TestEditor(unittest.TestCase):
    def setUp(self):
        with open('simple_file.txt', 'rb') as file:
            self.file_data = file.read()

        self.editor = HexEditor('simple_file.txt')

    def tearDown(self):
        self.editor.__del__()

    def test_hex_view(self):
        self.assertEqual(self.file_data.hex(' '), self.editor.get_hex_view())

    def test_read_nbytes_from_start(self):
        for i in range(min(len(self.file_data), 100)):
            self._test_read_nbytes(i, 0)

    def test_read_nbytes_with_offset(self):
        chunk_size = 3
        for i in range(min(len(self.file_data), 100) - chunk_size):
            self._test_read_nbytes(chunk_size, i)

    def test_read_nbytes_one_by_one(self):
        for i in range(min(len(self.file_data), 100)):
            self.assertEqual(self.file_data[i],
                             next(self.editor.read_nbytes(1)))

    def _test_read_nbytes(self, count, offset=None):
        if offset != None:
            self.assertSequenceEqual(
                self.file_data[offset:count + offset],
                list(self.editor.read_nbytes(count, offset)))
        else:
            self.assertSequenceEqual(self.file_data[:count],
                					 list(self.editor.read_nbytes(count)))


if __name__ == '__main__':
    unittest.main()
