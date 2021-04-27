import unittest

from modules.editor import HexEditor


class HexEditorOnRealFileTestCase(unittest.TestCase):
    def test1(self):
        editor = HexEditor('simple_file.txt')
        editor.insert_bytes(5, b'test')
        editor.insert_bytes(0, b'test')
        editor.replace_bytes(3, b'rep')

    def test2(self):
        editor = HexEditor('simple_file.txt')
        editor.insert_bytes(7, b'dfg')
        editor.replace_bytes(3, b'abc')
        editor.insert_bytes(4, b'12345')
