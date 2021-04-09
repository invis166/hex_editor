import unittest
import os


sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))


class TestEditor(unittest.TestCase):
	def setUp(self):
		self.editor = t.hex_editor()


if __name__ == '__main__':
	unittest.main()