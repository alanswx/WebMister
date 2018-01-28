#!/usr/bin/python3
import os
import shutil
import mimetypes
import datetime
from mimetypes import MimeTypes
from zipfile import ZipFile
from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
from server.FileManagerResponse import *



class MasterFileManager:

    mounts=None

    def __init__(self,pmounts):
      self.mounts=pmounts


    # Path to your files root
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)),'files')
    def fileManagerError(self,title='FORBIDDEN_CHAR_SLASH'):
       return self.error(title)
    def is_safe_path(self,path, follow_symlinks=True):
       basedir = self.root
       # resolves symbolic links
       if follow_symlinks:
           return os.path.realpath(path).startswith(basedir)
       return os.path.abspath(path).startswith(basedir)

    def initiate(self):
        ''' Initial request to connector.
        Intended to provide the application with safe server-side data, such as shared
        configuration etc. Due to security reasons never share any credentials and other
        secured data. Provide only safe / public data. '''
        extensions                      = {}
        extensions['ignoreCase']        = True
        extensions['policy']            = "DISALLOW_LIST"
        extensions['restrictions']      = []
        security                        = {}
        security['allowFolderDownload'] = True;
        security['readOnly']            = False
        security['extensions']          = extensions;
        config                          = {}
        config['options']               = {'culture':'en'}
        config['security']              = security
        attributes                      = {}
        attributes['config']            = config
        data                            = {}
        data['id']                      = '/'
        data['type']                    = 'initiate'
        data['attributes']              = attributes
        response                        = {}
        response['data']                = data
        return jsonify(response)
#===============================================================================
    def mount(self):
        return self.mountfile()
    def mountfile(self):
        file    = request.args.get('path').lstrip("/")
        print('orig file:'+file)
        found_mount=self.mounts.lookupmount(file)
        fm = found_mount['handler']
        file = found_mount['path']
        path = os.path.join(fm.getRoot() ,file)
        #file        = request.args.get('path').lstrip("/")
        #path        = os.path.join(self.root,file)
        print('file:'+file+'path:'+path)
        #if (self.is_safe_path(path)):
           #self.mounts.mountfileunix(path,file)
        self.mounts.mountfilehfs(path,file)
        return self.readfolder_folder("")

    def getinfo(self):
        ''' Provides data for a single file. '''
        file    = request.args.get('path').lstrip("/")
        found_mount=self.mounts.lookupmount(file)
        fm = found_mount['handler']
        print("*** found_mount['path']:"+found_mount['path']+" **")
        return fm.getinfo(found_mount['path'])

    def readfile(self):
        ''' Provides data for a single file. '''
        file    = request.args.get('path').lstrip("/")
        print('lookup ['+file+']')
        found_mount=self.mounts.lookupmount(file)
        fm = found_mount['handler']
        print("*** found_mount['path']:"+found_mount['path']+" **")
        return fm.readfile(found_mount['path'])
#===============================================================================
    def readfolder(self):
        folder          = request.args.get('path').lstrip("/")
        return self.readfolder_folder(folder)
    def readfolder_folder(self,folder):
        ''' Provides list of file and folder objects contained in a given directory. '''
        if (folder==''):
            print('inside top level')
            mountlist = self.mounts.getmounts()
            data            = []
            for mount in mountlist:
              # loop through each mounted volume 
              print(mount)
              m_data               = {}
              m_data['id']         = mount['name']+'/'
              m_data['type']       = "folder"
              m_attr = {}
              m_attr['name']  = mount['name']
              m_attr['readable']      = 1 
              m_attr['writable']      = 1 
              m_data['attributes']       = m_attr
              data.append(m_data)
            results         = {}
            results['data'] = data
            return jsonify(results)
        else:
           found_mount=self.mounts.lookupmount(folder)
           fm = found_mount['handler']
           print("*** found_mount['path']:"+found_mount['path']+" **")
           return fm.readfolder(found_mount['path'])
#===============================================================================
    def addfolder(self):
        path = request.args.get('path').lstrip("/")
        name        = request.args.get('name')
        #file     = request.args.get('path').lstrip("/")
        found_mount=self.mounts.lookupmount(path)
        fm = found_mount['handler']
        print("*** found_mount['path']:"+found_mount['path']+" **")
        return fm.addfolder(found_mount['path'],name)
