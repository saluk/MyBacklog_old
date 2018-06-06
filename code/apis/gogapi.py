#!python3
import time
import requests
import re
import os
from .. import games
import json

def get_gog_games_from_google():
    """Access google, search for www.gog.com/game/(game_id), return list of (game_id,game_name)"""
    url = "http://www.google.com/search"
    start = 0
    while 1:
        r = requests.get(url,params={"q":"site:gog.com/game/","start":start})
        t = r.text
        f = open("google.html","w",encoding="utf8")
        f.write(t)
        f.close()
        links = [x[0] for x in re.findall('q\=\http\:\/\/www\.gog\.com\/game\/(.*?)(\&|\?)',t)]
        for l in links:
            gog_games[l] = {"gogid":l}
        next = re.findall('<a(.*?)>.*?Next.*?\<\/a>',t)
        if next:
            next = re.findall('href="(.*?)"',next[0])
            if next:
                url = "http://www.google.com"+next[0]
                time.sleep(500)
                continue
        return
        
def get_gog_games_from_web():
    s = requests.Session()
    r = s.get("https://www.gog.com")
    buk = re.findall('<input.*?name="buk".*?>',r.text)
    buk = re.findall('value="(.*?)"',buk[0])
    buk = buk[0]
    print (buk)
    r = s.post("https://secure.gog.com/login",
        params={
            "log_email":"",
            "log_password":"",
            "redirectOk":"/",
            "submitForLoginForm":"Log me in",
            "unlockSettings":"0",
            "buk":buk
        })
    f = open("gog.html","w",encoding="utf8")
    f.write(r.text)
    f.close()
    r = s.get("https://secure.gog.com/account/games/shelf")
    f = open("gog_shelf.html","w",encoding="utf8")
    f.write(r.text)
    f.close()

"""
<div class="shelf_game" data-gameindex="dracula_trilogy" data-gameid="1207659251" data-orderid="3LKULVG353S" data-background="/upload/images/2013/07/50f3b525242c1a0129eabcbf5a6951c2e3f42194.jpg" data-title="dracula trilogy anuman interactive anuman interactive adventure pointandclick horror">
"""
def get_gog_games_html(html):
    from bs4 import BeautifulSoup
    gog_games = {}
    f = open(html)
    t = f.read()
    f.close()
    soup = BeautifulSoup(t)
    games = soup.find_all(lambda tag: tag.has_attr("data-gameindex"))
    for g in games:
        d = {}
        d["gameindex"] = g['data-gameindex']
        d["gameid"] = g['data-gameid']
        d["orderid"] = g['data-orderid']
        d["background"] = g['data-background']
        d["titlekeys"] = g['data-title']
        for image in g.find_all('img'):
            d["icon"] = image['src']
        gog_games[d["gameindex"]] = d
    return gog_games

class Browser:
    def __init__(self):
        self.cookies = {}
        self.headers = {"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Encoding":"gzip, deflate","Accept-Language":"en-us,ko;q=0.7,en;q=0.3",
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:28.0) Gecko/20100101 Firefox/28.0",
            "Referer":"https://www.humblebundle.com/",
            "X-Requested-With":"XMLHttpRequest"}
    def post(self,url,datax={},params={}):
        self.json = {}
        self.text = ""
        answer = requests.post(url,data=datax,params=params,cookies=self.cookies,headers=self.headers,allow_redirects=True)
        self.answer = answer
        self.cookies.update(answer.cookies)
        try:
            self.json = answer.json()
        except:
            pass
        try:
            self.text = answer.text
            self.url = answer.url
        except:
            pass
    def get(self,url,params={},cache=False,cache_root=""):
        self.json = {}
        self.text = ""
        if cache:
            if not os.path.exists(cache_root+"/cache/gogapi"):
                os.mkdir(cache_root+"/cache/gogapi")
        cache_url = cache_root+"/cache/gogapi/"+url.replace(":","").replace("/","").replace("?","QU").replace("&","AN")
        if not cache or not os.path.exists(cache_url):
            answer = requests.get(url,params=params,cookies=self.cookies,headers=self.headers)
            self.cookies.update(answer.cookies)
            try:
                self.json = answer.json()
            except:
                pass
            try:
                self.text = answer.text
                self.url = answer.url
            except:
                pass
            if cache:
                f = open(cache_url,"w")
                f.write(json.dumps({"json":self.json,"text":self.text,"url":self.url}))
                f.close()
        else:
            f = open(cache_url)
            d = json.loads(f.read())
            f.close()
            self.json = d["json"]
            self.text = d["text"]
            self.url = d["url"]

