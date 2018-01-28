#!/usr/bin/python3
import os
import shutil
import mimetypes
import datetime
from mimetypes import MimeTypes
from zipfile import ZipFile
from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
from server.FileManager import *
from server.HFSFileManager import *
from server.FileManagerResponse import *



class Mount:
    mounts = []
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)),'files')

    # start out by initializing the root of the file system
    def __init__(self):
       self.mountfileunix(self.root,'MiSTer')
       self.mountfileunix('/home/alans/mister/InstallerMister/misterinst','Cores')
       #self.mountfilehfs('/home/alans/Downloads/MinivMacBootv2.dsk','MinivMacBootv2.dsk')
       #self.mountfilehfs('/home/alans/Downloads/games-o.dsk','gameso')

    def getmounts(self):
       return self.mounts
    def lookupmount(self,folder):
       parts    = folder.split('/')
       mountname = parts.pop(0)
       path     = '/'.join(parts)
       print(mountname)
       print(path)
       found_mount = None
       for m in self.mounts:
          if m['name']==mountname:
             found_mount=m
             found_mount['path']=path
       return found_mount
          

     
    def mountfileunix(self,path,name):
       entry = {}
       entry['path']=path
       entry['name']=name
       entry['handler']=FileManager(path,name)
       self.mounts.append(entry)

    def mountfilehfs(self,path,name):
       print('mountfilehfs: path:'+path+' name:'+name)
       entry = {}
       entry['path']=path
       entry['name']=name
       entry['handler']=HFSFileManager(path,name)
       self.mounts.append(entry)

       
    def mountfile(self,path):
       print(self.mounts)
       self.mounts.append(path)
       print(self.mounts)
