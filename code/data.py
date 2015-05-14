#!python3
import os
import time
import datetime
import json
import sys
import subprocess
import webbrowser

fmt = "%H:%M:%S %Y-%m-%d"
def now():
    t = time.localtime()
    return time.strftime(fmt,t)
def stot(s):
    """From a string, return a datetime object"""
    if not s or s == "None":
        return time.localtime(0)
    return time.strptime(s,fmt)
def ttos(t):
    """From a datetime object, return a string"""
    return time.strftime(fmt,t)
#def sec_to_ts(sec):
#    """Convert an amount of seconds as a string into a time delta"""
#    return ttos(time.localtime(sec))

PRIORITIES = {-1:"now playing",0:"unprioritized",1:"soon",2:"later",3:"much later",5:"next year",99:"probably never"}
GAME_DB = "data/gamesv005.json"

run_with_steam = 1
#   NEW METHOD TO RUN THROUGH STEAM:
#   Export function which creates shortcuts to all non-steam games that aren't in steam yet
#   Manually creat shortcut for often played game, and put it in cache/steamshortcuts
#   When running a game, if a steam shortcut exists in cache/steamshortcuts, run that

class Source:
    """Definition of a source of games"""
    def args(self):
        """Return editable arguments that are unique to this source
        Defaults to install_path as that is pretty common"""
        return [("install_path","s")]
    def is_installed(self,game,source):
        return game.install_path
    def needs_download(self,game,source):
        if self.is_installed(game,source):
            return False
        return True
    def gameid(self,game):
        """Returns the unique id for the game according to this source
        If a unique id cannot be generated raise an error
        Defaults to a letters only version of the game's name"""
        if not game.name:
            raise InvalidIdException()
        return game.name_stripped
    def download_link(self,game,source):
        return ""
    def download_method(self,game,source):
        if game.download_link:
            webbrowser.open(game.download_link)
    def uninstall(self,game,source):
        if game.install_folder:
            subprocess.Popen(["explorer.exe",game.install_folder], cwd=game.install_folder, stdout=sys.stdout, stderr=sys.stderr)
    def get_run_args(self,game,source):
        """Returns the method to run the game. Defaults to using a batch file to run the install_path exe"""
        folder = game.install_folder #Navigate to executable's directory
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        import winshell, shlex
        if game.install_path.endswith(".lnk"):
            with winshell.shortcut(game.install_path) as link:
                args = [link.path] + shlex.split(link.arguments)
                folder = link.working_directory
        else:
            #Make batch file to run
            if 1:#not os.path.exists("cache/batches/"+game.gameid+".bat"):
                with open("cache/batches/"+game.gameid+".bat", "w") as f:
                    f.write('cd "%s"\n'%folder)
                    path = game.install_path.split("\\")[-1]
                    exe,args = path.split(".exe")
                    exe = exe+".exe"
                    f.write('"%s" %s\n'%(exe,args))
            args = [game.gameid+".bat"]
            folder = os.path.abspath("cache\\batches\\")
            #args = [game.install_path.split("\\")[-1]]
            #folder = game.install_path.rsplit("\\",1)[0]
            if not self.missing_steam_launch(game):
            #HACKY - run game through steam
                args = ["cache\\steamshortcuts\\%s.url"%game.shortcut_name]
                folder = os.path.abspath("")
        return args,folder
    def run_game(self,game,source):
        creationflags = 0
        shell = True
        if sys.platform=='darwin':
            shell = False
        args,folder = self.get_run_args(game,source)
        print("run args:",args,folder)

        if args and folder:
            print(args)
            curdir = os.path.abspath(os.curdir)
            os.chdir(folder)
            print(os.path.abspath(os.curdir))
            self.running = subprocess.Popen(args, cwd=folder, stdout=sys.stdout, stderr=sys.stderr, creationflags=creationflags, shell=shell)
            print("subprocess open")
            os.chdir(curdir)
    def missing_steam_launch(self,game,source):
        """Returns True if the game type wants a steam launcher and it doesn't exist"""
        if not run_with_steam:
            return False
        dest_shortcut_path = "cache/steamshortcuts/%s.url"%game.shortcut_name
        userhome = os.path.expanduser("~")
        desktop = userhome + "/Desktop/"
        shortcut_path = desktop+"%s.url"%game.shortcut_name
        if os.path.exists(shortcut_path):
            import shutil
            shutil.move(shortcut_path,dest_shortcut_path)
        if os.path.exists(dest_shortcut_path):
            return False
        return True
