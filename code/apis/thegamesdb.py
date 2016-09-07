#!python3
import json
import os
import sys
import difflib
import requests
import urllib
import xml.etree.cElementTree as etree

gamelistep = "http://thegamesdb.net/api/GetGamesList.php"
gameep = "http://thegamesdb.net/api/GetGame.php"

platforms = {'saturn': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/17.png', 'sys': 'Sega Saturn'}], 'snes': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/6.png', 'sys': 'Super Nintendo (SNES)'}], 'zxspectrum': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4913.png', 'sys': 'Sinclair ZX Spectrum'}], 'neogeocd': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4956.png', 'sys': 'Neo Geo CD'}], 'gameandwatch': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4950.png', 'sys': 'Game &amp; Watch'}], 'sg1000': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4949.png', 'sys': 'SEGA SG-1000'}], 'odyssey': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4927.png', 'sys': 'Magnavox Odyssey 2'}], 'vita': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/39.png', 'sys': 'Sony Playstation Vita'}], 'ps3': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/12.png', 'sys': 'Sony Playstation 3'}], 'gba': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/5.png', 'sys': 'Nintendo Game Boy Advance'}], 'atari': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/22.png', 'sys': 'Atari 2600'}, {'img': 'http://thegamesdb.net/banners/platform/consoleart/26.png', 'sys': 'Atari 5200'}, {'img': 'http://thegamesdb.net/banners/platform/consoleart/27.png', 'sys': 'Atari 7800'}, {'img': 'http://thegamesdb.net/banners/platform/consoleart/4943.png', 'sys': 'Atari 800'}], 'neogeo': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/24.png', 'sys': 'Neo Geo'}], 'fmtowns': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4932.png', 'sys': 'FM Towns Marty'}], '3d0': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/25.png', 'sys': '3DO'}], 'xbone': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4920.png', 'sys': 'Microsoft Xbox One'}], 'cdi': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4917.png', 'sys': 'Philips CD-i'}], 'amstrad': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4914.png', 'sys': 'Amstrad CPC'}], 'tgcd': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4955.png', 'sys': 'TurboGrafx CD'}], 'genesis': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/18.png', 'sys': 'Sega Genesis'}], 'wii': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/9.png', 'sys': 'Nintendo Wii'}], 'ps4': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4919.png', 'sys': 'Sony Playstation 4'}], 'appleii': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4942.png', 'sys': 'Apple II'}], 'virtualboy': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4918.png', 'sys': 'Nintendo Virtual Boy'}], 'nes': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4936.png', 'sys': 'Famicom Disk System'}, {'img': 'http://thegamesdb.net/banners/platform/consoleart/7.png', 'sys': 'Nintendo Entertainment System (NES)'}], 'atarist': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4937.png', 'sys': 'Atari ST'}], 'gamecube': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/2.png', 'sys': 'Nintendo GameCube'}], 'lynx': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4924.png', 'sys': 'Atari Lynx'}], 'ps2': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/11.png', 'sys': 'Sony Playstation 2'}], 'nuon': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4935.png', 'sys': 'Nuon'}], 'pcfx': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4930.png', 'sys': 'PC-FX'}], 'segacd': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/21.png', 'sys': 'Sega CD'}], 'amiga': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4911.png', 'sys': 'Amiga'}, {'img': 'http://thegamesdb.net/banners/platform/consoleart/4947.png', 'sys': 'Amiga CD32'}], 'vectrex': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4939.png', 'sys': 'Vectrex'}], 'gb': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4.png', 'sys': 'Nintendo Game Boy'}], 'msx': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4929.png', 'sys': 'MSX'}], 'psp': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/13.png', 'sys': 'Sony PSP'}], 'sms': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/35.png', 'sys': 'Sega Master System'}], 'colecovision': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/31.png', 'sys': 'Colecovision'}], 'none': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/37.png', 'sys': 'Mac OS'}, {'img': 'http://thegamesdb.net/banners/platform/consoleart/1.png', 'sys': 'PC'}], '3ds': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4912.png', 'sys': 'Nintendo 3DS'}], 'fairchild': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4928.png', 'sys': 'Fairchild Channel F'}], 'dreamcast': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/16.png', 'sys': 'Sega Dreamcast'}], 'commodore': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4946.png', 'sys': 'Commodore 128'}, {'img': 'http://thegamesdb.net/banners/platform/consoleart/40.png', 'sys': 'Commodore 64'}, {'img': 'http://thegamesdb.net/banners/platform/consoleart/4945.png', 'sys': 'Commodore VIC-20'}], 'ngage': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4938.png', 'sys': 'N-Gage'}], 'wonderswancolor': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4926.png', 'sys': 'WonderSwan Color'}], 'xbox360': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/15.png', 'sys': 'Microsoft Xbox 360'}], 'xbox': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/14.png', 'sys': 'Microsoft Xbox'}], 'psx': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/10.png', 'sys': 'Sony Playstation'}], 'tg16': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/34.png', 'sys': 'TurboGrafx 16'}], 'intellivision': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/32.png', 'sys': 'Intellivision'}], '32x': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/33.png', 'sys': 'Sega 32X'}], 'x68000': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4931.png', 'sys': 'X68000'}], 'gamegear': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/20.png', 'sys': 'Sega Game Gear'}], 'arcade': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/23.png', 'sys': 'Arcade'}], 'gbc': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/41.png', 'sys': 'Nintendo Game Boy Color'}], 'neogeopocket': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4922.png', 'sys': 'Neo Geo Pocket'}, {'img': 'http://thegamesdb.net/banners/platform/consoleart/4923.png', 'sys': 'Neo Geo Pocket Color'}], 'n64': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/3.png', 'sys': 'Nintendo 64'}], 'wiiu': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/38.png', 'sys': 'Nintendo Wii U'}], 'wonderswan': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/4925.png', 'sys': 'WonderSwan'}], 'jaguar': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/28.png', 'sys': 'Atari Jaguar'}, {'img': 'http://thegamesdb.net/banners/platform/consoleart/29.png', 'sys': 'Atari Jaguar CD'}], 'nds': [{'img': 'http://thegamesdb.net/banners/platform/consoleart/8.png', 'sys': 'Nintendo DS'}]}

