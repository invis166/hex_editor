import unittest

from modules.editor import HexEditor


class HexEditorOnRealFileTestCase(unittest.TestCase):
    def test1(self):
        editor = HexEditor('simple_file.txt')
        editor.insert(5, b'test')
        editor.insert(0, b'test')
        editor.replace(3, b'rep')

    def test2(self):
        editor = HexEditor('simple_file.txt')
        editor.insert(7, b'dfg')
        editor.replace(3, b'abc')
        editor.insert(4, b'12345')

    def test3(self):
        editor = HexEditor('simple_file.txt')
        editor.remove(3, 5)

    def test4(self):
        editor = HexEditor('../ui.py')
        editor.replace(67, b'\x00')
        editor.get_nbytes(60, 10)
