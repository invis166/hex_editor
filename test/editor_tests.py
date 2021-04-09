import unittest
import os
import sys


sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
from hex_editor.editor import HexEditor


class TestEditor(unittest.TestCase):
	def setUp(self):
		self.editor = HexEditor()


if __name__ == '__main__':
	unittest.main()