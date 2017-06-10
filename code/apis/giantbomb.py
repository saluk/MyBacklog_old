import sys
import os
import json
import difflib
import requests
import time
from code.resources import icons
import xml.etree.cElementTree as etree

apikey = "a4232ea9aea488fe5fe90f3a7c89c33439d569e2"

gameep = "http://www.giantbomb.com/api/game/%(game_id)s/"
gamesearchep = "http://www.giantbomb.com/api/search/"

headers = {
    'User-Agent': 'MyBacklog Game tracker and launcher v1.0',
    'From': 'saluk64007@gmail.com'
}

def get_game_info(id,cache_root="."):
    time.sleep(0.5)
    r = requests.get(gameep%{"game_id":id},params={"format":"json","api_key":apikey},headers=headers)
    json = r.json()
    return json

def find_game(name,cache_root="."):
    print("looking for game",name)
    time.sleep(0.5)
    r = requests.get(gamesearchep,params={"query":'"'+name+'"',"api_key":apikey,"resources":"game","format":"json"},headers=headers)
    result = r.json()
    #print(result)
    list = result.get("results",[])
    if not list:
        print("failed to find game")
        return
    #print("found candidates",list)
    def match(n1,n2):
        n1=n1.lower()
        n2=n2.lower()
        score = difflib.SequenceMatcher(None,n1,n2).ratio()
        if n2.startswith(n1):
            score += 0.1
        return score
    print( [(li["name"],match(name,li["name"])) for li in list] )
    list.sort(key=lambda li: -match(name,li["name"]))
    return list[0]
    
class giantbomb:
    def __init__(self,app):
        self.app = app
        if not os.path.exists(self.app.config["root"]+"/cache/giantbomb"):
            os.mkdir(self.app.config["root"]+"/cache/giantbomb")
    def update_game_data(self,game):
        game_platforms = []
        sources = []
        for source in game.sources:
            if source["source"] == "giantbomb":
                continue
            sources.append(source)
        game_in_db = find_game(game.name,self.app.config["root"])
        if not game_in_db:
            print("NO GAME FOR",game.name)
            return
        info = get_game_info(game_in_db["id"],self.app.config["root"])
        if not info.get("results",[]):
            print("GAME HAS NO INFO")
            return
        #print(info)
        game.sources[:] = sources
        game.sources.append({"source":"giantbomb","id":game_in_db["id"],"name":info["results"].get("name","")})
        print(game.images)
        if info["results"].get("image",None):
            for key in ["icon_url"]+list(info["results"]["image"].keys()):
                if key not in info["results"].get("image",[]):
                    continue
                url = info["results"]["image"][key]
                game.images[:] = [img for img in game.images if img["url"]]
                if "icon" not in [img["size"] for img in game.images]:
                    print("adding image",url)
                    game.images.append({"size":"icon","url":url})
                    #cache image for later
                    time.sleep(0.5)
                    icons.icon_for_game(game,32,{},self.app.config["root"])
                else:
                    print("has icon")
        else:
            for img in info["results"].get("images",[]):
                for key in ["icon_url"]+list(img.keys()):
                    if key not in img:
                        continue
                    url = img[key]
                    game.images[:] = [img for img in game.images if img["url"]]
                    if "icon" not in [img["size"] for img in game.images]:
                        print("adding image",url)
                        game.images.append({"size":"icon","url":url})
                    else:
                        print("has icon")
        print(game.images)
        print("UPDATED")

if __name__=="__main__":
    if len(sys.argv) < 2:
        sys.argv = ["x","far cry 3"]
    print (json.dumps(get_game_info(find_game(sys.argv[1])["id"]),indent=4))
