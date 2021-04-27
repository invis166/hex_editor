import unittest

from modules.editor import HexEditor


class HexEditorOnRealFileTestCase(unittest.TestCase):
    def test(self):
        editor = HexEditor('simple_file.txt')
        editor.insert_bytes(5, b'test')
        editor.insert_bytes(0, b'test')
        editor.replace_bytes(3, b'rep')