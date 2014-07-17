#!python3
import requests,re
import data
#import vdf

MY_API_KEY = "98934075AAB5F4E1223BEC4C40E88AA8"
MY_STEAM_ID = "76561197999655940"
STEAM_GAMES_URL = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=%(apikey)s&steamid=%(steamid)s&format=json&include_appinfo=1&include_played_free_games=1=1"

#f = open("finished.txt",encoding="utf8")
#finished = f.read().split("\n")
#finished = [x.decode("utf8") for x in finished]
#f.close()


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

def get_games(userid=MY_STEAM_ID):
    url = STEAM_GAMES_URL
    r = requests.get(url%{"apikey":MY_API_KEY,"steamid":MY_STEAM_ID})
    data = r.json()["response"]["games"]
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
    
def import_steam(userid=MY_STEAM_ID):
    #apps = load_userdata()["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"]
    apps = {}
    games = get_games()
    is_finished = []#match_finished_games(games,finished)
    library = []
    for g in games:
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
                lastplayed=data.sec_to_ts(int(app["LastPlayed"]))
        library.append(
            data.Game(name=g["name"],
                            minutes=g["playtime_forever"],
                            finished=set_finished,
                            source="steam",
                            steamid=g["appid"],
                            lastplayed=lastplayed,
                            icon_url=icon_url
        )
    )
    return library
    
def load_userdata(path="C:\\Steam\\userdata\\39390212\\config\\localconfig.vdf"):
    import vdf
    f = open(path)
    data = vdf.parse(f)
    f.close()
    return data
    
def create_nonsteam_shortcuts(games):
    """Given a list of games create shortcuts in steam for them"""
    import steam_shortcut_manager as ssm
    print ("Creating Steam Shortcuts")
    shortcuts = ssm.SteamShortcutManager("C:\\Steam\\userdata\\39390212\\config\\shortcuts.vdf")
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

#~ if __name__=="__main__":
    #~ import json
    #~ for game in import_steam():
        #~ print (game.name,game.icon_url)