as_list = ["Genre","Image","Platform","fanart"]
def get_value(child):
    v = {}
    if child.attrib:
        v = dict(child.attrib)
    if len(child):
        v.update(to_dict(child))
    if child.text:
        if child.text.replace("\\n","\n").strip():
            v["_value"] = child.text.replace("\\n","\n").strip()
    if len(v.keys())==1:
        if "_value" in v:
            return v["_value"]
        elif "_children" in v:
            return v["_children"]
    return v

def to_dict(tree,parent=None):
    #d = {"genre":[]}
    d = {}
    lists = {}
    for child in tree:
        v = get_value(child)
        if child.tag in as_list:
            if child.tag not in lists:
                lists[child.tag] = []
            lists[child.tag].append(v)
        else:
            d[child.tag] = v
    d.update(lists)
    return d
    
def get_platforms():
    r = requests.get("http://thegamesdb.net/api/GetPlatformsList.php")
    platforms = to_dict(etree.XML(r.text))["Platforms"]["Platform"]
    for platform in platforms:
        r = requests.get("http://thegamesdb.net/api/GetPlatform.php?id="+str(platform["id"]))
        platform = to_dict(etree.XML(r.text))
        img = [platform["Platform"][0]["Images"][key] for key in platform["Platform"][0]["Images"] if "consoleart" in key]
        if img:
            print(platform["Platform"][0]["Platform"][0],",",platform["baseImgUrl"]+img[0])
def _process_filedb():
    """Run from apis folder, will download system images and print a dict to copy into platforms above"""
    d = {}
    f = open("thegamesdb_platform_map.txt")
    lines = f.read().split("\n")
    for l in lines:
        k,s,img = l.split(",")
        k = k.strip()
        if k not in d:
            d[k] = []
        d[k].append({"sys":s.strip(),"img":img.strip()})
        
    #save system images
    for k in d:
        print (k)
        img = d[k][0]["img"].strip()
        if [ 1 for ext in ["png","jpg"] if os.path.exists("..\..\icons\%s.%s"%(k,ext)) ]:
            print(" skipping")
            continue
        print(" downloading")
        ext = img.rsplit(".",1)[1]        
        with open("..\..\icons\%s.%s"%(k,ext),"wb") as f:
            response = requests.get(img,stream=True)
            for block in response.iter_content(1024):
                f.write(block)
    
    #platforms dict
    print(d)
        

