import unittest
import hex_editor as t


class TestEditor(unittest.TestCase):
	def setUp(self):
		self.editor = t.hex_editor()


if __name__ == '__main__':
	unittest.main()