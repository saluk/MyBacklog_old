import os
import requests

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon,QPixmap
from code.resources import extract_icons

def path_to_icon(game,filecache_root):
    if game.icon_url:
        return filecache_root+"/cache/icons/"+game.icon_url.replace("http","").replace("https","").replace(":","").replace("/",""),"download",game.icon_url
    elif game.get_exe():
        exe_path = game.get_exe()
        return filecache_root+"/cache/icons/"+exe_path.replace("http","").replace("https","").replace(":","").replace("/","").replace("\\",""),"extract",exe_path
    elif game.get_gba():
        gba_path = game.get_gba()
        return filecache_root+"/cache/icons/"+gba_path.replace("http","").replace(":","").replace("/","").replace("\\",""),"gba",gba_path
    else:
        return filecache_root+"/icons/blank.png",None,""

def icon_in_cache(game,cache,filecache_root):
    fpath,mode,url = path_to_icon(game,filecache_root)
    if fpath in cache:
        return QIcon(cache[fpath])
    return None

def icon_for_game(game,size,icon_cache,filecache_root):
    fpath,mode,url = path_to_icon(game,filecache_root)
    if mode == "download":
        if not os.path.exists(fpath):
            print("Download icon:",game.icon_url)
            r = requests.get(game.icon_url)
            f = open(fpath,"wb")
            f.write(r.content)
            f.close()
    elif mode == "extract":
        if not os.path.exists(fpath):
            print("Extract icon:",url.encode("ascii","backslashreplace"))
            p = extract_icons.get_icon(url,filecache_root)
            import shutil
            if p:
                shutil.copy(p,fpath)
    elif mode == "gba":
        if not os.path.exists(fpath):
            print("Download gba icon:",url)
            p = extract_icons.get_gba(url)
            import shutil
            if p:
                shutil.copy(p,fpath)
    if os.path.exists(fpath) and not fpath+"_%d"%size in icon_cache:
        qp = QPixmap(fpath)
        if not qp.isNull():
            qp = qp.scaled(size,size,Qt.IgnoreAspectRatio,Qt.SmoothTransformation)
        icon_cache[fpath] = qp
    return icon_in_cache(game,icon_cache,filecache_root)