#!python3
import re,os,time
import random
from concurrent import futures

import requests
from bs4 import BeautifulSoup

try:
    from .. import games
    from code.apis import vdf
    from code import systems
except:
    pass

MY_API_KEY = ""
MY_STEAM_ID = ""

STEAM_GAMES_URL = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=%(apikey)s&steamid=%(steamid)s&format=json&include_appinfo=1&include_played_free_games=1"

def get_vdf_url(dat,*keys):
    o = dat
    traverse = list(keys)
    while traverse:
        k = traverse.pop(0)
        if k not in o:
            k = k.lower()
        o = o[k]
    return o

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
        try:
            user_id = re.findall("steamID64\>(\d+)\<\/steamID64",r.text)[0]
        except IndexError:
            raise ApiError()
        return user_id
    else:
        return custom_name
        
def scrape_app_page(appid,cache_root="",logger=None):
    url = "http://store.steampowered.com/app/"+str(appid)
    
    if not os.path.exists(cache_root+"/cache/steamapi"):
        os.mkdir(cache_root+"/cache/steamapi")
    cache_url = cache_root+"/cache/steamapi/"+url.replace(":","").replace("/","").replace("?","QU").replace("&","AN")
    dat = {}
    if not os.path.exists(cache_url):
        r = requests.get(url)
        html = r.text
        if "agecheck" in r.url:
            r = requests.post("http://store.steampowered.com/agecheck/app/"+str(appid)+"/",{
                    "snr":"1_agecheck_agecheck__age-gate",
                    "ageDay":str(random.randint(1,28)),
                    "ageMonth":random.choice(["February","September"]),
                    "ageYear":str(random.randint(1950,1995))
                })
            html = r.text

        tags=categories=[]

        #print("Scrape",appid)
        soup = BeautifulSoup(html,"html.parser")

        tag_html = soup.find(class_="popular_tags")
        if tag_html:
            tags = [x.text.strip() for x in tag_html.find_all("a")]

        category_html = soup.find(id="category_block")
        if category_html:
            categories = [x.text.strip() for x in category_html.find_all("a") if x.text.strip()]

        vr = []
        for block in soup.find_all(class_="block"):
            if block.find_all(class_="vrsupport"):
                vr = [x.text.strip().replace(" ","_") for x in block.find_all("a") if x.text.strip()]

        dat = {"tags":tags,"categories":categories,"vr":vr}
        
        f = open(cache_url,"w")
        f.write(repr(dat))
        f.close()

        print("Caching data for:"+appid)
        time.sleep(0.1)
    else:
        print("Loading data for",appid)
        f = open(cache_url)
        dat = eval(f.read())
        f.close()
    return dat

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
    
def import_steam(apikey=MY_API_KEY,userid=MY_STEAM_ID,cache_root=".",user_data=None,logger=None):
    #apps = load_userdata()["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"]
    apps = {}
    if user_data:
        apps = user_data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"]
    db = {}
    is_finished = []#match_finished_games(games,finished)
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
                                {"source":"steam","id":str(g["appid"])}
                            ],
                            lastplayed=lastplayed,
                            icon_url=icon_url,
                            import_date=games.now()
            )
        game.generate_gameid()
        db[str(g["appid"])] = game

    def get_extra_data(game):
        logger.write("scraping data...")
        extra_data = scrape_app_page(game.sources[0]["id"],cache_root,logger=logger)
        logger.write("scraped data:"+"".join(extra_data.keys()))
        genre = ""
        for cat in extra_data["categories"]:
            if "co-op" in cat.lower() and not genre:
                genre = "co-op"
            if "local co-op" in cat.lower():
                genre = "local co-op"
        for vr in extra_data["vr"]:
            genre += "; vr_"+vr
        if genre:
            game.genre = genre

    num_data = len(db)

    game_tasks = [game for game in db.values()]
    i = 0
    while game_tasks:
        next_set = game_tasks[:100]
        game_tasks = game_tasks[100:]
        with futures.ThreadPoolExecutor(50) as executor:
            tasks = [executor.submit(get_extra_data,game) for game in next_set]
            for cf in futures.as_completed(tasks):
                cf.result()
                if logger:
                    logger.write("Read data for game %s of %s"%(i+1,num_data))
                i+=1

    return db
    
