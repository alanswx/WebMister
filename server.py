import json
import subprocess
import sys
import os
import urllib.request

from flask import Flask, send_from_directory, request

from server.File import bluePrint as fileBluePrint

from server.Cores import Cores
from server.ArcadeRom import ArcadeRom


DIR = sys.path[0]
DIR = os.path.abspath(DIR)
MISTERDIR = os.path.join(DIR,"../InstallerMister/misterinst")
MISTERDIR = os.path.join(DIR,"../install_files/goodimage/image/")
MISTERDIR = os.path.abspath(MISTERDIR)

fileBluePrint.MISTERDIR=MISTERDIR

#
# The Core class deals with installed files on disk
#
core = Cores(DIR,MISTERDIR)
arcadeRom= ArcadeRom(DIR,MISTERDIR)

#
# setup flask and point /static to the right place
app = Flask(__name__,static_url_path='/static',static_folder='server/static')

#
# if we are running lighttpd it sets the HOME incorrectly, we fix it and use
# this to know if we should add /files onto the front of the FileManager paths
#
if os.environ['HOME']=='/root':
   os.environ['HOME']='/var/www'
   app.register_blueprint(fileBluePrint)
else:
   app.register_blueprint(fileBluePrint, url_prefix='/files')


@app.route("/")
def serve():
    return send_from_directory('client/dist', 'index.html')

@app.route('/fonts/<path:path>')
def send_fonts(path):
    return send_from_directory('client/src/app/fonts', path)

@app.route("/app.bundle.js")
def serve_app_bundle():
    return send_from_directory('client/dist', 'app.bundle.js')


@app.route("/app.bundle.css")
def serve_css_bundle():
    return send_from_directory('client/dist', 'app.bundle.css')


@app.route("/api/load_manifest")
def load_manifest():
    with open(os.path.join(DIR, 'server/manifest.json'), 'r') as f:
        d = json.load(f)
    return json.dumps(d)


@app.route("/api/get_local_files_for_core")
def local_files_for_core():
    print(MISTERDIR)
    corename = request.args.get('core')
    return json.dumps(core.update_core_from_disk(corename))

@app.route("/api/get_local_files_for_all_cores")
def local_files_for_all_cores():
    return json.dumps(core.update_cores_from_disk())

@app.route("/api/download_url")
def download_url():
    url= request.args.get('url')
    dest= request.args.get('dest')
    file_name = os.path.join(MISTERDIR,dest)
    result = {}
    #print(file_name) 
    #print(MISTERDIR) 
    #print(os.path.abspath(file_name))
    if os.path.abspath(file_name).startswith(MISTERDIR):
      try:
       dirname = os.path.dirname(file_name)
       print(dirname) 
       try:
          os.makedirs(dirname)
       except:
          pass
       fn,headers = urllib.request.urlretrieve(url,file_name)
       # we might look inside the structure and report a more machine readable error
       result = { "message": "OK" }
      except Exception as e:
       result = { "message": str(e) }
       print(e)
    else:
       result = { "message": "Invalid Path: "+dest}
     
    return json.dumps(result)
    
@app.route("/api/convert_rom")
def convert_rom():
    core = request.args.get('core')
    result=arcadeRom.convertRom(core)
    return json.dumps(result)

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')
