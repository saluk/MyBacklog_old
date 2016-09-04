import os
import requests

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon,QPixmap
from code.resources import extract_icons

def path_to_icon(game,filecache_root,size="icon"):
    url = ""
    if size=="icon": 
        url = game.icon_url
    if size=="logo": 
        url = game.logo_url
    if url:
        return filecache_root+"/cache/icons/"+url.replace("http","").replace("https","").replace(":","").replace("/",""),"download",url
    elif game.get_exe():
        exe_path = game.get_exe()
        return filecache_root+"/cache/icons/"+exe_path.replace("http","").replace("https","").replace(":","").replace("/","").replace("\\",""),"extract",exe_path
    elif game.get_gba():
        gba_path = game.get_gba()
        return filecache_root+"/cache/icons/"+gba_path.replace("http","").replace(":","").replace("/","").replace("\\",""),"gba",gba_path
    else:
        return "icons/blank.png",None,""

def icon_in_cache(game,cache,filecache_root,size="icon"):
    fpath,mode,url = path_to_icon(game,filecache_root,size)
    if fpath in cache:
        return QIcon(cache[fpath])
    return None

def icon_for_game(game,size,icon_cache,filecache_root,category="icon"):
    fpath,mode,url = path_to_icon(game,filecache_root,category)
    if mode == "download":
        if not os.path.exists(fpath):
            print("Download icon:",url)
            r = requests.get(url)
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
        qp = QPixmap(fpath.replace("/",os.path.sep))
        if not qp.isNull():
            if category == "icon": mode = Qt.IgnoreAspectRatio
            if category == "logo": mode = Qt.KeepAspectRatio
            qp = qp.scaled(size,size,mode,Qt.SmoothTransformation)
        icon_cache[fpath] = qp
    return icon_in_cache(game,icon_cache,filecache_root,category)