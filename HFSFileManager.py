#!/usr/bin/python3
import os
import sys
import shutil
import mimetypes
import datetime
from mimetypes import MimeTypes
from zipfile import ZipFile
from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
from .HFSFileManagerResponse import *
from io import BytesIO
import subprocess
import re

PATTERNFILE = re.compile('^(\d+)\s+(\w+)\s+(.{4}/.{4})\s+(\d+)\s+(\d+)\s+(\w{3}\s{1,2}\d{1,2}\s{1,2}\d{2}:{0,1}\d{2})\s(".*")(\**)$')
PATTERNDIR = re.compile('^(\d+)\s+(\w+)\s+(\d+\sitems*)\s+(\w{3}\s{1,2}\d{1,2}\s{1,2}\d{2}:{0,1}\d{2})\s(".*"):$')

DEBUG=False

class HFSFileManager:
    # Path to your files root
    root = ''
    mountname = ''
    def __init__(self,proot,name):
       self.root=proot
       self.mountname=name
       self._call_hmount(self.root)

   
    def _call_hmount(self,hfsfilename):
       # Calls hmount with path to HFS volume. Returns output of command,
       # which includes volume name and other information.
       try:
           hmount_output = subprocess.check_output(['hmount', hfsfilename],
                                                stderr=subprocess.STDOUT)
           try:
               hmount_output = hmount_output.decode('utf-8')
           except:
               hmount_output = hmount_output.decode('macroman') # Just in case
               # It will fail ungracefully here if neither encoding works
       except subprocess.CalledProcessError as e:
#        hmount_output = (True, e)
           sys.exit('_call_hmount error: {0}'.format(e.output,))
       return hmount_output

    def _call_hvol(self):
       # Calls hmount with path to HFS volume. Returns output of command,
       # which includes volume name and other information.
       try:
           hmount_output = subprocess.check_output(['hvol', self.root],
                                                stderr=subprocess.STDOUT)
           try:
               hmount_output = hmount_output.decode('utf-8')
           except:
               hmount_output = hmount_output.decode('macroman') # Just in case
               # It will fail ungracefully here if neither encoding works
       except subprocess.CalledProcessError as e:
