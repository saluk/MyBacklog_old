#!python3
import re,os

import requests

from .. import games

#import vdf

MY_API_KEY = ""
MY_STEAM_ID = ""

STEAM_GAMES_URL = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=%(apikey)s&steamid=%(steamid)s&format=json&include_appinfo=1&include_played_free_games=1"

def login_for_chat():
    sess = requests.session()
    sess.headers["Accept"] = "application/json, text/javascript;q=0.9, */*;q=0.5"
    sess.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    sess.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650"
    sess.headers["Referer"] = "http://steamcommunity.com/trade/1"
    try:
        f = open("cache/steamcookies",encoding="utf8")
        cookies = eval(f.read())
        f.close()
    except:
        cookies = {}
    print(cookies)
    #Get current rsa to use and encode password
    import rsa,base64
    r = sess.get("https://steamcommunity.com/login/getrsakey?username=saluk64007")
    dat = r.json()
    print (dat)
    if not dat["success"]:
        return None
    rsamod = int(dat["publickey_mod"],16)
    rsaexp = int(dat["publickey_exp"],16)
    rsatime = int(dat["timestamp"])
    pubkey = rsa.PublicKey(rsamod,rsaexp)
    bytepassword = b"games steam games 1 pass"
    encodedpassword = rsa.encrypt(bytepassword,pubkey)
    print (encodedpassword)
    b64pass = base64.b64encode(encodedpassword)
    print(b64pass)
    
    #Login
    data = {"password":b64pass,"username":"saluk64007",
        "captchagid":"","captcha_text":"",
        "emailauth":"","emailsteamid":"",
        "rsatimestamp":rsatime,
        "remember_login":True
    }
    dat = {"success":False,"firsttime":True}
    while not dat["success"]:
        print("sending data",data)
        r = sess.post("https://steamcommunity.com/login/dologin/",data=data)
        dat = r.json()
        print(r.json())
        if dat["success"]:
            print ("logged in")
            break
        if dat.get("emailauth_needed",False):
            data["emailsteamid"] = int(dat["emailsteamid"])
            s = input("enter auth code:")
            assert s
            data["emailauth"] = s
            print("processed data",data)
            assert data["emailauth"]
        else:
            print ("unknown error")
    sess.post("https://steamcommunity.com/",data={})
    cookies = sess.cookies
    f = open("cache/steamcookies","w",encoding="utf8")
    f.write(repr(requests.utils.dict_from_cookiejar(cookies)))
    f.close()
    return sess
    
def set_username(sess,name):
    r = sess.get("http://steamcommunity.com/profiles/76561197999655940/edit")
    sessid = re.findall("<input.*?sessionID.*?/>",r.text)[0]
    sessid = re.findall("value=\"(.*?)\"",sessid)[0]
    data = {
            "sessionID":sessid,
            "type":"profileSave",
            "personaName":name,
            "real_name":"saluk64007",
            "headline":"",
            "summary":"No information given.",
            "customURL":"saluk64007",
            "country":"US",
            "state":"",
            "city":"",
            "weblink_1_title":"",
            "weblink_1_url":"",
            "weblink_2_title":"",
            "weblink_2_url":"",
            "weblink_3_title":"",
            "weblink_4_url":"",
            }
    r = sess.post("http://steamcommunity.com/profiles/76561197999655940/edit",data=data)
    f = open("steampost.html","w",encoding="utf8")
    f.write(r.text)
    f.close()
    
#~ sess = login_for_chat()
#~ set_username(sess,"saluk")
#~ crash

class ApiError(Exception):
    pass

def get_user_id(custom_name):
    r = requests.get("http://steamcommunity.com/profiles/%s"%custom_name)
    if "Steam Community :: Error" in r.text:
        r = requests.get("http://steamcommunity.com/id/%s?xml=1"%custom_name)
        user_id = re.findall("steamID64\>(\d+)\<\/steamID64",r.text)[0]
        return user_id
    else:
        return custom_name

def get_games(apikey=MY_API_KEY,userid=MY_STEAM_ID):
    url = STEAM_GAMES_URL
    r = requests.get(url%{"apikey":apikey,"steamid":userid})
    try:
        data = r.json()["response"]["games"]
    except ValueError:
        raise ApiError()
    return data
    
