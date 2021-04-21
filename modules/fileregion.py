from functools import total_ordering


@total_ordering
class FileRegion:
	def __init__(self, start, end):
		self.start = start
		self.end = end

	def __eq__(self, other):
		if isinstance(other, int):
			return self.start <= other <= self.end

		if isinstance(other, FileRegion):
			pass

	def __gt__(self, other):
		if isinstance(other, int):
			return self.start > other

		if isinstance(other, FileRegion):
			pass

	def __lt__(self, other):
		if isinstance(other, int):
			return self.end < other

		if isinstance(other, FileRegion):
			pass

	def __repr__(self):
		return f'FileRegion({self.start}, {self.end})'