#        hmount_output = (True, e)
           sys.exit('_call_hmount error: {0}'.format(e.output,))
       return hmount_output

    def _call_hls(self,path):
         # Calls hls twice to obtain output for generating fileobjects
         # Returns output of command unformatted.
         try:
             # NOTE: hls arguments (from man page)
             # The order listed is to ensure consistent formatting for parsing.
             # -1 Output is formatted so entry appears on a single line.
             # -a All files and directories and "invisible" files are shown.
             # -c Sort and display by creation date (hls_cre_output only)
             # -m Sort and display by modification date (hls_mod_output only)
             # -i Show catalog IDs for each entry.
             # -l Display entries in long format, including entry type,
             #    flags, file type and reator, resource bytes, data bytes,
             #    date of creation or modification, and pathname.
             # -Q Cause all filenames to be enclosed in double-quotes and
             #    special/non-printable characters to be properly escaped.
             # -R Recursively descent into and display each directory contents.
             # -U Do not sort directory contents
             # -F Cause certain output filenames to be followed by
             #    a single-character flag (e.g., colon for directories and
             #    asterisk for applications.)
             # -N Cause all filenames to be output verbatim without any
             #    escaping or question mark substitution.
             print('==HLS==:',path)
             path=':'+path
             if path:
                 hls_cre_output = subprocess.check_output(['hls', '-1ailQF',path])
                 #hls_cre_output = subprocess.check_output(['hls', '-1ailQ',path])
             else:
                 hls_cre_output = subprocess.check_output(['hls', '-1ailQF'])
                 #hls_cre_output = subprocess.check_output(['hls', '-1ailQ'])
             #hls_mod_output = subprocess.check_output(['hls', '-1amilQRUFN'])

             # NOTE: Decode using macroman
             hls_cre_output = hls_cre_output.decode('macroman')
             #hls_mod_output = hls_mod_output.decode('macroman')

         except subprocess.CalledProcessError as e:
     #        sys.exit('_call_hls error: {0}'.format(e.output,))
             return (True, e)
         if DEBUG:
             with open('DEBUG_hfs2dfxml.txt', 'w') as debugfile:
                 _debug_output = hls_cre_output.split('\n')
                 for dbg in _debug_output:
                     debugfile.write(dbg)
                     debugfile.write('\n')
         return hls_cre_output

    def _parse_hls_mod(self,hls_mod_raw):
         # Takes raw hls input (assumes file modification times).
         # Returns a dictionary to correlate with additional hls output.
         hls_mod= []
         hls_mod_raw = hls_mod_raw.split('\n')
         for hls_mod_line in hls_mod_raw:
             if hls_mod_line.startswith(':'):
                 continue
             elif hls_mod_line == '\n':
                 continue
             elif hls_mod_line == '':
                 continue

             hls_mod_line = hls_mod_line.strip()
             parse_file_mod = re.match(PATTERNFILE, hls_mod_line)
             parse_dir_mod = re.match(PATTERNDIR, hls_mod_line)

             fs= {}
             if parse_file_mod and not parse_dir_mod:
                 fs['mod_cnid'] = parse_file_mod.group(1)
                 fs['mod_mdate'] = parse_file_mod.group(6)
                 fs['mod_filename'] = parse_file_mod.group(7)
                 fs['mod_nametype'] = parse_file_mod.group(2)
                 fs['mod_mactype'] = parse_file_mod.group(3)
                 fs['mod_datasize'] = parse_file_mod.group(4)
                 fs['type']='file'
             elif not parse_file_mod and parse_dir_mod:
                 fs['mod_cnid'] = parse_dir_mod.group(1)
                 fs['mod_mdate'] = parse_dir_mod.group(4)
                 fs['mod_filename'] = parse_dir_mod.group(5)
                 fs['mod_nametype'] = parse_dir_mod.group(2)
                 fs['type']='dir'
             else:
                 sys.exit('_parse_hls_mod error: Unexpected line format.\n' +
                     '|{0}|'.format(hls_mod_line))
                 # NOTE: Should be a logger event, probably?

             fs['mod_filename']=fs['mod_filename'].replace("\\ "," ")
             fs['mod_filename']=fs['mod_filename'].lstrip("\"").strip("\"")
             hls_mod.append(fs)
         return hls_mod

    def _call_hrename(self,fromname,toname):
       #hfsfilename="\":"+hfsfilename+"\""
       fromname=":"+fromname
       toname=":"+toname
       try:
           hrename_output = subprocess.check_output(['hrename', fromname,toname],
                                                stderr=subprocess.STDOUT,shell=False)
           try:
               hrename_output = hrename_output.decode('utf-8')
           except:
               hrename_output = hrename_output.decode('macroman') # Just in case
               # It will fail ungracefully here if neither encoding works
       except subprocess.CalledProcessError as e:
#        hrename_output = (True, e)
           sys.exit('_call_copy error: {0}'.format(e.output,))
       return hrename_output

    def _call_hcopy(self,hfsfilename):
       #hfsfilename="\":"+hfsfilename+"\""
       hfsfilename=":"+hfsfilename
       try:
           hcopy_output = subprocess.check_output(['hcopy', hfsfilename,'-'],
                                                stderr=subprocess.STDOUT,shell=False)
           try:
               hcopy_output = hcopy_output.decode('utf-8')
           except:
               hcopy_output = hcopy_output.decode('macroman') # Just in case
               # It will fail ungracefully here if neither encoding works
       except subprocess.CalledProcessError as e:
#        hcopy_output = (True, e)
           sys.exit('_call_copy error: {0}'.format(e.output,))
       return hcopy_output

    def _call_hcopy_fromfile(self,tempname,hfsfilename):
       hfsfilename=":"+hfsfilename
       try:
           hcopy_output = subprocess.check_output(['hcopy','-m', tempname,hfsfilename],
                                                stderr=subprocess.STDOUT)
           try:
               hcopy_output = hcopy_output.decode('utf-8')
           except:
               hcopy_output = hcopy_output.decode('macroman') # Just in case
               # It will fail ungracefully here if neither encoding works
       except subprocess.CalledProcessError as e:
