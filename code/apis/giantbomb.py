import sys
import json
import difflib
import requests
import xml.etree.cElementTree as etree

apikey = "a4232ea9aea488fe5fe90f3a7c89c33439d569e2"

gameep = "http://www.giantbomb.com/api/game/%(game_id)s/"
gamesearchep = "http://www.giantbomb.com/api/search/"

def get_game_info(id):
    r = requests.get(gameep%{"game_id":id},params={"format":"json","api_key":apikey})
    json = r.json()
    return json

def find_game(name):
    r = requests.get(gamesearchep,params={"query":'"'+name+'"',"api_key":apikey,"resources":"game","format":"json"})
    list = r.json()["results"]
    def match(n1,n2):
        n1=n1.lower()
        n2=n2.lower()
        score = difflib.SequenceMatcher(None,n1,n2).ratio()
        if n2.startswith(n1):
            score += 0.1
        return score
    print( [(li["name"],match(name,li["name"])) for li in list] )
    list.sort(key=lambda li: -match(name,li["name"]))
    print( list[0] )
    return list[0]

if __name__=="__main__":
    if len(sys.argv) < 2:
        sys.argv = ["x","far cry 3"]
    print (json.dumps(get_game_info(find_game(sys.argv[1])["id"]),indent=4))
