from functools import total_ordering
import bisect


class FileModel:
	def __init__(self):
		pass

	def search_regions(self, count: int, offset: int):
		region_index = bisect.bisect_left(self._regions, offset)

		result = []
		if region_index != -1:
			while self._regions[region_index] <= offset + count:
				print('here')
				result.append(self._regions[region_index])
				region_index += 1

		return result

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
