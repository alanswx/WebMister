# MiSTer Web UI

The Web UI has a few parts. 

+ Installer that pulls in packages from github
+ Filemanager style UI that allows you to upload and download off of the SD Card. It also allows mounting some emulated file systems.


## Setup

### Requirements

* Python >= `3.x`
* NodeJS >= `8.x`

### Client

From the `client` directory run the following:

* `npm install`
* `npm run build`

### Server

From the root directory run the following:

* `pip install -r requirements.txt`
* `python server.py`

## Usage

Navigate to `localhost:5000`