#Format:
"""{"products":[
    {"isGalaxyCompatible":true,
    "tags":[],
    "id":1207666333,
    "availability":{"isAvailable":true,"isAvailableInAccount":true},
    "title":"Dead State",
    "image":"\/\/images-3.gog.com\/b71936e5a70a388f5e3db8c729c7e46c2278e43904c1978ab968240efbefbadf",
    "url":"\/game\/dead_state",
    "worksOn":{"Windows":true,"Mac":false,"Linux":false},
    "category":"Role-playing",
    "rating":34,
    "isComingSoon":false,
    "isMovie":false,
    "isGame":true,
    "slug":"dead_state",
    "updates":0,
    "isNew":true,
    "dlcCount":0,
    "isHidden":false}
]}"""

class BadAccount(Exception):
    pass

class Gog:
    def __init__(self,app,username,password):
        self.app = app
        self.username = username
        self.password = password
        
    def get_shelf(self,multipack,gog_cookie_info):
        if not self.username or not self.password:
            raise BadAccount()
        print(time.time())
        
        
        
        b = Browser()
        #Try cookies
        logged_in = False
        #shelf: https://www.gog.com/account/getFilteredProducts?hiddenFlag=0&mediaType=1&page=2&sortBy=date_purchased&totalPages=7
        try:
            b.headers["User-Agent"] = gog_cookie_info["user_agent"]
            b.cookies = gog_cookie_info["cookies"]
            print("accessing gog with cookies:",b.cookies)
            
            import sqlite3
            conn = sqlite3.connect(self.app.config["root"]+"/cache/browser/Cookies")
            for cookie in conn.execute("select * from cookies"):
                b.cookies[cookie[2]] = cookie[3]
            print(b.cookies)
            conn.close()
            b.get("https://www.gog.com/account/getFilteredProducts",params={
                "hiddenFlag":1,
                "mediaType":1,
                "page":1,
                "sortBy":"date_purchased"
                })
            print(b.json)
            assert b.json["totalProducts"]
            print("Logged in")
            logged_in = True
        except:
            print("Not logged in")
            import traceback
            traceback.print_exc()
            pass

        if not logged_in:
            raise BadAccount()
            
        self.app.log.write("gog logged in: success")

        url = "https://www.gog.com/account/getFilteredProducts?mediaType=1&page=%(page)s&sortBy=date_purchased"

        imported_games = []
        packs = {}
        page = 1
        while 1:
            self.app.log.write("gog download page: %s"%page)
            print("getting page",page)
            b.get(url%{"page":page},cache=False,cache_root=self.app.config["root"])
            for game_data in b.json["products"]:
                if not game_data["isGame"]:
                    continue
                #print(game_data)
                gameid = str(game_data["slug"])
                gameid2 = str(game_data["id"])
                gamename = game_data["title"]
                #Add a formatter to the image to get the right size
                #_392 = big icon
                #_bg_1120.jpg = background of game page
                gameicon = "http:"+game_data["image"].replace("\\/","/")+"_392.jpg"
                genre = game_data["category"].lower()
                game = games.Game(name=gamename,icon_url=gameicon,import_date=games.now(),genre=genre)
                game.sources = [{"source":"gog","id":gameid,"id2":gameid2,"gog_data":game_data}]

                if gameid in multipack:
                    if gameid not in packs:
                        package = games.Game(name=gamename,icon_url=gameicon,import_date=games.now())
                        package.sources = [{"source":"gog","id":gameid,"id2":gameid2}]
                        package.package_data = {
                            "type":"bundle",
                            "contents":[],
                            "source_info":package.create_package_data()
                        }
                        packs[gameid] = package
                        package.generate_gameid()
                        imported_games.append(package)
                    package = packs[gameid]
                    for subgamename in multipack[gameid]:
                        subgame = game.copy()
                        subgame.name = subgamename
                        print("packaging",subgamename,"into",subgame.gameid,subgame.create_package_data())
                        subgame.package_data = {
                            "type":"content",
                            "parent":{"gameid":package.gameid,"name":package.name},
                            "source_info":subgame.create_package_data()
                        }
                        subgame.generate_gameid()
                        package.package_data["contents"].append({"gameid":subgame.gameid,"name":subgame.name})
                        imported_games.append(subgame)
                else:
                    game.generate_gameid()
                    imported_games.append(game)

            if page == b.json["totalPages"]:
                break
            page += 1
        return imported_games

if __name__ == "__main__":
    better_get_shelf()
    for game in import_gog():
        print (game.name)
