from collections import deque


class HexEditor:
	def __init__(self, filename: str):
		self.fp = open(filename, 'r+b')
		self.chunk_size = 1024

		self._changes = deque
		self._buffer = []

	def read_nbytes(self, count: int, offset: int=None):
		if offset != None:
			self.fp.seek(offset)

		while data := self.fp.read(chunk := min(self.chunk_size, count)):
			yield from data
			count -= chunk

	def read_bytes(self, start: int, end: int):
		return self.read_nbytes(end - start, start)

	def get_hex_view(self):
		return ' '.join(map(lambda x: hex(x)[2:], 
			            self.read_nbytes(self.chunk_size)))

	def replace(self, start: int, data: bytes):
		fp.seek(start)

	def insert(self):
		pass

	def __del__(self):
		self.fp.close()



if __name__ == '__main__':
	pass