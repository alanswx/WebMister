# MiSTer Web UI

The Web UI has a few parts. 

+ Installer that pulls in packages from github
+ Filemanager style UI that allows you to upload and download off of the SD Card. It also allows mounting some emulated file systems.

## API

` /api/load_manifest `

returns the json file that describes the cores and supporting files

` /api/get_local_files_for_core `

Parameter: 
* core - name of the core

looks on the local SD card and tells you about the files that are installed for a single core

` /api/get_local_files_for_all_cores `

looks on the local SD card and tells you about the files that are installed for all cores

` /api/download_url `

Parameters:
* url - source url
* dest - destination on the SD Card

Downloads the URL to the destination on the device. This is used to install cores, and supporting files.

` /api/convert_rom `

Parameter:
* core - name of the core to convert the rom 

Using the mame rom name (ie: pacman.zip) from the manifest.json it converts it into the MiSTer format.



## Setup

### Requirements

* Python >= `3.x`
* NodeJS >= `8.x`

* sudo apt-get install python3-parted

### Client

From the `client` directory run the following:

* `npm install`
* `npm run build`

### Server

From the root directory run the following:

* `pip install -r requirements.txt`
* `python server.py  --host=0.0.0.0`

## Usage

Navigate to `localhost:5000`


## Notes
 `sudo losetup --show -f -P /home/alans/mister/InstallerMister/misterinst/ao486/win95.vhd`
 `sudo mount /dev/loop1p1 mountpoint`
