#!python3
import re,os,time
import random
from concurrent import futures
import codecs

import requests
from bs4 import BeautifulSoup

from code.apis import vdf
from code.resources import icons

try:
    from .. import games
    from code import systems
except:
    pass

MY_API_KEY = ""
MY_STEAM_ID = ""

STEAM_GAMES_URL = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=%(apikey)s&steamid=%(steamid)s&format=json&include_appinfo=1&include_played_free_games=1"
USER_DATA_URL = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=%(apikey)s&steamids=%(steamid)s&format=json"

def vg(dat,key):
    try:
        return dat[key]
    except:
        for real_key in dat.keys():
            if real_key.lower()==key.lower():
                return dat[real_key]
        raise KeyError("Could not find key %s"%(key))
class ParsedVdf:
    def __init__(self,file_name=None,parsed_data=None):
        if parsed_data:
            self.parsed = parsed_data
        else:
            with codecs.open(file_name,encoding="utf8",errors="ignore") as f:
                self.parsed = vdf.parse(f,mapper=vdf.VDFDict,key_lower=False)
    def __contains__(self, key):
        if self.parsed.__contains__(key):
            return True
        for real_key in self.parsed.keys():
            if real_key.lower()==key.lower():
                return True
    def __getitem__(self, key):
        print("GETITEM",repr(key))
        val = vg(self.parsed, key)
        if isinstance(val,vdf.VDFDict):
            return ParsedVdf(parsed_data=val)
        return val
    def get(self, key, default=None):
        try:
            return self[key]
        except:
            return default
    def __getattr__(self, key):
        return getattr(self.parsed, key)

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
        f = open(cache_url)
        dat = eval(f.read())
        f.close()
    return dat

def get_games(apikey=MY_API_KEY,userid=MY_STEAM_ID):
    url = STEAM_GAMES_URL
    access_url = url%{"apikey":apikey,"steamid":userid}
    print("ACCESS:",access_url)
    r = requests.get(access_url)
    try:
        data = r.json()["response"]["games"]
    except ValueError:
        raise ApiError()
    return data

