import os
import subprocess
import sys

from flask import Flask, request, send_from_directory
from jinja2 import Markup, PackageLoader, Environment, FileSystemLoader, ChoiceLoader
dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')
app = Flask(__name__)
os.environ['HOME']='/var/www'

from File import bluePrint as fileBluePrint
app.register_blueprint(fileBluePrint)

@app.route("/")
def hello():
      return "Hello World!"

@app.route("/debug")
def debug():
     try:
       os.environ['HOME']='/var/www'
       hmount_output=''
       hfsfilename='/media/fat/web/WebMister/files/boot.vhd'
       env = dict(os.environ)
       env['HOME']='/var/www'
       try:
           hmount_output = subprocess.check_output(['hmount', hfsfilename], stderr=subprocess.STDOUT,shell=False)
           #hmount_output = subprocess.check_output(['hmount', hfsfilename], stderr=subprocess.STDOUT,env=env,shell=False)
           #hmount_output = subprocess.check_output(['strace','hmount', hfsfilename], stderr=subprocess.STDOUT)
           try:
               hmount_output = hmount_output.decode('utf-8')
           except:
               hmount_output = hmount_output.decode('macroman') # Just in case
               # It will fail ungracefully here if neither encoding works
       except subprocess.CalledProcessError as e:
#        hmount_output = (True, e)
#           sys.exit('_call_hmount error: {0}'.format(e.output,))
         hmount_output=('_call_hmount error: {0}'.format(e.output,))
         return hmount_output
     except Exception as e: 
      return "Hello World!"+str(e)
     return hmount_output

@app.route("/another")
def another():
    hmount_output=''
    try:
      hfsfilename='/media/fat/web/WebMister/files/boot.vhd'
      #hmount_output = subprocess.check_output(['/usr/bin/hmount'], stderr=subprocess.STDOUT, shell=True)
      hmount_output = subprocess.check_output(['/usr/bin/hmount', hfsfilename], stderr=subprocess.STDOUT, shell=True)
      return hmount_output
      #return 'in try' 
    except Exception as e: 
 
      return "Hello World!"+str(e)+hmount_output
      #return "in hello"

if __name__ == "__main__":
    app.run(debug=True)
