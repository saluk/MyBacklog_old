#!python3
import time
import requests
import re
from .. import data
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
def import_gog(multipack={}):
    packs = {}
    games = []
    gog_games = get_gog_games_html("cache/mygog_shelf.html")
    for key in gog_games:
        g = gog_games[key]
        multi = multipack.get(g["gameindex"],[""])
        for g2 in multi:
            name = g["gameindex"]
            if g2:
                name = g2
            name = " ".join([x.capitalize() for x in name.replace("_"," ").split(" ")])
            id = g["gameindex"]
            if g2:
                id = id+"."+g2.replace(" ","_")
                if not g["gameindex"] in packs:
                    package = data.Game(name=" ".join([x.capitalize() for x in g["gameindex"].split("_")]),source="gog",gogid=g["gameindex"],is_package=1)
                    packs[package.gameid] = package
                    games.append(package)
            game = data.Game(name=name,source="gog",gogid=g["gameindex"],icon_url=g["icon"],packageid=g2.replace(" ","_"))
            games.append(game)
    return games

class Browser:
    def __init__(self):
        self.cookies = {}
        #self.cookies = {"guc_al":"0","sessions_gog_com":"0","__utma":"95732803.1911890316.1399672018.1399672018.1399672018.1","__utmb":"95732803.5.9.1399672201295","__utmz":"95732803.1399672018.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)"}
        self.headers = {"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Encoding":"gzip, deflate","Accept-Language":"en-us,ko;q=0.7,en;q=0.3",
"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:28.0) Gecko/20100101 Firefox/28.0",
"Referer":"http://www.gog.com"}
    def post(self,url,data={},params={}):
        self.json = {}
        self.text = ""
        answer = requests.post(url,data=data,params=params,cookies=self.cookies,headers=self.headers,allow_redirects=True)
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
    def get(self,url,params={}):
        self.json = {}
        self.text = ""
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



class Gog:
    def __init__(self,username,password):
        self.username = username
        self.password = password
        self.import_gog = import_gog
    def better_get_shelf(self):
        print(time.time())
        b = Browser()
        #Try cookies
        logged_in = False
        try:
            f = open("cache/cookies","r")
            b.cookies = eval(f.read())
            f.close()
            b.get("https://www.gog.com/account/ajax",params={
                "a":"gamesShelfMore",
                "p":0,
                "s":"date_purchased",
                "h":0,
                "q":"",
                "t":"%d"%time.time()*100
                })
            assert b.json["count"]
            print("Logged in")
            logged_in = True
        except:
            print("Not logged in")
            pass

        if not logged_in:
            b.get("https://www.gog.com/")
            login_auth = re.findall("(https\:\/\/auth\.gog\.com.*?)(\"|')",b.text)
            print(login_auth)
            b.get(login_auth[0][0])
            token = re.findall("login\[\_token\].*?>",b.text)
            print("token:",token)
            token_value = re.findall("value\=\"(.*?)\"",token[0])[0]
            print("token_value:",token_value)
            print("cur url:",b.url)
            b.post("https://login.gog.com/login_check",{
                "login[username]":self.username,
                "login[password]":self.password,
                "login[_token]":token_value,
                #~ "register[email]":"",
                #~ "register[password]":"",
                #~ "register[_token]":token_value,
                "login[login]":"",
                },
                )
            print("new url:",b.url)

            #Properly follow redirect!
            #print(b.answer.history[1].content)
            print(b.answer.history[0].content)
            link = re.findall(b"content\=.*?https(.*?)\"",b.answer.history[0].content)
            print(link)
            linknice = "https"+link[0].decode("utf8").replace("auth?amp;","auth?").replace("%22&amp;amp;","&").replace("https%3A%2F%2F","https://").replace("%2F","/").replace("&amp;amp;","&").replace("&amp;","&")
            print(linknice)
            b.get(linknice)
            print(b.url)
            print(b.cookies)

        #Should be logged in now
        f = open("cache/cookies","w")
        f.write(repr(b.cookies))
        f.close()
        count = 50
        page=1
        f = open("cache/mygog_shelf.html","w")
        #b.get("https://www.gog.com/account")
        #f.write(b.text)
        while count:
            b.get("https://www.gog.com/account/ajax",params={
                "a":"gamesShelfMore",
                "p":page,
                "s":"date_purchased",
                "h":0,
                "q":"",
                "t":"%d"%time.time()*100
                })
            print(b.json["count"])
            f.write(b.json["html"])
            page+=1
            count=b.json["count"]
        f.close()

if __name__ == "__main__":
    better_get_shelf()
    for game in import_gog():
        print (game.name)