def match_finished_games(games,finished):
    matched = []
    for f in finished:
        matches = []
        for g in games:
            if g["name"].lower().startswith(f.lower()):
                matches.append(g)
        if not matches:
            print("no match:",f)
            crash
        #Choose match with shortest name (closest match)
        matches.sort(key=lambda match:len(match["name"]))
        matched.append(matches[0])
    return matched
    
def import_steam(apikey=MY_API_KEY,userid=MY_STEAM_ID):
    #apps = load_userdata()["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"]
    apps = {}
    is_finished = []#match_finished_games(games,finished)
    library = []
    for g in get_games(apikey,userid):
        set_finished = 0
        if g in is_finished:
            set_finished = 1
        icon_url = ""
        if "img_icon_url" in g:
            icon_url  = "http://media.steampowered.com/steamcommunity/public/images/apps/%(appid)s/%(img_icon_url)s.jpg"%g
        lastplayed = None
        if str(g["appid"]) in apps:
            app = apps[str(g["appid"])]
            if "LastPlayed" in app:
                lastplayed=games.sec_to_ts(int(app["LastPlayed"]))
        game = games.Game(name=g["name"],
                            minutes=g["playtime_forever"],
                            finished=set_finished,
                            sources=[
                                {"source":"steam","id":g["appid"]}
                            ],
                            lastplayed=lastplayed,
                            icon_url=icon_url
            )
        game.generate_gameid()
        library.append(game)
    return library
    
def load_userdata(path=""):
    if not path:
        return {}
    from code.apis import vdf

    f = open(path)
    data = vdf.parse(f)
    f.close()
    return data
    
def create_nonsteam_shortcuts(games,shortcut_folder):
    """Given a list of games create shortcuts in steam for them"""
    from code.apis import steam_shortcut_manager as ssm
    print ("Creating Steam Shortcuts")
    shortcuts = ssm.SteamShortcutManager(shortcut_folder)
    shortcuts.shortcuts = []
    for game in games.values():
        print (game.name)
        if game.install_path and game.source != "steam":
            print ("( ok )Valid nonsteam game")
        else:
            print ("(skip)Game is in steam or no install path")
            continue
        div = ssm.SteamShortcut(game.name,
            game.install_path,
            game.install_folder,
            "","mybacklog")
        shortcuts.add(div)
        print ("--added")
    print ("saving")
    shortcuts.save()
    print ("saved")

class Steam:
    def __init__(self,app,api_key,user_id,userfile,shortcut_folder):
        self.app = app
        self.api_key = api_key
        self.profile_name = user_id
        self.user_id = user_id
        self.userfile = userfile
        self.shortcut_folder = shortcut_folder
        self.userdata = load_userdata(self.userfile)
        #self.installed_apps = self.userdata.get("UserLocalConfigStore",{}).get("Software",{}).get("Valve",{}).get("Steam",{}).get("apps",{})
        self.installed_apps = {}
    def import_steam(self):
        try:
            return import_steam(self.api_key,self.user_id)
        except ApiError:
            user_id = get_user_id(self.profile_name)
            an = import_steam(self.api_key,user_id)
            if user_id != self.user_id:
                self.user_id = user_id
            return an
    def create_nonsteam_shortcuts(self,games):
        return create_nonsteam_shortcuts(games,self.shortcut_folder)
    def search_installed(self):
        self.installed_apps = {}
        path = self.userfile
        print("PATH",path)
        path = os.path.split(self.userfile)[0]
        path = os.path.split(path)[0]
        path = os.path.split(path)[0]
        path = os.path.split(path)[0]
        path = os.path.join(path,"SteamApps")
        for f in os.listdir(path):
            if "appmanifest" in f:
                id = f.replace("appmanifest_","").replace(".acf","")
                self.installed_apps[id] = f
    def is_installed(self,steamid):
        if not self.installed_apps:
            self.search_installed()
        if str(steamid) in self.installed_apps:
            return True
        self.search_installed()
        if str(steamid) in self.installed_apps:
            return True

#~ if __name__=="__main__":
    #~ import json
    #~ for game in import_steam():
        #~ print (game.name,game.icon_url)
