'''
@author: Michael Dawe
'''

import sys
import os
import re
import string
import hashlib
import struct
import argparse


def GetUnityScriptFileId(classname, namespace):
	#Unity script file id is the first four bytes of the MD4 hash of "s\0\0\0" + namespace + name, interpreted as a little endian
	# 32-byte integer. ("s\0\0\0\" is 115 as a 32-byte int, which is the class ID for MonoScript.)
	hashString = "s\0\0\0" + namespace + classname

	md4 = hashlib.new('md4', hashString).digest()
	md4Tuple = struct.unpack("<i", md4[:4])

	# if classname.endswith("InputManager"):
	# 	print("utf  8  : " + str(utf8Tuple[0]))
	# 	print("utf 16le: " + str(utf16leTuple[0]))
	# 	print("utf 16ge: " + str(utf16beTuple[0]))
	# 	print("regular : " + str(regularTuple[0]))
	# 	print("Goal    : 1682207554")

	return md4Tuple[0]

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Calculates Unity FileIds for scripts in a folder. Creates output used by FixupUnityScriptRefrences.py")
	parser.add_argument('scriptDir', help="The directory to look for .cs files in")
	parser.add_argument('dllFile',   help="The dll.meta that Unity will use in place of these cs files (i.e., where Unity looks the the dll that is built from these .cs files)")

	args = parser.parse_args()

	csFileList = []
	dllGuid = ""

	metaFile = open(args.dllFile, 'r')
	for line in metaFile:
		if line.startswith("guid:"):
			dllGuid = line[6:].strip() #format is "guid: ", so slice from char 6



	for path, subdirs, files in os.walk(args.scriptDir):
		#dirs = path.split(os.pathstep)
		#for d in dirs:
		#	if d==".svn" or d==".DS_Store":
		#		continue

		for name in files:
			#print("looking at " + path + "/" + name)
			if name.endswith(".cs"):
				#print ("found " + name)
				foundNamespace = False
				namespace = ""
				csFile = open(os.path.join(path, name), 'r')
				for line in csFile:
					namespaceMatch = re.search('(?<=namespace).*' ,line)
					if not namespaceMatch == None:
						foundNamespace = True
						namespace = namespaceMatch.group(0).strip(string.whitespace + "{").strip()
						#print ("File " + name + " has namespace " + namespace)


				# We have the namespace. Now output our name, namespace, and md4
				classname = name[:-3] # remove the ".cs"
				scriptFileInfo = classname, namespace, GetUnityScriptFileId(classname, namespace)
				csFileList.append(scriptFileInfo)

	if len(csFileList) > 0:
		f = open(args.scriptDir + "_scriptIds.csv", 'w')
		print dllGuid
		f.write(dllGuid + "\n")

		for name, namespace, scriptId in csFileList:
			print name, namespace, scriptId
			f.write(name + ":" + str(scriptId) + "\n")
		f.close()

