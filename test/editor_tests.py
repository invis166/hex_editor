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
