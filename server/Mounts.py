import parted
import mmap
import os
import subprocess
import time
import re


class Mounts:
    mounts = []
    def __init__(self):
       print('init')
       self.mounts = []
       self.loadmounts()


    def _call_mount(self,mountcommand):
       try:
           mount_output = subprocess.check_output(mountcommand.split(' '), stderr=subprocess.STDOUT)
       except subprocess.CalledProcessError as e:
#        hmount_output = (True, e)
         mount_output = e
       return mount_output

    def _call_unmount(self,path):
       print("_call_unmount:"+path)
       try:
           unmount_output = subprocess.check_output(['fusermount','-u',path], stderr=subprocess.STDOUT)
       except subprocess.CalledProcessError as e:
#        hmount_output = (True, e)
         unmount_output = e
         print(e)

       print(unmount_output)
       return unmount_output

    def loadmounts(self):
        mountstr=self._call_mount("mount")
        mountstr=mountstr.decode('utf-8')
        lines=mountstr.split("\n")
        p = re.compile('(.*) on (.*) type (.*) (\(.*\))')
        for line in lines:
           matches = p.match(line)
           if matches:
               device=matches.group(1)
               mount=matches.group(2)
               mounttype=matches.group(3)
               # AJS - should check to see if this mount is within our filepath
               if mounttype=='fuse':
                   print(device,mount,mounttype)
                   print(line)
                   m={}
                   m['cmd']=''
                   m['name']=mount
                   m['filename']=device
                   self.mounts.append(m)

    def mountfile(self,filename):
        filename_full=os.path.abspath(filename)
        namepart, file_extension = os.path.splitext(filename_full)
        try:
            os.mkdir(namepart)
        except Exception as e:
            pass
        mountcommand = self.lookupMountCommand(filename)
        if (mountcommand):
            self._call_mount(mountcommand)        
            print("mountfile: ["+filename+"]")
            print(mountcommand)
            m = {}
            m['cmd']=mountcommand
            m['name']=namepart
            m['filename']=filename_full
            self.mounts.append(m)
            print(self.mounts)

    def unmount(self,filename):
        print('unmount:'+filename)
        filename_full=os.path.abspath(filename)
        namepart, file_extension = os.path.splitext(filename_full)
        print(self._call_unmount(namepart))
        time.sleep(0.1) 
        try:
            os.rmdir(namepart)
        except Exception as e:
            print(e)

        print("unmount")
        print(filename)
      
    def unmountfile(self,filename):
        # remove from self.mounts
        newmounts=[]
        for m in self.mounts:
           print(m)
           if (m['name']!=filename):
              newmounts.append(m)
           else:
              self.unmount(m['filename'])
        self.mounts = newmounts

    def unmountall(self):
        print('unmountall')
        for m in self.mounts:
           print(m)
           self.unmount(m['filename'])
        self.mounts = []

    def lookupPartitions(self,device_name):
        result = []
        try:
            dev = parted.getDevice(device_name)
            disk = parted.newDisk(dev)
            for p in disk.partitions:
              if p.fileSystem:
                fs = {}
                fs['filename']=device_name
                fs['number']=p.number
                fs['name']=p.name
                fs['type']=p.fileSystem.type
                fs['startBlock']=p.fileSystem.geometry.start
                fs['sectorsize']=dev.sectorSize
                fs['startOffset']=dev.sectorSize*p.fileSystem.geometry.start
                result.append(fs)
        except parted.DiskException as e:
             fs = {}
             fs['error']="DiskException"
             fs['desc']=str(e)
             result.append(fs)
             #print('DiskException lookupPartitions exception: '+str(e))
        except parted.IOException as e:
             fs = {}
             fs['error']="file not found"
             fs['desc']=str(e)
             result.append(fs)
        except Exception as e:
             fs = {}
             fs['error']="error"
             fs['desc']=str(e)
             result.append(fs)
             #print(e)
             #print('lookupPartitions exception: '+str(e))
        
        return result

    
    def lookupMountCommand(self,filename):
        # see if this is a partitioned file system image
        filename_full=os.path.abspath(filename)
        namepart, file_extension = os.path.splitext(filename_full)
        #print(filename_full,namepart,file_extension)
        command=''
        result = self.lookupPartitions(filename_full)
        for partition in result:
            try:
                if (partition['type']=='hfs'):
                    command = "fusehfs "+filename_full+" "+namepart
                    return command
                elif (partition['type']=='fat16' or partition['type']=='fat32'):
                    command = "fusefat -o rw+ --offset="+str(partition['startOffset'])+" "+filename_full+" "+namepart
                    return command
            except Exception as e:
                #print (e)
                pass
        return None

        # check for CBM file
        #"cbmfsmount"
        result = self.looksLikeCBM(filename_full)
        if result[0]==True:
            command = "cbmfsmount "+filename_full+" "+namepart
            return command

        result = self.looksLikeZIP(filename_full)
        if result[0]==True:
            command = "fuse-zip "+filename_full+" "+namepart
            return command

        #print("no valid partition")
        return None
    

    def looksLikeZIP(self,filename):
        zip=False
        cbmType="Unknown"
        cbmVolName="Unknown"

        zipExtensions = [ '.zip','.ZIP']
        # should we look for the file extension?
        namepart, file_extension = os.path.splitext(filename)
        #print(namepart,file_extension)
        if file_extension in zipExtensions:
            return (True,file_extension,'')
        else:
            return (False,'','')

    def lookupCBMVolumeName(self,filename,BAM,HEADER,LENGTH):
        string = "Unknown"
        with open(filename, "r+b") as f:
            mm = mmap.mmap(f.fileno(), 0)
            ba=mm[BAM+HEADER:BAM+HEADER+LENGTH]
            #print (ba)
            st = bytearray()
            for b in ba:
                if b != 0xa0 :
                    st.append(b)
            string=st.decode('ascii')
            #print(string)
            mm.close()
            return string
        

    def looksLikeCBM(self,filename):
        cbm=False
        cbmType="Unknown"
        cbmVolName="Unknown"

        cbmExtensions = [ '.d64', '.D64', '.d71', '.D71', '.d80','.D80', '.d81', '.D81', '.d82','.D82']
        # should we look for the file extension?
        namepart, file_extension = os.path.splitext(filename)
        #print(namepart,file_extension)

        if file_extension not in cbmExtensions:
            return (cbm,cbmType,cbmVolName)
        # grab the file size
        try:
            statinfo = os.stat(filename)
        except Exception as e:
            print (e)
            return (cbm,cbmType,cbmVolName)

        disk_image_size= statinfo.st_size
    
        if disk_image_size==174848 or disk_image_size==175531:
            cbmVolName=self.lookupCBMVolumeName(filename,0x16500,0x90,16)
            cbm=True
            cbmType="D64"
        elif disk_image_size==196608 or disk_image_size==197376:
            cbm=True
            cbmType="D64"
        elif disk_image_size==351062 or disk_image_size==349696:
            cbm=True
            cbmType="D71"
            cbmVolName=self.lookupCBMVolumeName(filename,0x16500,0x90,16)
        elif disk_image_size==533248:
            cbm=True
            cbmType="D80"
            cbmVolName=self.lookupCBMVolumeName(filename,0x44E00,6,16)
        elif disk_image_size==819200 or disk_image_size==822400 :
            cbm=True
            cbmType="D81"
            cbmVolName=self.lookupCBMVolumeName(filename,0x61800,4,16)
        elif disk_image_size==1066496:
            cbm=True
            cbmType="D82"
            cbmVolName=self.lookupCBMVolumeName(filename,0x44E00,6,16)

        return (cbm,cbmType,cbmVolName)






if __name__ == "__main__":
    mount = Mounts()
    exit()
    devices = []
    devices.append("files/boot.vhd")
    devices.append("/home/alans/mister/InstallerMister/misterinst/ao486/win95.vhd")
    devices.append("../../LinuxFuseHFSworking/Disk605.dsk")
    devices.append("../../fusefat.old/new.vhd")
    devices.append("../../fusefat.old/test.vhd")
    devices.append("../../fusefat.old/file.img")
    devices.append("wrong../../fusefat.old/file.img")
    devices.append("../../cbmfs-1.0/atari.d64")
    devices.append("../../cbmfs-1.0/AZTEC.D64")
    devices.append("altered_beast.d81")
    devices.append("altered_beast.zip")

    for d in  devices:
        print(d)
        print(mount.lookupMountCommand(d))
        #result = mount.lookupPartitions(d)
        #print(result)
        #print(d)
        #result = mount.looksLikeCBM(d)
        #print(d)
        #print(result)
        #result =mount.looksLikeZIP(d)
        #print(result)


    #mount.mountfile("files/boot.vhd")
    mount.mountfile("../../LinuxFuseHFS/new.vhd")
    time.sleep(3)
    mount.unmountall()

