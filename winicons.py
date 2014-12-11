import os
import shutil
import requests
import zlib

def get_icon(exe):
    shutil.rmtree("extract")
    print("extracting",exe)
    os.system('ResourcesExtract.exe /Source "%s" /DestFolder "extract" /ExtractIcons 1 /ExtractCursors 0 /FileExistMode 1 /OpenDestFolder 0'%exe)
    for f in os.listdir("extract"):
        if "MAINICON" in f:
            print ("extracted",f)
            return "extract/"+f
    for f in os.listdir("extract"):
        if ".ico" in f:
            print ("extracted2",f)
            return "extract/"+f
    return "icons/none.png"

crcmap = {}
f = open("gbaroms.dat")
lines = f.read().split("\n")
f.close()
for l in lines:
    if l.strip():
        fields = l.split(";")
        crc = fields[8].lstrip("0")
        num = fields[0]
        crcmap[crc] = num

def read_crc(filename):
    return "%X"%(zlib.crc32(open(filename,"rb").read()) & 0xFFFFFFFF)

def get_gba(gba):
    shutil.rmtree("extract")
    os.mkdir("extract")
    print("extracting",gba)
    #get crc
    crc = read_crc(gba)
    print(crc)
    #get rom number
    num = crcmap[crc]
    print(num)
    #get icon path
    r = requests.get("http://www.emuparadise.me/GBA/boxart/%s.jpg"%num)
    f = open("extract/icon.png","wb")
    f.write(r.content)
    f.close()
    return "extract/icon.png"