class InvalidIdException(Exception):
    pass

sources = {}
class SteamSource(Source):
    """Needs .api to be set to steamapi.Steam"""
    def args(self):
        return []
    def run_game(self,game,source):
        webbrowser.open("steam://rungameid/%d"%source["id"])
    def missing_steam_launch(self,game,source):
        return False
    def download_method(self,game,source):
        webbrowser.open("steam://install/%d"%source["id"])
    def uninstall(self,game,source):
        webbrowser.open("steam://uninstall/%d"%source["id"])
    def is_installed(self,game,source):
        return self.api.is_installed(source["id"])
sources["steam"] = SteamSource()
class GogSource(Source):
    """Needs .api to be set to steamapi.Gog"""
    def args(self):
        return [("install_path","s")]
    def download_link(self,game,source):
        return "gogdownloader://%s/installer_win_en"%source["id"]
sources["gog"] = GogSource()
class HumbleSource(Source):
    def args(self):
        return [("install_path","s")]
sources["humble"] = HumbleSource()
class ItchSource(Source):
    pass
sources["itch"] = ItchSource()
class GBASource(Source):
    def get_run_args(self,game,source):
        args = ["C:\\emu\\retroarch\\retroarch.exe","-c","C:\\emu\\retroarch\\retroarch-gba.cfg",game.install_path]
        return args,"."
sources["gba"] = GBASource()
class SNESSource(Source):
    def get_run_args(self,game,source):
        args = ["C:\\emu\\retroarch\\retroarch.exe","-c","C:\\emu\\retroarch\\retroarch-snes.cfg",game.install_path]
        return args,"."
sources["snes"] = SNESSource()
class N64Source(Source):
    def get_run_args(self,game,source):
        args = ["C:\\emu\\retroarch\\retroarch.exe","-c","C:\\emu\\retroarch\\retroarch-n64.cfg",game.install_path]
        return args,"."
sources["n64"] = N64Source()
class NDSSource(Source):
    def get_run_args(self,game,source):
        args = ["C:\\emu\\retroarch\\retroarch.exe","-c","C:\\emu\\retroarch\\retroarch-nds.cfg",game.install_path]
        return args,"."
sources["nds"] = NDSSource()
class NoneSource(Source):
    pass
sources["none"] = NoneSource()
class OriginSource(Source):
    pass
sources["origin"] = OriginSource()
class GamersGateSource(Source):
    pass
sources["gamersgate"] = GamersGateSource()
class OfflineSource(Source):
    def get_run_args(self,game,source):
        return None,None
sources["offline"] = OfflineSource()

