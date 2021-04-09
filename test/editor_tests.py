import unittest
import os
import sys


sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
from hex_editor.editor import HexEditor


class TestEditor(unittest.TestCase):
	def setUp(self):
		self.editor = HexEditor('simple_file.txt')

	def test_hex_view(self):
		self.assertEqual('41 41 41 41 42 42 42 42 43 43 43 43', 
						 self.editor.get_hex_view())


if __name__ == '__main__':
	unittest.main()