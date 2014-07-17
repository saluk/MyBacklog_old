#!python3
import time
import requests
import re
import data
import json

class Browser:
    def __init__(self):
        self.cookies = {}
        #self.cookies = {"guc_al":"0","sessions_gog_com":"0","__utma":"95732803.1911890316.1399672018.1399672018.1399672018.1","__utmb":"95732803.5.9.1399672201295","__utmz":"95732803.1399672018.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)"}
        self.headers = {"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Encoding":"gzip, deflate","Accept-Language":"en-us,ko;q=0.7,en;q=0.3",
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:28.0) Gecko/20100101 Firefox/28.0",
            "Referer":"https://www.humblebundle.com/",
            "X-Requested-With":"XMLHttpRequest"}
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

import time

def get_humble_gamelist():
    b = Browser()
    logged_in = False
    if not logged_in:
        b.get("https://www.humblebundle.com")
        b.post("https://www.humblebundle.com/login",{
            "authy-token":"",
            "goto":"/home",
            "password":"blurontian",
            "qs":"",
            "submit-data":"",
            "username":"saluk64007@gmail.com"})
        print ("loggedin",b.url)
        print (b.cookies)
    
    #Should be logged in now
    api_get_order = "https://www.humblebundle.com/api/v1/order/%(key)s"
    #print (b.url,b.text)
    b.get("http://www.humblebundle.com/home")
    keys = re.findall("gamekeys\:.*?\[(.*?)\]",b.text)[0]
    print (keys)
    games = []
    for key in keys.split(","):
        key = re.findall("\"(.*?)\"",key)[0]
        b.get(api_get_order%{"key":key})
        print (b.json)
        hdata = b.json
        package = data.Game(name=hdata["product"]["human_name"],
                                        humble_package=hdata["gamekey"],
                                        humble_machinename=hdata["product"]["machine_name"],
                                        source="humble",
                                        is_package=1)
        games.append(package)
        for sub in hdata["subproducts"]:
            game = data.Game(name=sub["human_name"],
                                        source="humble",
                                        humble_machinename=sub["machine_name"],
                                        humble_package=hdata["gamekey"],
                                        website=sub["url"],
                                        icon_url=sub["icon"])
            games.append(game)
    for g in games:
        print (g.name,g.icon_url)
    print(games)
    return games
    

if __name__ == "__main__":
    get_humble_gamelist()
