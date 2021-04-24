import os.path
from buffer import DataBuffer
from filemodel import FileModel


class HexEditor:
	def __init__(self, filename: str):
		self._fp = open(filename, 'r+b')
		self._model = FileModel(os.path.getsize(filename))
		self._buffer = DataBuffer(self._model, self._fp)

	def get_nbytes(self):
		pass

	def replace_bytes(self):
		pass

	def insert_bytes(self):
		pass

	def remove_bytes(self):
		pass

	def save_changes(self):
		pass

	def __del__(self):
		self.fp.close()


if __name__ == '__main__':
	pass