#!python3
import os
import time
import datetime
import json

fmt = "%H:%M:%S %Y-%m-%d"
def now():
    t = time.localtime()
    return time.strftime(fmt,t)
def stot(s):
    if not s:
        return time.localtime(0)
    return time.strptime(s,fmt)
def ttos(t):
    return time.strftime(fmt,t)
def sec_to_ts(sec):
    return ttos(time.localtime(sec))

PRIORITIES = {-1:"now playing",0:"unprioritized",1:"soon",2:"later",3:"much later",5:"next year",99:"probably never"}

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
    def gameid(self,game):
        """Returns the unique id for the game according to this source
        If a unique id cannot be generated raise an error
        Defaults to a letters only version of the game's name"""
        if not game.name:
            raise InvalidIdException()
        s = [x.lower() for x in game.name if x.lower() in "abcdefghijklmnopqrstuvwxyz1234567890 "]
        s = "".join(s).replace(" ","_")
        return s
    def get_run_args(self,game):
        """Returns the method to run the game. Defaults to using a batch file to run the install_path exe"""
        import subprocess
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
                    f.write('"%s"\n'%game.install_path)
            args = [game.gameid+".bat"]
            folder = os.path.abspath("cache\\batches\\")
            if not self.missing_steam_launch(game):
            #HACKY - run game through steam
                args = ["cache\\steamshortcuts\\%s.url"%game.shortcut_name]
                folder = os.path.abspath("")
        return args,folder
    def missing_steam_launch(self,game):
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
    def args(self):
        return [("steamid","i")]
    def gameid(self,game):
        if not game.steamid:
            raise InvalidIdException()
        return "steam_%s"%game.steamid
    def get_run_args(self,game):
        args = ["c:\\steam\\steam.exe", "-applaunch", "%d"%game.steamid]
        return args,"."
    def missing_steam_launch(self,game):
        return False
sources["steam"] = SteamSource()
class GogSource(Source):
    def args(self):
        return [("gogid","s"),("install_path","s")]
    def gameid(self,game):
        if not game.gogid:
            raise InvalidIdException()
        return "gog_%s"%game.gogid
sources["gog"] = GogSource()
class HumbleSource(Source):
    def args(self):
        return [("humble_machinename","s"),("install_path","s"),("humble_package","s")]
    def gameid(self,game):
        if not game.humble_machinename:
            raise InvalidIdException()
        return "humble_%s"%game.humble_machinename
sources["humble"] = HumbleSource()
class GBASource(Source):
    def get_run_args(self,game):
        args = ["c:\\emu\\gb\\vbam\\VisualBoyAdvance-M.exe",game.install_path]
        return args,"."
sources["gba"] = GBASource()
class NoneSource(Source):
    pass
sources["none"] = NoneSource()
class OriginSource(Source):
    pass
sources["origin"] = OriginSource()

class Game:
    args = [("name","s"),("playtime","f"),("finished","i"),("genre","s"),("source","s"),("hidden","i"),("icon_url","s"),
    ("packageid","s"),("is_package","i"),("notes","s"),("priority","i"),("website","s")]
    def __init__(self,**kwargs):
        dontsavekeys = set(dir(self))
        self.name = ""
        self.playtime = 0
        self.finished = 0
        self.hidden = 0
        self.is_package = 0   #Set to 1 if it includes multiple games
        self.lastplayed = None   #timestamp in fmt
        self.source = "steam"
        self.packageid = ""  #Id of game within a package
        self.genre = ""
        self.icon_url = ""
        self.notes = ""
        self.priority = 0
        
        self.steamid = ""
        self.gogid = ""
        self.humble_machinename = ""
        self.humble_package = ""
        self.install_path = ""
        self.website = ""
        self.savekeys = set(dir(self)) - dontsavekeys
        for k in kwargs:
            if hasattr(self,k):
                setattr(self,k,kwargs[k])
        if "minutes" in kwargs:
            self.playtime = datetime.timedelta(minutes=kwargs["minutes"]).total_seconds()
        if stot(self.lastplayed).tm_year<1971:
            self.lastplayed = None
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
        return self.args+sources[self.source].args()
    @property
    def hours_minutes(self):
        s = self.playtime
        min = s/60.0
        hour = int(min/60.0)
        min = min-hour*60.0
        return hour,min
    @property
    def last_played_nice(self):
        if not self.lastplayed:
            return "never"
        t = time.strptime(self.lastplayed,fmt)
        return time.strftime("%a, %d %b %Y %H:%M:%S",t)
    @property
    def gameid(self):
        s = ""
        s = sources[self.source].gameid(self)
        if self.packageid and s:
            s += ".%s"%self.packageid
        return s
    @property
    def install_folder(self):
        """Full path to folder where executable is located"""
        return self.install_path.rsplit("\\",1)[0]
    def get_run_args(self):
        """Returns the args and folder to pass to the subprocess to run the game, according to our source"""
        return sources[self.source].get_run_args(self)
    def missing_steam_launch(self):
        return sources[self.source].missing_steam_launch(self)
    def dict(self):
        d = {}
        for k in self.savekeys:
            d[k] = getattr(self,k)
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
            if g.gogid == self.gogid and self.source=="gog" and g.source=="gog":
                gamelist.append(g)
            if g.source=="humble" and self.source=="humble" and self.humble_package==g.humble_package:
                gamelist.append(g)
        return gamelist
    def __repr__(self):
        return repr(self.dict())

class Games:
    def __init__(self):
        self.games = {}
        self.multipack = json.loads(open("gog_packages.json").read())
    def load(self,file):
        if not os.path.exists(file):
            print("Warning, no save file to load:",file)
            return
        f = open(file,"r")
        d = f.read()
        f.close()
        load_data = json.loads(d)
        for k in load_data["games"]:
            self.games[k] = Game(**load_data["games"][k])
    def import_packages(self):
        for gkey in list(self.games.keys()):
            game = self.games[gkey]
            if game.source=="gog" and "." in game.gogid:
                gogid,packageid = game.gogid.rsplit(".",1)
                game.gogid = gogid
                game.packageid = packageid
                package = Game(name=" ".join([x.capitalize() for x in gogid.split("_")]),
                        is_package=1,source="gog",gogid=gogid)
                if not package.gameid in self.games:
                    self.games[package.gameid] = package
                del self.games[gkey]
                self.games[game.gameid] = game
    def save(self,file):
        save_data = {"games":{}}
        for k in self.games:
            save_data["games"][k] = self.games[k].dict()
        f = open(file,"w")
        f.write(json.dumps(save_data,sort_keys=True,indent=4))
        f.close()
        f = open("gog_packages.json","w")
        f.write(json.dumps(self.multipack,sort_keys=True,indent=4))
        f.close()
    def add_games(self,game_list):
        for g in game_list:
            self.update_game(g.gameid,g)
    def update_game(self,gameid,game,force=False):
        assert(isinstance(game,Game))
        cur_game = self.games.get(gameid,None)
        if not cur_game or force:
            self.games[gameid] = game
            return
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
        return game
    def list(self):
        v = self.games.values()
        return sorted(v,key=lambda g:(g.finished,g.priority,-time.mktime(stot(g.lastplayed)),g.name))
    def delete(self, game):
        del self.games[game.gameid]