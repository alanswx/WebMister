#!/usr/bin/python3
import os
import re
import datetime
from PIL import Image

class HFSFileManagerResponse(object):
    # absolute path to base folder
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)),'files')
    def __init__(self,root,path,mountid,hfsentry):
        ''' Init '''
        self.root=root
        self.hfsentry=hfsentry
        if 'mod_mactype' in self.hfsentry:
           parts = self.hfsentry['mod_mactype'].split('/')
           self.mac_type=parts[0]
           self.mac_creator=parts[1]
        self.path          = path # absolute path to file or folder
        self.mountid          = mountid # absolute path to file or folder
        print('self.root:'+self.root)
        print('self.path:'+self.path)
        self.relative_path = re.sub('^'+self.root, '', self.path) # path from file manager base folder
        print('self.mountid:'+self.mountid)
        print('self.relative_path:'+self.relative_path)
        self.relative_path=self.mountid+self.relative_path
        print('self.relative_path:'+self.relative_path)
        self.type          = 'folder' if hfsentry['type']=='dir' else 'file'
        #self.statinfo      = os.stat(self.path)
        self.attributes    = None
        self.data          = None
        self.response      = None
        self.content       = None
#===============================================================================
    def set_data(self):
        ''' Build data dict for response '''
        data               = {}
        # set id (path from file manager base folder)
        data['id']         = self.relative_path
        if self.type == 'folder':
            # trailing slash is mandatory on folders
            data['id']     = self.relative_path.rstrip('/')+'/'
        data['type']       = self.type
        self.set_attributes()
        data['attributes'] = self.attributes
        self.data = data
#===============================================================================
    def set_attributes(self):
        ''' Build attributes dict for response '''
        attributes                  = {}
        attributes['name']          = self.relative_path.strip('/').split('/').pop()
        if self.type == 'file':
            attributes['extension'] = os.path.splitext(self.path)[1].lstrip('.')
            if self.mac_type=='ttro' or self.mac_type=='TEXT':
               attributes['extension'] = 'txt'
               attributes['name'] = attributes['name']+'.txt'
            if self.mac_type=='GIFf':
               attributes['extension'] = 'gif'
               attributes['name'] = attributes['name']+'.gif'
            if self.mac_type=='JPEG':
               attributes['extension'] = 'jpg'
               attributes['name'] = attributes['name']+'.jpg'
            height                  = 0
            width                   = 0
            if attributes['extension'] in ['gif','jpg','jpeg','png']:
                im = Image.open(self.path)
                height,width = im.size
            attributes['height']    = height
            attributes['width']     = width
            attributes['size']      = int(self.hfsentry['mod_datasize'])
        attributes['path']          = self.path
        attributes['readable']      = 1
        attributes['writable']      = 1

        try:
          datetime_object = datetime.datetime.strptime(self.hfsentry['mod_mdate'], '%b %d %Y')
          t=datetime_object.strftime("%s")
        except Exception:
          t="0" 
        #attributes['created']       = datetime.datetime.fromtimestamp(self.statinfo.st_ctime).ctime()
        #attributes['modified']      = datetime.datetime.fromtimestamp(self.statinfo.st_mtime).ctime()
        attributes['created']     = int(t)
        attributes['modified']     = int(t)
        attributes['timestamp']     =int(t)
        if self.content:
            attributes['content']   = self.content
        self.attributes = attributes
#===============================================================================
    def set_response(self):
        response         = {}
        self.set_data()
        response['data'] = self.data
        self.response    = response
#===============================================================================
    def set_content(self,content):
        ''' Set the content in the case where we must pass it to the client '''
        self.content = content