class Game:
    args = [("name","s"),("playtime","f"),("lastplayed","s"),("finished","i"),("genre","s"),("hidden","i"),("icon_url","s"),
    ("packageid","s"),("is_package","i"),("notes","s"),("priority","i"),("website","s"),("import_date","s"),("finish_date","s")]
    def __init__(self,**kwargs):
        dontsavekeys = set(dir(self))
        self.gameid = ""

        self.name = ""
        self.playtime = 0
        self.finished = 0
        self.hidden = 0
        self.is_package = 0   #Set to 1 if it includes multiple games
        self.lastplayed = ""   #timestamp in fmt
        self.import_date = ""
        self.finish_date = ""
        self.sources = []
        self.packageid = ""  #Id of game within a package
        self.genre = ""
        self.icon_url = ""
        self.notes = ""
        self.priority = 0

        self.install_path = ""
        self.website = ""
        self.savekeys = set(dir(self)) - dontsavekeys
        for k in kwargs:
            if hasattr(self,k):
                setattr(self,k,kwargs[k])
        if not self.gameid:
            self.gameid = self.name_stripped+".0"
        if "minutes" in kwargs:
            self.playtime = datetime.timedelta(minutes=kwargs["minutes"]).total_seconds()
        self.data_changed_date = ""
    @property
    def name_stripped(self):
        if not self.name:
            return ""
        s = [x.lower() for x in self.name if x.lower() in "abcdefghijklmnopqrstuvwxyz1234567890 "]
        s = "".join(s).replace(" ","_")
        return s
    @property
    def is_in_package(self):
        return self.packageid or "humble" in self.sources and self.sources["humble"]["package"]
    def is_installed(self):
        for s in self.sources:
            if sources[s["source"]].is_installed(self,s):
                return True
    def needs_download(self):
        for s in self.sources:
            if sources[s["source"]].needs_download(self,s):
                return True
    def played(self):
        """Resets lastplayed to now"""
        self.lastplayed = now()
    def set_played(self,t):
        self.lastplayed = time.strftime(fmt,t)
    def display_print(self):
        print (self.name)
        print ("  %.2d:%.2d"%self.hours_minutes)
    @property
    def shortcut_name(self):
        """Returns game.name according to steam shortcut options"""
        return self.name.replace(":","")
    @property
    def valid_args(self):
        a = self.args[:]
        for s in self.sources:
            a.extend(sources[s["source"]].args())
        return a
    @property
    def hours_minutes(self):
        s = self.playtime
        min = s/60.0
        hour = int(min/60.0)
        min = min-hour*60.0
        return hour,min
    @property
    def last_played_nice(self):
        if not self.lastplayed or self.lastplayed == "None":
            return "never"
        t = time.strptime(self.lastplayed,fmt)
        return time.strftime("%a, %d %b %Y %H:%M:%S",t)
    @property
    def download_link(self):
        for s in self.sources:
            return sources[s["source"]].download_link(self,s)
    def download_method(self):
        for s in self.sources:
            return sources[s["source"]].download_method(self,s)
    def uninstall(self):
        for s in self.sources:
            return sources[s["source"]].uninstall(self,s)
    @property
    def install_folder(self):
        """Full path to folder where executable is located"""
        return self.install_path.rsplit("\\",1)[0]
    def get_run_args(self):
        """Returns the args and folder to pass to the subprocess to run the game, according to our source"""
        for s in self.sources:
            return sources[s["source"]].get_run_args(self,s)
    def run_game(self):
        for s in self.sources:
            return sources[s["source"]].run_game(self,s)
    def missing_steam_launch(self):
        for s in self.sources:
            return sources[s["source"]].missing_steam_launch(self,s)
    def dict(self):
        d = {}
        for k in self.savekeys:
            d[k] = getattr(self,k)
        d["sources"] = d["sources"].copy()
        return d
    def copy(self):
        return Game(**self.dict())
    def games_for_pack(self,games):
        if not self.is_package:
            raise Exception("Not a package")
        gamelist = []
        for g in games.games.values():
            if g==self:
                continue
            if g.is_package:
                continue
            add = False
            for ps in g.sources:
                for gs in self.sources:
                    if ps["source"] == "gog" and gs["source"] == "gog" and ps["id"] == gs["id"]:
                        add = True
                    if ps["source"] == "humble" and gs["source"] == "humble" and ps["package"] == gs["package"]:
                        add = True
            if add:
                gamelist.append(g)
        return gamelist
    def __repr__(self):
        return repr(self.dict())
    @property
    def source_match(self):
        string = ""
        for s in sorted(self.sources):
            string += s["source"] + "_" + str(s.get("id","")) + ";"
        return string
    def same_game(self,other_game):
        """Is this game logically the same game as other_game?

        Eventually
        if the id of this game from source_a matches the id of the other_game from source_a; YES
        if the id of this game from source_a does NOT match the id of the other_game from source_a: NO
        if our name matches other_game.name: yes
        if our name does not match other_game.name: no

        For now, we limit one entry per source:
        if our sources all match other_game.sources: yes
        if our install_path matches other_game.install_path: yes
        if our name matches other_game.name with NO sources: yes
        no
        """

        match1 = self.source_match
        match2 = other_game.source_match

        if self.is_package != other_game.is_package:
            return False
        if (match1 or match2):
            if match1==match2:
                return True
            return False
        if (self.install_path or other_game.install_path):
            if self.install_path==other_game.install_path:
                return True
            return False
        if self.name_stripped==other_game.name_stripped:
            return True
        return False

