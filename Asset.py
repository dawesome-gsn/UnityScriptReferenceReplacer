import sys
import os

class Asset(object):
	def __init__(self, name, guid):
		self.filename = name
		self.guid = guid

def AssetFromPath(path):
	newAsset = None
	meta = path + ".meta"
	filename = path[path.find("Assets"):]

	if os.path.isfile(meta):
		f = open(meta, 'r')
		for line in f:
			if line.startswith("guid:"):
				guid = line[5:].strip()
				newAsset = Asset(filename, guid)
				break
		f.close()
	return newAsset
