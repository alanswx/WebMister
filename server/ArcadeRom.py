import os
import sys
import json
import zipfile
import datetime

class ArcadeRom:
    mister_root = ''
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
              return {}
        except KeyError:
            return {}

        # AJS - TODO - fix directory paths for both read and write rom (zip and .rom)
        thiscore = self.manifest[core]
        arcadeRom = thiscore["arcadeRom"]
        arcadeRomFiles = thiscore["arcadeRomFiles"]
        arcadeRomOutput= thiscore["arcadeRomOutput"] 
        print(arcadeRom)
        print(arcadeRomFiles)
        print(arcadeRomOutput)
        arcadeRomFileParts = arcadeRomFiles.split("+")
        zf = zipfile.ZipFile('../froggers2.zip', 'r')
        romfile=open(arcadeRomOutput,'wb')
        for name in arcadeRomFileParts:
           print("arcade file:")
           print(name)
           data = zf.read(name)
           romfile.write(data)
           print name, len(data), repr(data[:10])
        romfile.close()
        print zf.namelist()
        for info in zf.infolist():
            print info.filename
            print '\tComment:\t', info.comment
            print '\tModified:\t', datetime.datetime(*info.date_time)
            print '\tSystem:\t\t', info.create_system, '(0 = Windows, 3 = Unix)'
            print '\tZIP version:\t', info.create_version
            print '\tCompressed:\t', info.compress_size, 'bytes'
            print '\tUncompressed:\t', info.file_size, 'bytes'
            print

if __name__ == "__main__":
     arcadeRom= ArcadeRom(os.path.join(sys.path[0],".."),os.path.join(sys.path[0],"../../InstallerMister/misterinst"))
     arcadeRom.convertRom("frogger")
