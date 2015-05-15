#!python3
import time
import requests
import re
from code import games
import json

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

import time

def get_humble_gamelist():
    b = Browser()
    logged_in = False
    b.get("https://www.humblebundle.com/")
    if not logged_in:
        try:
            f = open("cache/hcookies","r")
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
            "password":"blurontian",
            "qs":"",
            "submit-data":"",
            "username":"saluk64007@gmail.com"})
        print ("loggedin",b.url)
        print (b.cookies)
        f = open("humble.html","w")
        f.write(b.text)
        f.close()

    f = open("cache/hcookies","w")
    f.write(repr(b.cookies))
    f.close()
    
    #Should be logged in now
    api_get_order = "https://www.humblebundle.com/api/v1/order/%(key)s"
    #print (b.url,b.text)
    b.get("https://www.humblebundle.com/home")
    f = open("humble2.html","w")
    f.write(b.text)
    f.close()
    keys = re.findall("gamekeys \=.*?\[(.*?)\]",b.text)[0]
    print (keys)
    games = []
    for key in keys.split(","):
        key = re.findall("\"(.*?)\"",key)[0]
        b.get(api_get_order%{"key":key})
        print (b.json)
        hdata = b.json
        package = games.Game(name=hdata["product"]["human_name"])
        package.sources = [{"source":"humble","id":hdata["product"]["machine_name"],"package":hdata["gamekey"]}]
        package.package_data = {
            "type":"bundle",
            "contents":[],
            "source_info":package.create_package_data()
        }
        games.append(package)
        for sub in hdata["subproducts"]:
            game = games.Game(name=sub["human_name"],
                                        website=sub["url"],
                                        icon_url=sub["icon"])
            game.sources = [{"source":"humble","id":sub["machine_name"],"package":hdata["gamekey"]}]
            game.package_data = {
                    "type":"content",
                    "parent":{"gameid":package.gameid,"name":package.name},
                    "source_info":game.create_package_data()
            }
            games.append(game)
            package.package_data["contents"].append({"gameid":game.gameid,"name":game.name})
    for g in games:
        print (g.name,g.icon_url)
    print(games)
    return games
    

if __name__ == "__main__":
    get_humble_gamelist()