#        hcopy_output = (True, e)
           sys.exit('_call_copy error: {0}'.format(e.output,))
       return hcopy_output
    def _call_hcopy_tofile(self,hfsfilename,output):
       hfsfilename=":"+hfsfilename
       try:
           hcopy_output = subprocess.check_output(['hcopy','-m', hfsfilename,output],
                                                stderr=subprocess.STDOUT,shell=False)
           try:
               hcopy_output = hcopy_output.decode('utf-8')
           except:
               hcopy_output = hcopy_output.decode('macroman') # Just in case
               # It will fail ungracefully here if neither encoding works
       except subprocess.CalledProcessError as e:
#        hcopy_output = (True, e)
           sys.exit('_call_copy error: {0}'.format(e.output,))
       return hcopy_output

    def _call_hmkdir(self,hfsfilename):
       #hfsfilename="\":"+hfsfilename+"\""
       hfsfilename=":"+hfsfilename
       hmkdir_output=''
       try:
           hmkdir_output = subprocess.check_output(['hmkdir', hfsfilename],
                                                stderr=subprocess.STDOUT,shell=False)
           try:
               hmkdir_output = hmkdir_output.decode('utf-8')
           except:
               hmkdir_output = hmkdir_output.decode('macroman') # Just in case
               # It will fail ungracefully here if neither encoding works
       except subprocess.CalledProcessError as e:
#        hmkdir_output = (True, e)
         #  sys.exit('_call_hmkdir error: {0}'.format(e.output,))
         print('_call_hmkdir error: {0}'.format(e.output,))
       return hmkdir_output
    def _call_hdel(self,hfsfilename):
       #hfsfilename="\":"+hfsfilename+"\""
       hfsfilename=":"+hfsfilename
       hdel_output=''
       try:
           hdel_output = subprocess.check_output(['hdel', hfsfilename],
                                                stderr=subprocess.STDOUT,shell=False)
           try:
               hdel_output = hdel_output.decode('utf-8')
           except:
               hdel_output = hdel_output.decode('macroman') # Just in case
               # It will fail ungracefully here if neither encoding works
       except subprocess.CalledProcessError as e:
#        hdel_output = (True, e)
         #  sys.exit('_call_hdel error: {0}'.format(e.output,))
         print('_call_hdel error: {0}'.format(e.output,))
       return hdel_output
    def _call_hrmdir(self,hfsfilename):
       #hfsfilename="\":"+hfsfilename+"\""
       hfsfilename=":"+hfsfilename
       hrmdir_output=''
       try:
           hrmdir_output = subprocess.check_output(['hrmdir', hfsfilename],
                                                stderr=subprocess.STDOUT,shell=False)
           try:
               hrmdir_output = hrmdir_output.decode('utf-8')
           except:
               hrmdir_output = hrmdir_output.decode('macroman') # Just in case
               # It will fail ungracefully here if neither encoding works
       except subprocess.CalledProcessError as e:
#        hrmdir_output = (True, e)
         #  sys.exit('_call_hrmdir error: {0}'.format(e.output,))
         print('_call_hrmdir error: {0}'.format(e.output,))
       return hrmdir_output
     


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
    def getinfo(self,hfsfilename):
        ''' Provides data for a single file. '''
        self._call_hvol()
        hls_mod_raw=self._call_hls(hfsfilename)
        hls_d=self._parse_hls_mod(hls_mod_raw)
        print('===readfile===: '+content)
        response    = HFSFileManagerResponse(self.root,hfsfilename,self.mountname,hls_d[0])
        response.set_response()
        return jsonify(response.response)
