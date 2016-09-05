#!python3
import json
import os
import sys
import difflib
import requests
import xml.etree.cElementTree as etree

gamelistep = "http://thegamesdb.net/api/GetGamesList.php"
gameep = "http://thegamesdb.net/api/GetGame.php"

platforms = {"snes":"Super Nintendo (SNES)","pc":"pc","none":"pc"}

as_list = ["Genres","Images"]
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

def to_dict(tree):
    #d = {"genre":[]}
    d = {}
    lists = {}
    for child in tree:
        v = get_value(child)
        if child.tag in ["Genres","Images"]:
            if child.tag not in lists:
                lists[child.tag] = []
            lists[child.tag].append(v)
        else:
            d[child.tag] = v
    d.update(lists)
    return d

def find_game(name,platform,cache_root=""):
    ckey = cache_root+"/cache/thegamesdb/fg"+name.replace(" ","_").replace(":","-").replace("/","_slsh_")
    if os.path.exists(ckey):
        xml = open(ckey).read()
    else:
        r = requests.get(gamelistep,params={"name":'"'+name+'"',"platform":platforms[platform]})
        xml = r.text
        with open(ckey,"w",encoding="utf8") as f:
            f.write(xml)
    root = etree.XML(xml)
    list = [to_dict(game) for game in root]
    if not list:
        return None
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

def get_game_info(game_id,cache_root=""):
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
        #print(info)
        game.sources[:] = sources
        game.sources.append({"source":"thegamesdb","id":game_in_db["id"]})
        print(game.images)
        for image in info["Game"]["Images"]:
            if "boxart" in image:
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
    print (repr(get_game_info(find_game("Kyuuyaku Megami Tensei","snes")["id"])).encode("utf8"))
    #print (get_game_info(find_game("lands of lore ii","pc")["id"]))
    #print (get_game_info(find_game("lands of lore 2","pc")["id"]))
