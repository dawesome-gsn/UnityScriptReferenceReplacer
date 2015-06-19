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
import shutil
from IPTech import Asset
from tempfile import mkstemp


def GetUnityScriptFileId(name, namespace):
	#Unity script file id is the first four bytes of the MD4 hash of "s\0\0\0" + namespace + name, interpreted as a little endian
	# 32-byte integer. ("s\0\0\0\" is 115 as a 32-byte int, which is the class ID for MonoScript.)
	hashString = "s\0\0\0" + namespace + name
	md4 = hashlib.new('md4', hashString.encode('utf-8')).hexdigest().upper()
	intTuple = struct.unpack("<i", md4[:4]) # unpack the string as 4-byte little endian ints
	return intTuple[0]

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Fixup script references for scripts that were previously loose script files and have moved into a dll. Run CreateUnityFileIDForDLLScripts.py on the scripts that create the dll first.")
	parser.add_argument('scriptIdFile', help="The csv output from CreateUnityFileIDForDLLScripts.py to use.")
	parser.add_argument('assetDir', help="The directory to look for Unity assets in")
	parser.add_argument('assetValut', help="The AssetValut.csv from the original Unity project. Used to match files to their old GUIDs")
	parser.add_argument('--dryrun', help="If set, prints substitutions without modifing the asset files.", action="store_true")
	args = parser.parse_args()

	idFile = open(args.scriptIdFile, 'r')
	newDLLScriptGuid = idFile.readline()

	scriptNameIdTuples = []
	for line in idFile:
		ll = line.split(":")
		print("Added to scriptNames " + ll[0] + ", " + ll[1])
		scriptNameIdTuples.append(ll)

	#Load the existing assets/GUIDs
	oldAssetList = Asset.LoadVault(args.assetValut)
	testGuid = ""
	for asset in oldAssetList:
		if asset.filename.endswith("View.cs"):
			testGuid = asset.guid.strip()
			print("Found " + asset.filename + " " + asset.guid)

	excludedDirs = set([".svn", ".DS_Store"])
	for path, dirs, files in os.walk(args.assetDir):
		dirs[:] = [d for d in dirs if d not in excludedDirs]

		for name in files:
			if name == ".DS_Store":
				continue
			#print("looking at " + path + "/" + name)
			
			# Look for script references within our old prefab/scene files
			if name.endswith(".prefab") or name.endswith(".unity"):
			# if name == "DailySpinnerWheel.prefab":
				filename = os.path.join(path, name)
				tempFileHandle, tempAbsPath = mkstemp()
				with open(tempAbsPath, 'w') as newAssetFile:
					with open(filename, 'r') as existingAssetFile:
						for line in existingAssetFile:
							if line.strip().startswith("m_Script:"):
								fileIdIndex = line.find("fileID: ") + 8
								endFileIdIndex = fileIdIndex + line[fileIdIndex:].find(",")
								fileId = line[fileIdIndex:endFileIdIndex].strip()

								guidIndex = line.find("guid: ") + 6;
						 		endGuidIndex = guidIndex + line[guidIndex:].find(",")
								guid = line[guidIndex:endGuidIndex].strip()

								# if name.endswith("DailySpinnerWheel.prefab"):
								# 	print(name + " has guid " + guid)
								#print("Checking " + name + " for script guid " + guid)
						 		matchedName = False
						 		for asset in oldAssetList:
									#if guid==testGuid:
									#	print("Matched testGuid!")
									if guid==asset.guid.strip():
										# print("Found matching script guid, " + asset.filename + " " + guid)
										assetScriptName = asset.filename[asset.filename.rfind("/") + 1:-3] # Everything after the last /, excepting ".cs"
										#print("Matching against " + assetScriptName)
										for scriptName, scriptFileId in scriptNameIdTuples:
											if scriptName == assetScriptName :
												if matchedName:
													sys.exit("Matched " + asset.filename + " more than once!")
												matchedName = True
												#print("  Found matching script name, " + scriptName)
												newline = line.replace(fileId, scriptFileId.strip()).replace(guid, newDLLScriptGuid.strip())
												print ("In " + name + ", matched " + scriptName +", replacing \n\t" + line + "with\n\t" + newline)
												newAssetFile.write(newline)
								if not matchedName:
									newAssetFile.write(line)
							else :
								newAssetFile.write(line)

				os.close(tempFileHandle)

				if not args.dryrun:
					os.remove(filename)
					shutil.move(tempAbsPath, filename)
				else:
					os.remove(tempAbsPath)
