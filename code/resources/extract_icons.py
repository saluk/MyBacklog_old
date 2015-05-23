import os
import shutil
import zlib

import requests

from code.systems import *


def get_icon(exe,filecache_root):
    if not EXTRACT_ICONS:
        return "icons/none.png"
    if os.path.exists(filecache_root+"/extract"):
        shutil.rmtree(filecache_root+"/extract")
    print("extracting",exe.encode("utf8"))
    os.system('tools\\ResourcesExtract.exe /Source "%s" /DestFolder "%s" /ExtractIcons 1 /ExtractCursors 0 /FileExistMode 1 /OpenDestFolder 0'%(exe,(filecache_root+"/extract").replace("/",os.path.sep)))
    for f in os.listdir(filecache_root+"/extract"):
        if "MAINICON" in f:
            return filecache_root+"/extract/"+f
    for f in os.listdir(filecache_root+"/extract"):
        if ".ico" in f:
            return filecache_root+"/extract/"+f
    return "icons/none.png"

crcmap = {}
#f = open("gbaroms.dat")
#lines = f.read().split("\n")
#f.close()
for l in []:#lines:
    if l.strip():
        fields = l.split(";")
        crc = fields[8].lstrip("0")
        num = fields[0]
        crcmap[crc] = num

def read_crc(filename):
    return "%X"%(zlib.crc32(open(filename,"rb").read()) & 0xFFFFFFFF)

def get_gba(gba):
    if not os.path.exists("gba"):
        return "icons/none.png"
    if os.path.exists("extract"):
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