def find_game(name,platform,cache_root="..\.."):
    for platform in platforms[platform]:
        print("search for platform",platform["sys"])
        ckey = cache_root+"/cache/thegamesdb/fg"+name.replace(" ","_").replace(":","-").replace("/","_slsh_")
        if os.path.exists(ckey):
            print("from cache")
            xml = open(ckey).read()
        else:
            print("look up",ckey)
            print({"name":'"'+name+'"',"platform":platform["sys"]})
            r = requests.get(gamelistep,params={"name":'"'+name+'"',"platform":platform["sys"]})
            xml = r.text
            print(xml)
            with open(ckey,"w",encoding="utf8") as f:
                f.write(xml)
        root = etree.XML(xml)
        list = [to_dict(game) for game in root]
        if not list:
            continue
        #find best match
        def match(n1,n2):
            n1=n1.lower()
            n2=n2.lower()
            score = difflib.SequenceMatcher(None,n1,n2).ratio()
            if n2.startswith(n1):
                score += 0.1
            return score
        #print ( [(li["GameTitle"],match(name,li["GameTitle"])) for li in list] )
        for i in range(len(list)):
            list[i]["sort_index"] = i
        #list.sort(key=lambda li: (-match(name,li["GameTitle"]),li["sort_index"]))
        return list[0]

def get_game_info(game_id,cache_root="..\.."):
    ckey = cache_root+"/cache/thegamesdb/gi"+str(game_id)
    if os.path.exists(ckey):
        xml = open(ckey).read()
    else:
        r = requests.get(gameep,params={"id":game_id})
        xml = r.text
        with open(ckey,"w",encoding="utf8") as f:
            f.write(xml)
    root = etree.XML(xml)
    return to_dict(root)
    
class thegamesdb:
    def __init__(self,app):
        self.app = app
        if not os.path.exists(self.app.config["root"]+"/cache/thegamesdb"):
            os.mkdir(self.app.config["root"]+"/cache/thegamesdb")
    def update_game_data(self,game):
        game_platforms = []
        sources = []
        for source in game.sources:
            if source["source"] == "thegamesdb":
                continue
            sources.append(source)
            if source["source"] in platforms:
                game_platforms.append(source["source"])
        if not game_platforms:
            print("NO PLATFORMS")
            return
        game_in_db = find_game(game.name,game_platforms[0],self.app.config["root"])
        if not game_in_db:
            print("NO GAME FOR",game.name,game_platforms[0])
            return
        info = get_game_info(game_in_db["id"],self.app.config["root"])
        if "Game" not in info:
            print("GAME HAS NO INFO")
            return
        print(info)
        game.sources[:] = sources
        game.sources.append({"source":"thegamesdb","id":game_in_db["id"]})
        print(game.images)
        if "boxart" in info["Game"]["Images"]:
            image = info["Game"]["Images"]
            #FIXME bad code - need to simplify and put in game as a function
            game.images[:] = [img for img in game.images if img["url"]]
            if "icon" not in [img["size"] for img in game.images]:
                print("adding image",image)
                game.images.append({"size":"icon","url":info["baseImgUrl"]+image["boxart"]["_value"]})
            else:
                print("has icon")
        print(game.images)
        print("UPDATED")

if __name__=="__main__":
    print (get_game_info(find_game("God of War","ps2")["id"]))
    #get_platforms()
    #_process_filedb()
    #print (repr(get_game_info(find_game("Kyuuyaku Megami Tensei","snes")["id"])).encode("utf8"))
    #print (get_game_info(find_game("lands of lore ii","pc")["id"]))
    #print (get_game_info(find_game("lands of lore 2","pc")["id"]))
