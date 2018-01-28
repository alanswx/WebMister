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



class FileManager:
    # Path to your files root
    root = ''
    mountname = ''
    def __init__(self,proot,name):
       self.root=proot
       self.mountname=name
    def getRoot(self):
       return self.root
    def fileManagerError(self,title='FORBIDDEN_CHAR_SLASH'):
       return self.error(title)
    def is_safe_path(self,path, follow_symlinks=True):
       basedir = self.root
       # resolves symbolic links
       if follow_symlinks:
           return os.path.realpath(path).startswith(basedir)
       print('path:'+path+'basedir:'+basedir)
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
    def getinfo(self,file):
        ''' Provides data for a single file. '''
        #file        = request.args.get('path').lstrip("/")
        path        = os.path.join(self.root,file)
        if (self.is_safe_path(path)):
           with open(path, "r") as fh:
               content = fh.read()
           response    = FileManagerResponse(self.root,path,self.mountname)
           response.set_response()
           return jsonify(response.response)
        else:
           return self.fileManagerError()
#===============================================================================
    def readfolder(self):
        folder          = request.args.get('path').lstrip("/")
        return self.readfolder(folder)
    def readfolder(self,folder):
        ''' Provides list of file and folder objects contained in a given directory. '''
        #folder          = request.args.get('path').lstrip("/")
        folder_path     = os.path.join(self.root,folder)
        data            = []
        if (self.is_safe_path(folder_path)):
           for file in os.listdir(folder_path):
               path        = os.path.join(folder_path,file)
               response    = FileManagerResponse(self.root,path,self.mountname)
               response.set_data()
               data.append(response.data)
           results         = {}
           results['data'] = data
           return jsonify(results)
        else:
           return self.fileManagerError()
#===============================================================================
    def addfolder(self,path,name):
        ''' Creates a new directory on the server within the given path. '''
        #path        = request.args.get('path').lstrip("/")
        #name        = request.args.get('name')
        folder_path = os.path.join(self.root,path,name)
        print('addfolder: ['+folder_path+']')
        if (self.is_safe_path(folder_path)):
           print('safe addfolder: ['+folder_path+']')
           if not os.path.exists(folder_path):
               os.makedirs(folder_path)
           response    = FileManagerResponse(self.root,folder_path,self.mountname)
           response.set_response()
           return jsonify(response.response)
        else:
           return self.fileManagerError()
#===============================================================================
    def upload(self,file):
        ''' Uploads a new file to the given folder.
            Upload form in the RichFilemanager passes an uploaded file. The name of the
            form element is defined by upload.paramName option in Configuration options
            ("files[]" by default). '''
        path    = os.path.join(self.root,file)
        #path = request.form.get('path').lstrip("/")
        # check if the post request has the file part
        if 'files' in request.files:
            file = request.files.get('files')
            if file.filename != '':
                filename  = secure_filename(file.filename)
                file_path = os.path.join(self.root,path,filename)
                if (self.is_safe_path(file_path)):
                   file.save(file_path)
                   response  = FileManagerResponse(self.root,file_path,self.mountname)
                   response.set_response()
                   return jsonify(response.response)
                else:
                   return self.fileManagerError()
        # if upload failed return error
        return self.fileManagerError()
#===============================================================================
    def rename(self,old,new):
        ''' Renames an existed file or folder. '''
        # Relative path of the source file/folder to rename. e.g. "/images/logo.png"
        #old      = request.args.get('old').lstrip("/")
        parts    = old.split('/')
        filename = parts.pop()
        path     = '/'.join(parts)
        old_path = os.path.join(self.root,path,filename)
        # New name for the file/folder after the renaming. e.g. "icon.png"
        #new      = request.args.get('new')
        new_path = os.path.join(self.root,path,new)
        if filename:
           look = new_path
        else:
           oldname = parts.pop()
           path     = '/'.join(parts)
           new_path = os.path.join(self.root,path,new)
        if (self.is_safe_path(new_path)):
           os.rename(old_path, new_path)
           response = FileManagerResponse(self.root,new_path,self.mountname)
           response.set_response()
           return jsonify(response.response)
        else:
           return self.fileManagerError()
#===============================================================================
    def move(self,old,new):
        ''' Moves file or folder to specified directory. '''
        # Relative path of the source file/folder to move. e.g. "/images/logo.png"
        #old      = request.args.get('old').lstrip("/")
        print('old:'+old)
        old = os.path.join(self.root,old)
        print('with path old:'+old)
        parts    = old.split('/')
        filename = parts.pop()
        path     = '/'.join(parts)
        old_path = os.path.join(self.root,old)
        # New relative path for the file/folder after the move. e.g. "/images/target/"
        #new      = request.args.get('new').lstrip("/")
        new = os.path.join(self.root,new)
        print('new:'+new)
        new_path = os.path.join(self.root,new,filename)
        if (self.is_safe_path(new_path)):
           shutil.move(old_path,new_path)
           if filename:
              look = new_path
           else:
              look = new_path+'/'+parts[len(parts)-1]
           response = FileManagerResponse(self.root,look,self.mountname)
           response.set_response()
           return jsonify(response.response)
        else:
           return self.fileManagerError()