def import_steam(apikey=MY_API_KEY,userid=MY_STEAM_ID,cache_root=".",user_data=None,logger=None):
    #apps = load_userdata()["UserLocalConfigStore"]["Software"]["valve"]["Steam"]["apps"]
    apps = {}
    if user_data:
        apps = user_data["userlocalconfigstore"]["software"]["valve"]["steam"]["apps"]
    db = {}
    is_finished = []
    for g in get_games(apikey,userid):
        set_finished = 0
        if g in is_finished:
            set_finished = 1
        icon_url = ""
        logo_url = ""
        if "img_icon_url" in g and g["img_icon_url"].strip():
            icon_url  = "http://media.steampowered.com/steamcommunity/public/images/apps/%(appid)s/%(img_icon_url)s.jpg"%g
        if "img_logo_url" in g and g["img_logo_url"].strip():
            logo_url = "http://media.steampowered.com/steamcommunity/public/images/apps/%(appid)s/%(img_logo_url)s.jpg"%g
        lastplayed = None
        app = apps.get(str(g["appid"]),None)
        if app:
            lp = app.get("lastplayed",None)
            if lp:
                lastplayed=games.sec_to_ts(int(lp))
        #print(g)
        game = games.Game(name=g["name"],
                            minutes=g["playtime_forever"],
                            finished=set_finished,
                            sources=[
                                {"source":"steam","id":str(g["appid"])}
                            ],
                            lastplayed=lastplayed,
                            icon_url=icon_url,
                            logo_url=logo_url,
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

    data = ParsedVdf(systems.fullpath(path))

    load_userdata.cache[path] = data
    load_userdata.cache["_time_"] = time.time()
    return data
load_userdata.cache = {}

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
            if not os.path.exists(lc):
                continue
            print("Check user",user_id,p3,lc)
            dat = ParsedVdf(lc)
            username = dat["userlocalconfigStore"]["friends"][user_id]["name"]
            users[username] = {"local":lc,"shortcut":p3+"/shortcuts.vdf","account_id":int(user_id)+76561197960265728}
    return users

class Steam:
    def __init__(self,app,api_key,user_id,userfile,shortcut_folder):
        self.app = app
        self.api_key = api_key
        if not api_key:
            self.api_key = "98934075AAB5F4E1223BEC4C40E88AA8"
        self.profile_name = user_id
        self.user_id = get_user_id(self.profile_name)
        self.userfile = userfile
        self.shortcut_folder = shortcut_folder
        self.userdata = load_userdata(self.userfile)
        path = os.path.split(self.userfile)[0]
        path = os.path.split(path)[0]
        path = os.path.join(path,"7")
        path = os.path.join(path,"remote")
        self.shared_config = os.path.join(path,"sharedconfig.vdf")
        self.installed_apps = {}
        self.last_install_search = 0
    def get_steamapp_paths(self):
        path = self.userfile
        path = os.path.split(self.userfile)[0]
        path = os.path.split(path)[0]
        path = os.path.split(path)[0]
        path = os.path.split(path)[0]
        path = os.path.join(path,"SteamApps")
        paths = [path]
        if os.path.exists(path+"/libraryfolders.vdf"):
            libraryfolders = ParsedVdf(path+"/libraryfolders.vdf")
            print(libraryfolders)
            i = 1
            while 1:
                if str(i) not in libraryfolders["libraryfolders"].keys():
                    break
                paths.append(libraryfolders["libraryfolders"][str(i)]+"/steamapps")
                i+=1
        print("found steam paths:",paths)
        return paths
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
        return list(games.values())
    def update_local_games(self,db):
        paths = self.get_steamapp_paths()
        for path in paths:
            for p in os.listdir(path):
                if "appmanifest" in p:
                    print("Scanning",os.path.join(path,p))
                    vdf_data = ParsedVdf(os.path.join(path,p))
                    appid = vdf_data["AppState"]["appID"]
                    name = vdf_data["appstate"].get("name","")
                    if not name:
                        name = vdf_data["appstate"].get("userconfig",{}).get("name","")
                    if name and appid not in db:
                        name = name.encode("latin-1","ignore").decode("utf8","ignore")
                        db[appid] = games.Game(name=name,sources=[{"source":"steam","id":str(appid)}],import_date=games.now())
                        db[appid].generate_gameid()
        return db
    def search_installed(self):
        paths = self.get_steamapp_paths()
        self.installed_apps = {}
        for path in paths:
            print("checking path",path)
            if not os.path.isdir(path):
                continue
            for f in os.listdir(path):
                print(f)
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
    def export(self):
        print(self.shared_config)
        vdict = ParsedVdf(self.shared_config)
        for game in self.app.games.list():
            if game.get_source("steam"):
                export_game_category(game,vdict)
        with open(self.shared_config,"w") as f:
            vdf.dump(vdict.parsed,f,pretty=True)
        create_nonsteam_shortcuts(self.app.games.list(None),self.shortcut_folder,self.app.config["root"])
    def running_game_id(self):
        url = USER_DATA_URL%{"apikey":self.api_key,"steamid":self.user_id}
        print(url)
        r = requests.get(USER_DATA_URL%{"apikey":self.api_key,"steamid":self.user_id})
        data = r.json()
        print(data)
        return data["response"]["players"][0].get("gameid",None)

def import_all():
    import json
    for game in import_steam():
        print (game.name,game.icon_url)

def tolist(klist):
    l = [(int(k),v) for (k,v) in klist.items()]
    l.sort(key=lambda x: x[0])
    return [kv[1] for kv in l]
def toklist(list):
    d = {}
    i=0
    for v in list:
       d[str(i)] = v
       i+=1
    return vdf.VDFDict(d)
    
def shortcut_id(name="Assassin's Creed Syndicate(mbl)",target='"C:\\Program Files (x86)\\MyBacklog\\MyBacklog.exe" --play b998da00d9917a242109d9069c08e1a6'):
    """
    Calculates the filename for a given shortcut. This filename is a 64bit
    integer, where the first 32bits are a CRC32 based off of the name and
    target (with the added condition that the first bit is always high), and
    the last 32bits are 0x02000000.
    """
    # Following comment from: https://github.com/scottrice/Ice
    # This will seem really strange (where I got all of these values), but I
    # got the xor_in and xor_out from disassembling the steamui library for 
    # OSX. The reflect_in, reflect_out, and poly I figured out via trial and
    # error.
    from crcmod import mkCrcFun
    #algorithm = crc_algorithms.Crc(width = 32, poly = 0x04C11DB7, reflect_in = True, xor_in = 0xffffffff, reflect_out = True, xor_out = 0xffffffff)
    #algorithm = mkCrcFun(poly = 0x04C11DB7, initCrc = 0xffffffff, xorOut = 0xffffffff)
    input_string = bytes(target+name,'ascii')
    import binascii
    top_32 = binascii.crc32(input_string) | 0x80000000
    full_64 = (top_32 << 32) | 0x02000000
    return str(full_64)
    
def make_grid_for_shortcut(name,target,iconpath,shortcutpath):
    if not os.path.exists(iconpath): return
    import shutil
    gameid = shortcut_id(name,target)
    shutil.copy(iconpath,os.path.join(os.path.dirname(shortcutpath),"grid",gameid+".png"))

def create_nonsteam_shortcuts(gamelist,shortcutpath,filecache_root=""):
    """Given a list of games create shortcuts in steam for them"""
    with open(shortcutpath,"rb") as f:
        fjson = vdf.binary_loads(f.read(),mapper=vdf.VDFDict)
        current_cuts = tolist(fjson.get("shortcuts",{}))
    for c in current_cuts[:]:
        if "mbl" in c["AppName"]:
            current_cuts.remove(c)
    print(current_cuts)
            
    for game in gamelist:
        print(repr(game.name))
        if game.is_installed() and not game.get_source("steam"):
            if "shin megami tensei" in game.name.lower():
                print ("( ok )Valid nonsteam game")
        else:
            if "shin megami tensei" in game.name.lower():
                print (game.get_source("steam"),"(skip)Game is in steam or no install path")
            continue
        tags = ["mybacklog"]
        if game.finished:
            tags += ["finished"]
        else:
            tags += ["unfinished"]
        logopath = icons.icon_for_game(game,64,{},filecache_root,category="logo",imode="path")
        iconpath = icons.icon_for_game(game,64,{},filecache_root,category="icon",imode="path")
        name = game.name_ascii + "(mbl)"
        exe = '"C:\\Program Files (x86)\\MyBacklog\\MyBacklog.exe" --play %s'%game.gameid
        make_grid_for_shortcut(name,exe,logopath,shortcutpath)
        cut = {"AppName":name,
            "exe":exe,
            "StartDir":"C:\\Program Files (x86)\\MyBacklog",
            "icon":iconpath,
            'ShortcutPath': '', 
            'LaunchOptions': '', 
            'IsHidden': 0, 
            'AllowDesktopConfig': 1, 
            'OpenVR': 0, 
            'LastPlayTime': games.ts_to_sec(game.lastplayed), 
            'tags': toklist(tags)
            }
        current_cuts.append(cut)
        print ("--added")
    print ("saving",{"shortcuts":toklist(current_cuts)})
    with open(shortcutpath,"wb") as f:
        f.write(vdf.binary_dumps(vdf.VDFDict({"shortcuts":toklist(current_cuts)})))
    print ("saved")
def export_game_category(game,vdict):
    """Exports attributes from mybacklog into steam"""
    steamid = str(game.get_source("steam")["id"])
    apps = vdict["UserRoamingConfigStore"]["Software"]["Valve"]["Steam"]["apps"]
    
    set_category = []
    clear_category = []
    if game.finished:
        set_category.append("finished")
        clear_category.append("unfinished")
    else:
        clear_category.append("finished")
        set_category.append("unfinished")
        
    def add_cat(c,d):
        for k in d:
            if d[k]==c:
                return
        k = int(k)+1
        d[k]=c
    
    if not steamid in apps.parsed:
        apps.parsed[steamid] = vdf.VDFDict({"tags":{}})
    if not "tags" in apps.parsed[steamid]:
        apps.parsed[steamid]["tags"] = vdf.VDFDict({})
    cats = tolist(apps.parsed[steamid]["tags"])
    for cat in set_category:
        if cat not in cats:
            cats.append(cat)
    for cat in clear_category:
        if cat in cats:
            cats.remove(cat)
    apps.parsed[steamid][(0,"tags")] = toklist(cats)

    if "Hidden" in apps.parsed[steamid]:
        del apps.parsed[steamid]["Hidden"]
    if game.hidden:
        apps.parsed[steamid]["Hidden"] = "1"
        