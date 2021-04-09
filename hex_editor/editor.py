class HexEditor:
	def __init__(self, filename):
		self.fp = open(filename, 'r+b')

	def get_hex_view(self):
		print(self.fp.read().hex(' '))

	def __del__(self):
		self.fp.close()



if __name__ == '__main__':
	pass