#===============================================================================
    def upload(self):
        path = request.form.get('path').lstrip("/")
        #file     = request.args.get('path').lstrip("/")
        found_mount=self.mounts.lookupmount(path)
        fm = found_mount['handler']
        print("*** found_mount['path']:"+found_mount['path']+" **")
        return fm.upload(found_mount['path'])
#===============================================================================
    def rename(self):
        ''' Renames an existed file or folder. '''
        # Relative path of the source file/folder to rename. e.g. "/images/logo.png"
        old      = request.args.get('old').lstrip("/")
        found_mount_old=self.mounts.lookupmount(old)
        fm_old = found_mount_old['handler']
        new      = request.args.get('new')
        return fm_old.rename(found_mount_old['path'],new)
#===============================================================================
    def move(self):
        ''' Moves file or folder to specified directory. '''
        # Relative path of the source file/folder to move. e.g. "/images/logo.png"
        old      = request.args.get('old').lstrip("/")
        print('move: old:'+old)
        found_mount_old=self.mounts.lookupmount(old)
        fm_old = found_mount_old['handler']
        fm_old_path = found_mount_old['path']
        print("*** found_mount_old['path']:"+fm_old_path+" **")
        parts    = old.split('/')
        filename = parts.pop()
        path     = '/'.join(parts)
        old_path = os.path.join(self.root,old)
        # New relative path for the file/folder after the move. e.g. "/images/target/"
        new      = request.args.get('new').lstrip("/")
        new_path = os.path.join(self.root,new,filename)
        print('move new:'+new)
        found_mount_new=self.mounts.lookupmount(new)
        fm_new= found_mount_new['handler']
        print("*** found_mount_new['path']:"+found_mount_new['path']+" **")
        if fm_old==fm_new:
           print('fm_old == fm_new')
           return fm_old.move(fm_old_path,found_mount_new['path'])
        else:
           print('different system? fm_old != fm_new')
           self.recursiveFStoFSCopy(fm_old,fm_new,fm_old_path,found_mount_new['path'])
           print('readfolder:'+new)
           return self.readfolder_folder(new)

#===============================================================================
    def recursiveFStoFSCopy(self,src_fm,dst_fm,src,dst):
           print('recursiveFStoFSCopy: src: '+src+' dst:'+dst)
           #is the source a file?
           dir=src_fm.is_dir(src)
           parts    = src.split('/')
           src_filename = parts.pop()
           print('dir:'+str(dir))
           if dir:
             # create destination folder
             print('create dest folder:['+dst+'] ['+src+']')
             dst_name=src #os.path.join(dst,src)
             dst_fm.addfolder('',src)
             # get list of files in dst_name
             src_list=src_fm.get_dir_list(src)
             for entry in src_list:
                print(entry)
                src_name=os.path.join(src,entry['name'])
                print(src_name)
                self.recursiveFStoFSCopy(src_fm,dst_fm,src_name,dst_name)
           else:
             # copy file from src to tmp
             print('else - copy regular file')
             src_fm.copy_to_tmp(src,"tempname")
             # copy file from tmp to dst
             dst_name=os.path.join(dst,src_filename)
             print('about to call copy_from_tmp:'+dst_name)
             dst_fm.copy_from_tmp("tempname",dst_name)
             os.remove("tempname")

#===============================================================================
    def copy(self):
        ''' Copies file or folder to specified directory. '''
        # Relative path of the source file/folder to move. e.g. "/images/logo.png"
        old      = request.args.get('source').lstrip("/")
        found_mount_old=self.mounts.lookupmount(old)
        fm = found_mount_old['handler']
        fm_old_path = found_mount_old['path']
        new      = request.args.get('target').lstrip("/")
        found_mount_new=self.mounts.lookupmount(new)
        fm_new_path = found_mount_new['path']
        return fm.copy(fm_old_path,fm_new_path)
        parts    = old.split('/')
        filename = parts.pop()
        path     = '/'.join(parts)
        old_path = os.path.join(self.root,old)
        # New relative path for the file/folder after the move. e.g. "/images/target/"
        new      = request.args.get('new').lstrip("/")
        new_path = os.path.join(self.root,new,filename)
        if (self.is_safe_path(new_path)):
           shutil.copyfile(old_path, new_path)
           response = FileManagerResponse(new_path)
           response.set_response()
           return jsonify(response.response)
        else:
           return self.fileManagerError()
