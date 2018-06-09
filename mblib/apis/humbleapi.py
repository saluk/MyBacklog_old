#!python3
import time
import requests
import re
import os
from mblib import games
import json

class ApiError(Exception):
    pass

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
            if not os.path.exists(cache_root+"/cache/humble"):
                os.mkdir(cache_root+"/cache/humble")
        if not cache or not os.path.exists(cache_root+"/cache/humble/"+url.replace(":","").replace("/","")):
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
                    f = open(cache_root+"/cache/humble/"+url.replace(":","").replace("/",""),"w")
                    f.write(json.dumps({"json":self.json,"text":self.text,"url":self.url}))
                    f.close()
        else:
            f = open(cache_root+"/cache/humble/"+url.replace(":","").replace("/",""))
            d = json.loads(f.read())
            f.close()
            self.json = d["json"]
            self.text = d["text"]
            self.url = d["url"]

import time

def get_humble_gamelist(log,username,password,cache_root):
    b = Browser()
    logged_in = False
    b.get("https://www.humblebundle.com/")
    log.write("humble logging in...")
    if not logged_in:
        try:
            f = open(cache_root+"/cache/hcookies","r")
            b.cookies = eval(f.read())
            f.close()
        except:
            pass
        b.get("https://www.humblebundle.com/home")
        if "error_id" not in b.text:
            logged_in = True
            print("used cookies!")
    if not logged_in:
        print("b.cookies:",b.cookies)
        b.post("https://www.humblebundle.com/processlogin",{
            "authy-token":"",
            "_le_csrf_token":b.cookies["csrf_cookie"],
            "goto":"/home",
            "password":password,
            "qs":"",
            "submit-data":"",
            "username":username})
        print ("loggedin",b.url)
        print (b.cookies)

    f = open(cache_root+"/cache/hcookies","w")
    f.write(repr(b.cookies))
    f.close()

    #Should be logged in now
    api_get_order = "https://www.humblebundle.com/api/v1/order/%(key)s"
    #print (b.url,b.text)
    b.get("https://www.humblebundle.com/home")
    if "error_id" in b.text:
        raise ApiError()
    log.write("humble login: success")
    try:
        keys = re.findall("gamekeys \=.*?\[(.*?)\]",b.text)[0]
    except:
        raise ApiError()
    print (keys)
    imported_games = []
    log.write("humble download info for %s packages"%len(keys.split(",")))
    for key in keys.split(","):
        key = re.findall("\"(.*?)\"",key)[0]
        b.get(api_get_order%{"key":key},cache=True,cache_root=cache_root)
        print (b.json)
        hdata = b.json
        package = games.Game(name=hdata["product"]["human_name"],import_date=games.now())
        package.sources = [{"source":"humble","id":str(hdata["product"]["machine_name"]),"package":hdata["gamekey"]}]
        package.package_data = {
            "type":"bundle",
            "contents":[],
            "source_info":package.create_package_data()
        }
        package.generate_gameid()
        imported_games.append(package)
        log.write("humble download info for %s products"%len(hdata["subproducts"]))
        for sub in hdata["subproducts"]:
            game = games.Game(name=sub["human_name"],
                                        website=sub["url"],
                                        icon_url=sub["icon"],
                                        import_date=games.now())
            game.sources = [{"source":"humble","id":str(sub["machine_name"]),"package":hdata["gamekey"]}]
            game.package_data = {
                    "type":"content",
                    "parent":{"gameid":package.gameid,"name":package.name},
                    "source_info":game.create_package_data()
            }
            game.generate_gameid()
            imported_games.append(game)
            package.package_data["contents"].append({"gameid":game.gameid,"name":game.name})
    for g in imported_games:
        print (g.name,g.gameid,g.package_data.keys(),g.icon_url)
    return imported_games

class Humble:
    def __init__(self,app,username,password):
        self.app = app
        self.username = username
        self.password = password
    def get_gamelist(self):
        return get_humble_gamelist(self.app.log,self.username,self.password,self.app.config["root"])

if __name__ == "__main__":
    get_humble_gamelist()