#===============================================================================
    def readfolder(self,folder):
        ''' Provides list of file and folder objects contained in a given directory. '''
        #folder          = request.args.get('path').lstrip("/")
        print('readfolder('+folder+')')
        folder=folder.replace("/",":")
        self._call_hvol()
        hls_mod_raw=self._call_hls(folder)
        hls_d=self._parse_hls_mod(hls_mod_raw)
        print('--HLS--:')
        print(hls_d)
        folder=folder.replace(":","/")
        folder_path     = os.path.join(self.root,folder)
        data            = []
        for e in hls_d:
           fname = e['mod_filename']
           fname_path     = os.path.join(self.root,fname)
           if fname_path!=folder_path:
               path        = os.path.join(folder_path,e['mod_filename'].lstrip(":"))
           else:
               path        = folder_path
           response    = HFSFileManagerResponse(self.root,path,self.mountname,e)
           response.set_data()
           data.append(response.data)
        results         = {}
        results['data'] = data
        if (len(data)==1):
           tmp = {}
           tmp['data']=data[0]

           return jsonify(tmp)
        return jsonify(results)
#===============================================================================
    def addfolder(self,path,name):
        ''' Creates a new directory on the server within the given path. '''
        #folder_path = os.path.join(self.root,path,name)
        folder_path = os.path.join(path,name)
        folder=folder_path.replace("/",":")
        self._call_hvol()
        self._call_hmkdir(folder)
        return self.readfolder(folder_path)
#===============================================================================
    def upload(self):
        print('UPLOAD NOT IMPLEMENTED')
        return self.fileManagerError()
        ''' Uploads a new file to the given folder.
            Upload form in the RichFilemanager passes an uploaded file. The name of the
            form element is defined by upload.paramName option in Configuration options
            ("files[]" by default). '''
        path = request.form.get('path').lstrip("/")
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
        parts    = old.split('/')
        filename = parts.pop()
        path     = '/'.join(parts)
        old_path = os.path.join(path,filename)
        # New name for the file/folder after the renaming. e.g. "icon.png"
        #new      = request.args.get('new')
        new_path = os.path.join(path,new)
        if filename:
           look = new_path
        else:
           oldname = parts.pop()
           path     = '/'.join(parts)
           new_path = os.path.join(path,new)
        self._call_hvol()
        self._call_hrename(old_path, new_path)
        new_path= new_path.lstrip(":")
        return self.readfolder(new_path)
#===============================================================================
    def move(self):
        ''' Moves file or folder to specified directory. '''
        print('MOVE NOT IMPLEMENTED')
        return self.fileManagerError()
        # Relative path of the source file/folder to move. e.g. "/images/logo.png"
        old      = request.args.get('old').lstrip("/")
        parts    = old.split('/')
        filename = parts.pop()
        path     = '/'.join(parts)
        old_path = os.path.join(self.root,old)
        # New relative path for the file/folder after the move. e.g. "/images/target/"
        new      = request.args.get('new').lstrip("/")
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
    def copy(self):
        print('COPY NOT IMPLEMENTED')
        return self.fileManagerError()
        ''' Copies file or folder to specified directory. '''
        # Relative path of the source file/folder to move. e.g. "/images/logo.png"
        old      = request.args.get('old').lstrip("/")
        parts    = old.split('/')
        filename = parts.pop()
        path     = '/'.join(parts)
        old_path = os.path.join(self.root,old)
        # New relative path for the file/folder after the move. e.g. "/images/target/"
        new      = request.args.get('new').lstrip("/")
        new_path = os.path.join(self.root,new,filename)
        if (self.is_safe_path(new_path)):
           shutil.copyfile(old_path, new_path)
           response = FileManagerResponse(self.root,new_path,self.mountname)
           response.set_response()
           return jsonify(response.response)
        else:
           return self.fileManagerError()