test1 = Game(name="blah")
test2 = test1.copy()
test2.name = "blah2"
assert test1.name!=test2.name

actions = {"add":{"type":"addgame","game":"","time":""},
        "delete":{"type":"deletegame","game":"","time":""},
        "update":{"type":"updategame","game":"","changes":{},"time":""},
        "play":{"type":"playgame","game":"","time":""},
        "stop":{"type":"stopgame","game":"","time":""}
        }
def changed(da,db):
    """Helper for update action, returns difference of 2 dicts"""
    print("Changed? ",da,db)
    d = {"_del_":[],"_add_":[],"_set_":[]}
    for k in da:
        if k not in db:
            d["_del_"].append(k)
        elif db[k] != da[k]:
            d["_set_"].append({"k":k,"v":db[k],"ov":da[k]})
    for k in db:
        if k not in da:
            d["_add_"].append({"k":k,"v":db[k]})
    if not d["_del_"]:
        del d["_del_"]
    if not d["_add_"]:
        del d["_add_"]
    if not d["_set_"]:
        del d["_set_"]
    print(d)
    return d
def add_action(t,**d):
    a = actions[t].copy()
    a.update(d)
    a["time"] = now()
    return a

class Games:
    def __init__(self):
        self.games = {}
        self.source_map = {}
        self.actions = []
        self.multipack = {}
        try:
            self.multipack = json.loads(open("gog_packages.json").read())
        except:
            pass
    def load(self,file=GAME_DB):
        if not os.path.exists(file):
            print("Warning, no save file to load:",file)
            return
        f = open(file,"r")
        d = f.read()
        f.close()
        self.translate_json(d)
    def translate_json(self,d):
        self.games = {}
        load_data = json.loads(d)
        for k in load_data["games"]:
            self.games[k] = Game(**load_data["games"][k])
        if not self.multipack:
            self.multipack = load_data.get("multipack",{})
        self.actions = load_data.get("actions",[])
    def save_data(self):
        save_data = {"games":{}}
        for k in self.games:
            save_data["games"][k] = self.games[k].dict()
        save_data["actions"] = self.actions
        save_data["multipack"] = self.multipack
        return json.dumps(save_data,sort_keys=True,indent=4)
    def save(self,file=GAME_DB):
        sd = self.save_data()
        f = open(file,"w")
        f.write(sd)
        f.close()
    def build_source_map(self):
        """Builds a dictionary map of source_id:game to make it easier to search for a game from
        a given source"""
        self.source_map = {}
        for gameid in self.games:
            game = self.games[gameid]
            keys = []
            for s in game.sources:
                keys.append(s["source"]+"_"+str(s.get("id","")))
            for key in keys:
                if key not in self.source_map:
                    self.source_map[key] = []
                self.source_map[key].append(game)
    def add_games(self,game_list):
        self.build_source_map()
        for g in game_list:
            self.update_game(g.gameid,g)
    def get_similar_games(self,game):
        list = []

        ids = []
        for s in game.sources:
            for g in self.source_map.get(s["source"]+"_"+str(s.get("id","")),[]):
                ids.append(g.gameid)

        okey,i = game.gameid.rsplit(".",1)
        while 1:
            nkey = okey+"."+str(i)
            if nkey not in self.games:
                break
            ids.append(okey+"."+str(i))
            i=int(i)+1

        for oid in ids:
            if game.same_game(self.games[oid]):
                list.append(self.games[oid])
            elif game.gameid==oid:
                list.append(self.games[oid])
        return list
    def update_game(self,gameid,game,force=False):
        assert(isinstance(game,Game))

        cur_game = None
        i = 0
        for g in self.get_similar_games(game):
            if g.same_game(game):
                cur_game = g
                break
            i2 = int(g.gameid.rsplit(".",1)[1])
            if i2>i:
                i = i2
        okey,oldi = gameid.rsplit(".",1)
        gameid = okey+"."+str(i)
        assert game is not cur_game

        if not cur_game or force:
            if cur_game:
                diff = changed(cur_game.dict(),game.dict())
                if diff:
                    print("UPDATE CHANGED GAME")
                    self.actions.append(add_action("update",game=game.dict(),changes=diff))
                    print("updating",cur_game.gameid,cur_game.source_match,">",game.gameid,game.source_match)
                else:
                    print("UPDATE... did not change game")
                    return
            else:
                self.actions.append(add_action("add",game=game.dict()))
                print("ADD GAME ACTION")
                print("adding",game.gameid,game.source_match)
            game.data_changed_date = now()
            self.games[gameid] = game
            return
        previous_data = cur_game.dict()
        if game.icon_url:
            cur_game.icon_url = game.icon_url
        if game.playtime > cur_game.playtime:
            cur_game.playtime = game.playtime
        if game.finished:
            cur_game.finished = 1
        if game.lastplayed and (not cur_game.lastplayed or stot(game.lastplayed)>stot(cur_game.lastplayed)):
            cur_game.lastplayed = game.lastplayed
        cur_game.is_package = game.is_package
        cur_game.packageid = game.packageid
        diff = changed(previous_data,cur_game.dict())
        if diff:
            cur_game.data_changed_date = now()
            self.actions.append(add_action("update",game=game.dict(),changes=diff))
            print("update 2",cur_game.gameid,cur_game.source_match,">",game.name,game.source_match)
        return cur_game
    def list(self,sort="priority"):
        v = self.games.values()
        if sort=="priority":
            return sorted(v,key=lambda g:(g.finished,g.priority,-time.mktime(stot(g.lastplayed)),g.name))
        elif sort=="added":
            add_dates = {}
            for a in self.actions:
                if a["type"] == "addgame":
                    g = Game(**a["game"])
                    add_dates[g.gameid] = time.mktime(stot(a["time"]))
            default = time.mktime(stot("23:39:03 1980-07-16"))
            return sorted(v,key=lambda g:(-time.mktime(stot(g.import_date)) or default))
        elif sort=="changed":
            default = time.mktime(stot("23:39:03 1980-07-16"))
            return sorted(v,key=lambda g:(-time.mktime(stot(g.data_changed_date)) or default))
    def get_package_for_game(self,game):
        for p in self.games.values():
            if not p.is_package:
                continue
            if p==game:
                continue
            for ps in p.sources:
                for gs in game.sources:
                    if ps["source"] == "gog" and gs["source"] == "gog" and ps["id"] == gs["id"]:
                        return p
                    if ps["source"] == "humble" and gs["source"] == "humble" and ps["package"] == gs["package"]:
                        return p
        return None
    def delete(self, game):
        self.actions.append(add_action("delete",game=game.dict()))
        del self.games[game.gameid]
    def play(self, game):
        self.actions.append(add_action("play",game=game.dict()))
    def stop(self, game):
        self.actions.append(add_action("stop",game=game.dict()))
