import os.path
from modules.buffer import DataBuffer
from modules.filemodel import FileModel, FileRegion, EditedFileRegion


class HexEditor:
	def __init__(self, filename: str):
		self._fp = open(filename, 'r+b')
		self._model = FileModel(os.path.getsize(filename))
		self._buffer = DataBuffer(self._model, self._fp)

	def get_nbytes(self, offset: int, count: int) -> bytes:
		return bytes(self._buffer.read_nbytes(offset, count))

	def replace(self, offset: int, data: bytes) -> None:
		self._model.replace(offset, data)

	def insert(self, offset: int, data: bytes) -> None:
		self._model.insert(offset, data)

	def remove(self, offset: int, data: bytes) -> None:
		pass

	def save_changes(self):
		for region in self._model.file_regions:
			if isinstance(region, EditedFileRegion):
				self._fp.seek(region.start)
				self._fp.write(region.data)
			elif region.original_start != region.start:
				self._fp.seek(region.start)
				self._fp.write(self.get_nbytes(region.start, region.length))
		self._fp.flush()

		self._model = FileModel(self._model.file_size)
		self._buffer._file_model = self._model

	def exit(self):
		self._fp.close()

	def __del__(self):
		self.exit()


if __name__ == '__main__':
	pass
