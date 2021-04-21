from collections import deque

from buffer import DataBuffer
from fileregion import FileRegion


class HexEditor:
	def __init__(self, filename: str):
		self._fp = open(filename, 'r+b')
		self._buffer = DataBuffer()
		self._regions = []

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


'''
Не уверен, где должен быть буффер, у редактора или у графической составляющей.
Все действия редактирования должны быть делегированы в FileModel.
Если делегировать все редактирование FileModel, то какие фукнции остаются у 
сущности HexEditor и нужна ли она вообще?
'''