def load_userdata(path=""):
    if not path:
        return {}

    if path in load_userdata.cache and (time.time()-load_userdata.cache["_time_"])<10:
        return load_userdata.cache[path]

    f = open(systems.fullpath(path))
    data = vdf.parse(f)
    f.close()

    load_userdata.cache[path] = data
    load_userdata.cache["_time_"] = time.time()
    return data
load_userdata.cache = {}
    
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

def find_steam_files():
    """Iterate through common steam installation paths to find user files"""
    users = {}
    for path in systems.steam_paths:
        p2 = path+"/userdata"
        if not os.path.exists(p2):
            continue
        for user_id in os.listdir(p2):
            p3 = p2+"/"+user_id+"/config"
            lc = p3+"/localconfig.vdf"
            if not os.path.exists(p3):
                continue
            f = open(lc)
            dat = vdf.parse(f)
            f.close()
            username = dat["UserLocalConfigStore"]["friends"][user_id]["name"]
            users[username] = {"local":lc,"shortcut":p3+"/shortcuts.vdf","account_id":int(user_id)+76561197960265728}
    return users

class Steam:
    def __init__(self,app,api_key,user_id,userfile,shortcut_folder):
        self.app = app
        self.api_key = api_key
        if not api_key:
            self.api_key = "98934075AAB5F4E1223BEC4C40E88AA8"
        self.profile_name = user_id
        self.user_id = user_id
        self.userfile = userfile
        self.shortcut_folder = shortcut_folder
        self.userdata = load_userdata(self.userfile)
        #self.installed_apps = self.userdata.get("UserLocalConfigStore",{}).get("Software",{}).get("Valve",{}).get("Steam",{}).get("apps",{})

        self.installed_apps = {}
        self.last_install_search = 0
    def get_steamapp_path(self):
        path = self.userfile
        path = os.path.split(self.userfile)[0]
        path = os.path.split(path)[0]
        path = os.path.split(path)[0]
        path = os.path.split(path)[0]
        path = os.path.join(path,"SteamApps")
        return path
    def import_steam(self):
        games = {}
        try:
            games = import_steam(self.api_key,self.user_id,self.app.config["root"],self.userdata,self.app.log)
        except ApiError:
            user_id = get_user_id(self.profile_name)
            games = import_steam(self.api_key,user_id,self.app.config["root"],self.userdata,self.app.log)
            if user_id != self.user_id:
                self.user_id = user_id
        self.update_local_games(games)
        return games.values()
    def update_local_games(self,db):
        from code.apis import vdf
        path = self.get_steamapp_path()
        for p in os.listdir(path):
            if "appmanifest" in p:
                print("Scanning",os.path.join(path,p))
                f = open(os.path.join(path,p))
                vdf_data = vdf.parse(f)
                f.close()
                appid = get_vdf_url(vdf_data,"AppState","appID")
                name = vdf_data["AppState"].get("name","")
                if not name:
                    name = vdf_data["AppState"].get("UserConfig",{}).get("name","")
                if name and appid not in db:
                    name = name.encode("latin-1","ignore").decode("utf8","ignore")
                    db[appid] = games.Game(name=name,sources=[{"source":"steam","id":str(appid)}],import_date=games.now())
                    db[appid].generate_gameid()
        return db
    def create_nonsteam_shortcuts(self,games):
        return create_nonsteam_shortcuts(games,self.shortcut_folder)
    def search_installed(self):
        path = self.get_steamapp_path()
        self.installed_apps = {}
        for f in os.listdir(path):
            if "appmanifest" in f:
                id = f.replace("appmanifest_","").replace(".acf","")
                self.installed_apps[id] = f
    def is_installed(self,steamid):
        if not self.installed_apps:
            self.search_installed()
        if str(steamid) in self.installed_apps:
            return True

        if time.time()-self.last_install_search>10:
            self.search_installed()
            self.last_install_search = time.time()

        if str(steamid) in self.installed_apps:
            return True

def import_all():
    import json
    for game in import_steam():
        print (game.name,game.icon_url)
