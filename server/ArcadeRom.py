import os
import sys
import json
import zipfile
import datetime

class ArcadeRom:
    mister_root = ''

    def __init__(self,DIR,MISTER):
       self.mister_root=MISTER
       self.load_manifest(DIR)

    def load_manifest(self,DIR):
        with open(os.path.join(DIR, 'server/manifest.json'), 'r') as f:
            self.manifest = json.load(f)

    def convertRom(self,core):
        try:
           if not self.manifest[core]:
              return { "message" : "core not found"}
        except KeyError:
              return { "message" : "core not found"}

        # AJS - TODO - fix directory paths for both read and write rom (zip and .rom)
        thiscore = self.manifest[core]
        arcadeRom = ''
        try:
            if thiscore["arcadeRom"]:
                arcadeRom = thiscore["arcadeRom"]
        except KeyError:
            return { "message" : "Rom not in manifest"}
        arcadeRomFiles = ''
        try:
            if thiscore["arcadeRomFiles"]:
                arcadeRomFiles = thiscore["arcadeRomFiles"]
        except KeyError:
            return { "message" : "Rom Files not in manifest"}
        arcadeRomOutput= ''
        try:
            if thiscore["arcadeRomOutput"]:
                arcadeRomOutput = thiscore["arcadeRomOutput"]
        except KeyError:
            return { "message" : "Rom Output Files not in manifest"}
        arcadeRomPath = os.path.join(self.mister_root,arcadeRom)
        arcadeRomOutputPath = os.path.join(self.mister_root,arcadeRomOutput)
        print(arcadeRom)
        print(arcadeRomFiles)
        #print(arcadeRomOutput)
        arcadeRomFileParts = arcadeRomFiles.split("+")
        try:
            zf = zipfile.ZipFile(arcadeRomPath, 'r')
        except FileNotFoundError as e:
            return { "message" : 'File Not Found'}
        except Exception as e:
            return { "message" : str(e)}
        try:
            romfile=open(arcadeRomOutputPath,'wb')
        except Exception as e:
            return { "message" : str(e)}
        for name in arcadeRomFileParts:
           print("arcade file:")
           print('['+name+']')
           try:
              data = zf.read(name)
           except Exception as e:
              return { "message" : str(e)}
           romfile.write(data)
           print (name, len(data), repr(data[:10]))
        romfile.close()
        print (zf.namelist())
        for info in zf.infolist():
            print (info.filename)
            print ('\tComment:\t', info.comment)
            print ('\tModified:\t', datetime.datetime(*info.date_time))
            print ('\tSystem:\t\t', info.create_system, '(0 = Windows, 3 = Unix)')
            print ('\tZIP version:\t', info.create_version)
            print ('\tCompressed:\t', info.compress_size, 'bytes')
            print ('\tUncompressed:\t', info.file_size, 'bytes')
            print()
        zf.close()
        return { "message" : "OK"}

if __name__ == "__main__":
     arcadeRom= ArcadeRom(os.path.join(sys.path[0],".."),os.path.join(sys.path[0],"../../InstallerMister/misterinst"))
     #res=arcadeRom.convertRom("scramble")
     res=arcadeRom.convertRom("xevious")
     print(res)