#===============================================================================
    def savefile(self):
        print('SAVEFILE NOT IMPLEMENTED')
        return self.fileManagerError()
        ''' Overwrites the content of the specific file to the "content" request parameter value. '''
        file    = request.form.get('path').lstrip("/")
        content = request.form.get('content')
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
    def recursive_delete(self,file):
        if self.is_dir(file):
            # get list of everything in dir 
            dirlist=self.get_dir_list(file)
            for d in dirlist:
              newf=os.path.join(file,d['name'])
              self.recursive_delete(newf)
            # rmdir the empty directory
            file=file.replace("/",":")
            self._call_hrmdir(file)
        else:
            file=file.replace("/",":")
            self._call_hdel(file)

    def delete(self,file):
        ''' Deletes an existed file or folder. '''
        self._call_hvol()
        self.recursive_delete(file)
        return self.readfolder(file)
#===============================================================================
    #def download(self):
    def download(self,file):
        print('DOWNLOAD NOT IMPLEMENTED')
        return self.fileManagerError()
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
    def getimage(self):
        print('GETIMAGE NOT IMPLEMENTED')
        return self.fileManagerError()
        ''' Outputs the content of image file to browser. '''
        file      = request.args.get('path').lstrip("/")
        path      = os.path.join(self.root,file)
        mime_type, encoding = mimetypes.guess_type(path)
        if (self.is_safe_path(path)):
           return send_file(path, mimetype=mime_type)
        else:
           return self.fileManagerError()
#===============================================================================
    def readfile(self,hfsfilename):
        ''' Outputs the content of requested file to browser. Intended to read
        file requested via connector path (not absolute path), for files located
        outside document root folder or hosted on remote server. '''
        self._call_hvol()
        hfsfilename=hfsfilename.replace("/",":")
        content= self._call_hcopy(hfsfilename)
        mimetype="text/plain"
        print('===readfile===: '+content)
        #file     = request.args.get('path').lstrip("/")
        #path     = os.path.join(self.root,file)
        #mimetype, encoding = MimeTypes().guess_type(path)
        #parts = file.split('/')
        #filename = parts.pop()
        #if (self.is_safe_path(path)):
        return send_file(BytesIO(bytearray(content,"utf-8")),
                     mimetype=mimetype,
                     attachment_filename=hfsfilename,
                     as_attachment=True)
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
    def extract(self):
        print('EXTRACT NOT IMPLEMENTED')
        return self.fileManagerError()
        ''' Extract files and folders from zip archive.
        Note that only the first-level of extracted files and folders are returned
        in the response. All nested files and folders should be omitted for correct
        displaying at the client-side. '''
        source          = request.form.get('source').lstrip("/")
        source_path     = os.path.join(self.root,source)
        target          = request.form.get('target').lstrip("/")
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
        filename=filename.replace("/",":")
        self._call_hvol()
        print('hfs is_dir:'+filename)
        hls_mod_raw=self._call_hls(filename)
        if hls_mod_raw.find("Not a directory")>=0:
            print('not a dir?')
            print(hls_mod_raw)
            return False
        hls_d=self._parse_hls_mod(hls_mod_raw)
        fname = filename
        fname = filename.strip(":")
        fname = ':'+fname
        print('fname:'+fname)
        print(hls_d)
        if len(hls_d)==1:
           print('do these match?:')
           print(hls_d[0]['mod_filename'])
           print(fname)
        if len(hls_d)==1 and hls_d[0]['mod_filename']==fname and hls_d[0]['type']!='dir':
          print('we got a match')
          return False
        else:
          return True
    def get_dir_list(self,dirname):
        dirname=dirname.replace("/",":")
        self._call_hvol()
        hls_mod_raw=self._call_hls(dirname)
        hls_d=self._parse_hls_mod(hls_mod_raw)
        entries=[]
        for entry in hls_d:
           e = {}
           e['name']=entry['mod_filename']
           entries.append(e)
        return entries

    def copy_to_tmp(self,src,tempname):
        src=src.replace("/",":")
        self._call_hvol()
        self._call_hcopy_tofile(src,tempname)

    def copy_from_tmp(self,tempname,dst):
        dst=dst.replace("/",":")
        print('copy_from_tmp:'+tempname+' '+dst)
        self._call_hvol()
        output=self._call_hcopy_fromfile(tempname,dst)
        print(output)

