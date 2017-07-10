import os
import requests

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QIcon,QPixmap
except:
    pass
    
try:
    import pygame
except:
    pass

from code.resources import extract_icons

headers = {
    'User-Agent': 'MyBacklog Game tracker and launcher v1.0',
    'From': 'saluk64007@gmail.com'
}

def path_to_icon(game,filecache_root,category="icon"):
    url = ""
    if category=="icon": 
        url = game.icon_url
    if category=="logo": 
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

def icon_in_cache(game,size,cache,filecache_root,category="icon",imode="qt"):
    fpath,mode,url = path_to_icon(game,filecache_root,category)
    if (fpath,size) in cache:
        if imode=="qt":
            return QIcon(cache[(fpath,size)])
        return cache[(fpath,size)]
    return None

def icon_for_game(game,size,icon_cache,filecache_root,category="icon",imode="qt"):
    cur = icon_in_cache(game,size,icon_cache,filecache_root,category,imode)
    if cur:
        return cur
        
    fpath,mode,url = path_to_icon(game,filecache_root,category)
    if mode == "download":
        if not os.path.exists(fpath):
            print("Download icon:",url)
            r = requests.get(url,headers=headers)
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
    if os.path.exists(fpath) and not (fpath,size) in icon_cache:
        if imode=="qt":
            mode = ""
            with open(fpath.replace("/",os.path.sep),"rb") as f:
                head = str(f.read(20))
                if "JFIF" in head:
                    mode = "JPG"
            qp = QPixmap(fpath.replace("/",os.path.sep),mode)
            if not qp.isNull():
                if category == "icon": mode = Qt.IgnoreAspectRatio
                if category == "logo": mode = Qt.KeepAspectRatio
                qp = qp.scaled(size,size,mode,Qt.SmoothTransformation)
            icon_cache[(fpath,size)] = qp
        else:
            try:
                icon_cache[(fpath,size)] = pygame.transform.scale(pygame.image.load(fpath),[size,size])
            except:
                pass
    return icon_in_cache(game,size,icon_cache,filecache_root,category,imode)