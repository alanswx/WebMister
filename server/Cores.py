import os
import sys
import json
import sys

class Cores:
    manifest = {}
    diskdata = {}
    mister_root = ''

    def __init__(self,DIR,MISTER):
       self.mister_root=MISTER
       self.load_manifest(DIR)

    def load_manifest(self,DIR):
        with open(os.path.join(DIR, 'server/manifest.json'), 'r') as f:
            self.manifest = json.load(f)

    def update_core_from_disk(self,core):
        try:
           if not self.manifest[core]:
              return {}
        except KeyError:
            return {}

        coreinfo = {}
        print(core)
        print(self.manifest[core])
        print(self.manifest[core]['additionalData'])
        if (self.manifest[core]['additionalData']):
           directory = os.path.join(self.mister_root,self.manifest[core]['additionalDataDir'])
           additional=[]
           for e in  self.manifest[core]['additionalData']:
              print(e)
              if (e['target']):
                  filename = os.path.join(directory,e['target'])
                  if (os.path.exists(filename)):
                      stats = os.stat(filename)
                      e['created']     = int(stats.st_ctime)
                      e['modified']     = int(stats.st_mtime)
                      e['timestamp']     = int(stats.st_mtime)
                      e['sizeondisk']     = int(stats.st_size)
                      additional.append(e)
                      print(stats)
           # check
           coreinfo['additionalData']=additional
        self.diskdata[core]=coreinfo
        return coreinfo 

    def update_cores_from_disk(self):
        for core in self.manifest:
            self.update_core_from_disk(core)
        print(self.diskdata)
        return self.diskdata


if __name__ == "__main__":
     core = Cores(os.path.join(sys.path[0],".."),os.path.join(sys.path[0],"../../InstallerMister/misterinst"))
     core.update_cores_from_disk()