#===============================================================================
    def copy(self,old,new):
        ''' Copies file or folder to specified directory. '''
        # Relative path of the source file/folder to move. e.g. "/images/logo.png"
        #old      = request.args.get('old').lstrip("/")
        print('copy old:'+old+' new:'+new)
        parts    = old.split('/')
        filename = parts.pop()
        path     = '/'.join(parts)
        old_path = os.path.join(self.root,old)
        # New relative path for the file/folder after the move. e.g. "/images/target/"
        #new      = request.args.get('new').lstrip("/")
        new_path = os.path.join(self.root,new,filename)
        if (self.is_safe_path(new_path)):
           shutil.copyfile(old_path, new_path)
           response = FileManagerResponse(self.root,new_path,self.mountname)
           response.set_response()
           return jsonify(response.response)
        else:
           return self.fileManagerError()
#===============================================================================
    def savefile(self,file,content):
        ''' Overwrites the content of the specific file to the "content" request parameter value. '''
        #file    = request.form.get('path').lstrip("/")
        #content = request.form.get('content')
        path    = os.path.join(self.root,file)
        if (self.is_safe_path(path)):
           if os.path.isfile(path):
               with open(path, "w") as fh:
                   fh.write(content)
           response = FileManagerResponse(self.root,path,self.mountname)
           response.set_response()
           return jsonify(response.response)
        else:
           return self.fileManagerError()
#===============================================================================
    #def delete(self):
    def delete(self,file):
        ''' Deletes an existed file or folder. '''
        #file    = request.args.get('path').lstrip("/")
        path    = os.path.join(self.root,file)
        response = FileManagerResponse(self.root,path,self.mountname)
        response.set_response()
        if (self.is_safe_path(path)):
           if os.path.isdir(path):
               shutil.rmtree(path)
           elif os.path.isfile(path):
               os.remove(path)
           return jsonify(response.response)
        else:
           return self.fileManagerError()
#===============================================================================
    #def download(self):
    def download(self,file):
        ''' Downloads requested file or folder.
        The download process consists of 2 requests:
        1. Ajax GET request. Perform all checks and validation. Should return
        file/folder object in the response data to proceed.
        2. Regular GET request. Response headers should be properly configured
        to output contents to the browser and start download.
        Thus the implementation of download method should differentiate requests
        by type (ajax/regular) and act accordingly. '''
        #file     = request.args.get('path').lstrip("/")
        path     = os.path.join(self.root,file)
        mimetype, encoding = MimeTypes().guess_type(path)
        parts    = file.split('/')
        filename = parts.pop()
        # Check for AJAX request
        if request.is_xhr:
            response = FileManagerResponse(self.root,path,self.mountname)
            response.set_response()
            return jsonify(response.response)
        else:
           if (self.is_safe_path(path)):
              return send_file(path,
                         mimetype=mimetype,
                         attachment_filename=filename,
                         as_attachment=True)
           else:
              return self.fileManagerError()
#===============================================================================
    def getimage(self,file):
        ''' Outputs the content of image file to browser. '''
        #file      = request.args.get('path').lstrip("/")
        path      = os.path.join(self.root,file)
        mime_type, encoding = mimetypes.guess_type(path)
        if (self.is_safe_path(path)):
           return send_file(path, mimetype=mime_type)
        else:
           return self.fileManagerError()
#===============================================================================
    def readfile(self,file):
        ''' Outputs the content of requested file to browser. Intended to read
        file requested via connector path (not absolute path), for files located
        outside document root folder or hosted on remote server. '''
        #file     = request.args.get('path').lstrip("/")
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
        print('SUMMARIZE NOT IMPLEMENTED')
        return self.fileManagerError()
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
    def extract(self,source,target):
        print('extract source:'+source+' target:'+target)
        ''' Extract files and folders from zip archive.
        Note that only the first-level of extracted files and folders are returned
        in the response. All nested files and folders should be omitted for correct
        displaying at the client-side. '''
        #source          = request.form.get('source').lstrip("/")
        source_path     = os.path.join(self.root,source)
        #target          = request.form.get('target').lstrip("/")
        target_path     = os.path.join(self.root,target)
        if (self.is_safe_path(source_path) and self.is_safe_path(target_path)):
           with ZipFile(source_path,"r") as zip_ref:
               zip_ref.extractall(target_path)
           data            = []
           for file in os.listdir(target_path):
               path        = os.path.join(target_path,file)
               response    = FileManagerResponse(self.root,path,self.mountname)
               response.set_data()
               data.append(response.data)
           results         = {}
           results['data'] = data
           return jsonify(results)
        else:
           return self.fileManagerError()
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

    def is_dir(self,filename):
        path = os.path.join(self.root,filename)
        return os.path.isdir(path)

    def get_dir_list(self,dirname):
        entries=[]
        dirname = os.path.join(self.root,dirname)
        #dirname=dirname.strip("/")
        for thefile in os.listdir(dirname):
           e = {}
           e['name']=thefile
           #e['type']=
           entries.append(e)
        return entries

    def copy_to_tmp(self,src,tempname):
        source_path     = os.path.join(self.root,src)
        shutil.copyfile(source_path, tempname)

    def copy_from_tmp(self,tempname,dst):
        dest_path     = os.path.join(self.root,dst)
        shutil.copyfile(tempname, dest_path)