#===============================================================================
    def savefile(self):
        ''' Overwrites the content of the specific file to the "content" request parameter value. '''
        file    = request.form.get('path').lstrip("/")
        content = request.form.get('content')
        found_mount=self.mounts.lookupmount(file)
        fm = found_mount['handler']
        print("*** found_mount['path']:"+found_mount['path']+" **")
        return fm.savefile(found_mount['path'],content)
#===============================================================================
    def delete(self):
        ''' Deletes an existed file or folder. '''
        file    = request.args.get('path').lstrip("/")
        found_mount=self.mounts.lookupmount(file)
        fm = found_mount['handler']
        print("*** found_mount['path']:"+found_mount['path']+" **")
        return fm.delete(found_mount['path'])
#===============================================================================
    def download(self):
        file     = request.args.get('path').lstrip("/")
        ''' Downloads requested file or folder.
        The download process consists of 2 requests:
        1. Ajax GET request. Perform all checks and validation. Should return
        file/folder object in the response data to proceed.
        2. Regular GET request. Response headers should be properly configured
        to output contents to the browser and start download.
        Thus the implementation of download method should differentiate requests
        by type (ajax/regular) and act accordingly. '''
        found_mount=self.mounts.lookupmount(file)
        fm = found_mount['handler']
        print("*** found_mount['path']:"+found_mount['path']+" **")
        return fm.download(found_mount['path'])
#===============================================================================
    def getimage(self):
        ''' Outputs the content of image file to browser. '''
        file      = request.args.get('path').lstrip("/")
        found_mount=self.mounts.lookupmount(file)
        fm = found_mount['handler']
        print("*** found_mount['path']:"+found_mount['path']+" **")
        return fm.getimage(found_mount['path'])
#===============================================================================
    def areadfile(self):
        ''' Outputs the content of requested file to browser. Intended to read
        file requested via connector path (not absolute path), for files located
        outside document root folder or hosted on remote server. '''
        file     = request.args.get('path').lstrip("/")
        path     = os.path.join(self.root,file)
        mimetype, encoding = MimeTypes().guess_type(path)
        parts = file.split('/')
        filename = parts.pop()
        if (self.is_safe_path(path)):
           return send_file(path,
                     mimetype=mimetype,
                     attachment_filename=filename,
                     as_attachment=True)
        else:
           return self.fileManagerError()
#===============================================================================
    def summarize(self):
        ''' Display user storage folder summarize info. '''
        statinfo                = os.stat(self.root)
        attributes              = {}
        attributes['size']      = statinfo.st_size
        attributes['files']     = len([name for name in os.listdir(self.root) if os.path.isfile(name)])
        attributes['folders']   = len([name for name in os.listdir(self.root) if os.path.isdir(name)])
        attributes['sizeLimit'] = 0
        data                    = {}
        data['id']              = '/'
        data['type']            = 'summary'
        data['attributes']      = attributes
        result                  = {}
        result['data']          = data
        return jsonify(result)
#===============================================================================
    def extract(self):
        ''' Extract files and folders from zip archive.
        Note that only the first-level of extracted files and folders are returned
        in the response. All nested files and folders should be omitted for correct
        displaying at the client-side. '''
        source          = request.form.get('source').lstrip("/")
        src_found_mount=self.mounts.lookupmount(source)
        srcfm = src_found_mount['handler']
        newsrc_path=src_found_mount['path']
        print("*** src_found_mount['path']:"+src_found_mount['path']+" **")
        source_path     = os.path.join(self.root,source)
        target          = request.form.get('target').lstrip("/")
        target_found_mount=self.mounts.lookupmount(target)
        targetfm = target_found_mount['handler']
        newtarget_path=target_found_mount['path']
        print("*** target_found_mount['path']:"+target_found_mount['path']+" **")
        return srcfm.extract(newsrc_path,newtarget_path)
#===============================================================================
    def error(self,title='Server Error. Unexpected Mode.'):
        '''  '''
        result           = {}
        errors           = []
        error            = {}
        error['id']      = 'server'
        error['code']    = '500'
        error['title']   = title
        errors.append(error)
        result['errors'] = errors
        return jsonify(result)
#===============================================================================
    def is_binary_file(self,filepathname):
        textchars = bytearray([7,8,9,10,12,13,27]) + bytearray(range(0x20, 0x7f)) + bytearray(range(0x80, 0x100))
        is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
        try:
            if is_binary_string(open(filepathname, 'rb').read(1024)):
               return True
        except UnicodeDecodeError:
            print('decode error')
        return False
