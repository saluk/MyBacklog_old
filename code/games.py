#!python3
import os
import time
import datetime
import json
import hmac
import copy
from code import sources

fmt = "%H:%M:%S %Y-%m-%d"
def now():
    t = time.localtime()
    return time.strftime(fmt,t)
def stot(s):
    """From a string, return a struct_time"""
    if not s or s == "None":
        return time.localtime(0)
    try:
        return time.strptime(s,fmt)
    except:
        return time.localtime(0)
def ttos(t):
    """From a struct_time object, return a string"""
    return time.strftime(fmt,t)
#def sec_to_ts(sec):
#    """Convert an amount of seconds as a string into a time delta"""
#    return ttos(time.localtime(sec))

PRIORITIES = {-1:"now playing",0:"unprioritized",1:"soon",2:"later",3:"much later",5:"next year",99:"probably never"}

def get_source(s):
    return sources.all[s]

class Game:
    args = [("name","s"),("playtime","f"),("lastplayed","d"),("finished","i"),("genre","s"),("hidden","i"),("icon_url","s"),
    ("notes","s"),("priority","i"),("website","s"),("import_date","d"),("finish_date","d")]
    def __init__(self,**kwargs):
        dontsavekeys = set(dir(self))
        self.gameid = Exception("Do not save me")

        self.name = ""
        self.playtime = 0
        self.finished = 0
        self.hidden = 0
        self.package_data = {}
        self.lastplayed = ""   #timestamp in fmt
        self.data_changed_date = ""
        self.import_date = ""
        self.finish_date = ""
        self.sources = []
        self.genre = ""
        self.icon_url = ""
        self.notes = ""
        self.priority = 0

        self.website = ""
        self.savekeys = set(dir(self)) - dontsavekeys
        for k in kwargs:
            if hasattr(self,k):
                setattr(self,k,kwargs[k])
        if "minutes" in kwargs:
            self.playtime = datetime.timedelta(minutes=kwargs["minutes"]).total_seconds()
        self.games = None
        if "games" in kwargs:
            self.games = kwargs["games"]
    @property
    def name_stripped(self):
        if not self.name:
            return ""
        s = [x.lower() for x in self.name if x.lower() in "abcdefghijklmnopqrstuvwxyz1234567890 "]
        s = "".join(s).replace(" ","_")
        return s
    def generate_gameid(self):
        """Used to generate the intial gameid, before collisions are checked when checking into the db"""
        pool = hmac.new(b"")
        if self.sources:
            for s in self.sources:
                pool.update(bytes(s["source"],"utf8"))
                if s.get("id"):
                    pool.update(bytes(str(s["id"]),"utf8"))
                else:
                    #Need SOME way to uniquely identify this game that's not attributed anywhere
                    #It probably does NOT have package_data
                    #Go with the name...
                    pool.update(bytes(self.name_stripped,"utf8"))
        if self.package_data:
            pool.update(bytes(self.package_data["type"],"utf8"))
            if self.package_data["type"] == "bundle":
                pool.update(bytes(self.package_data["source_info"]["package_source"],"utf8"))
                pool.update(bytes(str(self.package_data["source_info"]["package_id"]),"utf8"))
            elif self.package_data["type"] == "content":
                pool.update(bytes(self.package_data["source_info"]["package_source"],"utf8"))
                pool.update(bytes(str(self.package_data["source_info"]["package_id"]),"utf8"))
                try:
                    pool.update(bytes(str(self.package_data["source_info"]["id_within_package"]),"utf8"))
                except:
                    print(self.package_data)
                    crash
        if not self.sources and not self.package_data:
            pool.update(bytes(self.name_stripped,"utf8"))
        self.gameid = pool.hexdigest()
    @property
    def is_in_package(self):
        return self.package_data.get("type","")=="content"
    @property
    def is_package(self):
        return self.package_data.get("type","")=="bundle"
    def is_installed(self):
        for s in self.sources:
            if get_source(s["source"]).is_installed(self,s):
                return True
    def needs_download(self):
        for s in self.sources:
            if get_source(s["source"]).needs_download(self,s):
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
            a.extend(get_source(s["source"]).args())
        return a
    @property
    def playtime_hours_minutes(self):
        s = self.playtime
        min = s/60.0
        hour = int(min/60.0)
        min = min-hour*60.0
        return "%.2d:%.2d"%(hour,min)
    @playtime_hours_minutes.setter
    def playtime_hours_minutes(self,s):
        hour,min = s.split(":")
        t = int(hour)*60*60+int(min)*60
        self.playtime = t
    @property
    def last_played_nice(self):
        if not self.lastplayed or self.lastplayed == "None":
            return "never"
        try:
            t = time.strptime(self.lastplayed,fmt)
            return time.strftime("%a, %d %b %Y %H:%M:%S",t)
        except:
            return "error"
    @property
    def download_link(self):
        for s in self.sources:
            return get_source(s["source"]).download_link(self,s)
    def download_method(self):
        for s in self.sources:
            return get_source(s["source"]).download_method(self,s)
    def uninstall(self):
        for s in self.sources:
            return get_source(s["source"]).uninstall(self,s)
    @property
    def install_folder(self):
        """Full path to folder where executable is located"""
        return self.install_path.rsplit("\\",1)[0]
    def run_game(self,cache_root):
        for s in self.sources:
            return get_source(s["source"]).run_game(self,s,cache_root)
    def dict(self):
        d = {}
        for k in self.savekeys:
            d[k] = getattr(self,k)
        d["sources"] = copy.deepcopy(d["sources"])
        return d
    def copy(self):
        g = Game(**self.dict())
        g.games = self.games
        return g
    def games_for_pack_converter(self,games):
        #TODO: This is just so we don't break the converter, once we have fully migrated we don't need this anymore
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

        print(match1,match2)

        if self.is_package != other_game.is_package:
            return False
        if self.is_in_package != other_game.is_in_package:
            return False
        if self.is_in_package and other_game.is_package or self.is_package and other_game.is_in_package:
            return False
        if self.is_in_package:
            if self.package_data["source_info"] != other_game.package_data["source_info"]:
                return False
        if (match1 or match2):
            if match1==match2:
                return True
            return False
        if (self.get_path() or other_game.get_path()):
            if self.get_path()==other_game.get_path():
                return True
            return False
        if self.name_stripped==other_game.name_stripped:
            return True
        return False
    def create_package_data(self):
        def get_source_info(source):
            if source["source"] == "gog":
                return {"package_source":"gog","package_id":source["id"],"id_within_package":self.name_stripped}
            elif source["source"] == "humble":
                return {"package_source":"humble","package_id":source["package"],"id_within_package":source["id"]}
        for source in self.sources:
            inf = get_source_info(source)
            if inf:
                return inf
        return {}
    def get_path(self):
        """If possible, return path to the main exe or file which launches the game"""
        if not self.games:
            return ""
        files = self.games.local.get("game_data",{}).get(self.gameid,{}).get("files",[])
        for f in files:
            if f["primary"]:
                return f["path"]
        return ""
    def get_exe(self):
        """If possible, return an exe, or file to launch the game"""
        path = self.get_path()
        if path.endswith(".exe"):
            return path
    def get_gba(self):
        path = self.get_path()
        if path.endswith(".gba"):
            return path
    @property
    def install_path(self):
        return self.get_path()
    @install_path.setter
    def install_path(self,value):
        if not value:
            return
        if not self.get_path():
            file = {"source":self.sources[0],"primary":True}
            if self.gameid not in self.games.local["game_data"]:
                self.games.local["game_data"][self.gameid] = {"files":[]}
            if not self.games.local["game_data"][self.gameid]["files"]:
                self.games.local["game_data"][self.gameid]["files"] = []
            self.games.local["game_data"][self.gameid]["files"].append(file)
        else:
            file = self.games.local["game_data"][self.gameid]["files"][0]
        file["type"] = "exe"
        if self.sources[0]["source"] in ["gba","snes","n64","nds"]:
            file["type"] = "rom"
        file["path"] = value
        print("set path:",self.games.local["game_data"][self.gameid]["files"])

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
        self.local = {}
        self.source_definitions = {}
    def load(self,game_db_file,local_db_file):
        self.load_games(game_db_file)
        self.load_local(local_db_file)
        sources.register_sources(self.source_definitions)
    def load_games(self,file):
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
            self.games[k].games = self
        if not self.multipack:
            self.multipack = load_data.get("multipack",{})
        self.actions = load_data.get("actions",[])
        self.source_definitions.update(sources.default_definitions.copy())
        self.source_definitions.update(load_data.get("source_definitions",{}).copy())
    def load_local(self,file):
        if not os.path.exists(file):
            print("Warning, no local save file to load:",file)
            return
        f = open(file,"r")
        d = f.read()
        f.close()
        self.local_translate_json(d)
    def local_translate_json(self,d):
        self.local = {"game_data":{}}
        load_data = json.loads(d)
        self.local.update(load_data)
    def save_games_data(self):
        save_data = {"games":{}}
        for k in self.games:
            save_data["games"][k] = self.games[k].dict()
        save_data["actions"] = self.actions
        save_data["multipack"] = self.multipack
        save_data["source_definitions"] = self.source_definitions
        return json.dumps(save_data,sort_keys=True,indent=4)
    def save_games(self,file):
        sd = self.save_games_data()
        f = open(file,"w")
        f.write(sd)
        f.close()
    def save_local(self,file):
        sd = json.dumps(self.local,sort_keys=True,indent=4)
        f = open(file,"w")
        f.write(sd)
        f.close()
    def save(self,game_db_file,local_db_file):
        self.save_games(game_db_file)
        self.save_local(local_db_file)
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

        print(game.gameid,"should be in self.games")
        if game.gameid in self.games:
            print(game.gameid,"is in games")
            ids.append(game.gameid)

        for oid in ids:
            if game.same_game(self.games[oid]):
                list.append(self.games[oid])
            elif game.gameid==oid:
                print("sameid:",game.gameid)
                list.append(self.games[oid])
        print("similar games:",list)
        return list
    def correct_gameid(self,oldid,gameid):
        newid = gameid
        next=0
        while newid in self.games:
            collision = hmac.new(bytes("","utf8"))
            collision.update(bytes(str(oldid)+str(next),"utf8"))
            next+=1
            newid = collision.hexdigest()
        if newid!=oldid:
            #TODO: kind of bad, Force all references to update their key
            for chk_game in self.games.values():
                for child in chk_game.package_data.get("contents",[]):
                    if child["gameid"] == oldid:
                        print("changed child id",child["gameid"],"to",newid,"on",chk_game.gameid)
                        child["gameid"] = newid
                parent = chk_game.package_data.get("parent",{})
                if parent:
                    if parent.get("gameid",{}) == oldid:
                        print("changed parent id",parent["gameid"],"to",newid,"on",chk_game.gameid)
                        parent["gameid"] = newid
            if oldid in self.local["game_data"]:
                self.local["game_data"][newid] = self.local["game_data"][oldid]
                del self.local["game_data"][oldid]
        return newid
    def update_id(self,oldid,newid):
        """Convert a game from oldid to newid,
        if newid already exists; modify it"""
        print("updating id",oldid,newid)
        if oldid==newid:
            return newid
        return self.correct_gameid(oldid,newid)
    def find_matching_game(self,game):
        for g in self.get_similar_games(game):
            if g.same_game(game):
                return g
    def force_update_game(self,oldid,game):
        if oldid in self.games:
            cur_game = self.games[oldid]
        else:
            cur_game = self.find_matching_game(game)
        game.gameid = self.update_id(oldid,game.gameid)
        if cur_game:
            diff = changed(cur_game.dict(),game.dict())
            if diff:
                print("UPDATE CHANGED GAME")
                self.actions.append(add_action("update",game=game.dict(),changes=diff))
                if oldid in self.games:
                    del self.games[oldid]
                self.games[game.gameid] = game
            else:
                print("UPDATE... did not change game")
        else:
            self.actions.append(add_action("add",game=game.dict()))
            print("ADD GAME ACTION")
            print("adding",game.gameid,game.source_match)
            game.data_changed_date = now()
            self.games[game.gameid] = game
        return game
    def update_game(self,gameid,game):
        assert(isinstance(game,Game))
        game.games = self

        cur_game = self.find_matching_game(game)
        assert game is not cur_game

        if not cur_game:
            game.gameid = self.correct_gameid(gameid,gameid)
            self.actions.append(add_action("add",game=game.dict()))
            print("ADD GAME ACTION")
            print("adding",game.gameid,game.source_match)
            game.data_changed_date = now()
            self.games[game.gameid] = game
            return game
        previous_data = cur_game.dict()
        gameid = self.update_id(cur_game.gameid,gameid)
        if gameid!=cur_game.gameid:
            del self.games[cur_game.gameid]
            cur_game.gameid = gameid
            self.games[gameid] = cur_game
        if game.name != cur_game.name:
            cur_game.name = game.name
        if game.icon_url:
            cur_game.icon_url = game.icon_url
        if game.playtime > cur_game.playtime:
            cur_game.playtime = game.playtime
        if game.finished:
            cur_game.finished = 1
        if game.lastplayed and (not cur_game.lastplayed or stot(game.lastplayed)>stot(cur_game.lastplayed)):
            cur_game.lastplayed = game.lastplayed
        if game.sources != cur_game.sources:
            cur_game.sources = game.sources
        cur_game.package_data = game.package_data.copy()
        diff = changed(previous_data,cur_game.dict())
        if diff:
            cur_game.data_changed_date = now()
            self.actions.append(add_action("update",game=game.dict(),changes=diff))
            print("update 2",cur_game.gameid,cur_game.source_match,">",game.name.encode("utf8"),game.source_match)
        else:
            print("no updates to",cur_game.gameid,cur_game.source_match)
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
            #crash
            def key(game):
                if game.data_changed_date:
                    return -time.mktime(stot(game.data_changed_date))
                return -time.mktime(stot("23:39:03 1980-07-16"))
            return sorted(v,key=key)
    def get_package_for_game_converter(self,game):
        #TODO: Only implemented here for conversion from old data, once migrated can remove
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
    def get_package_for_game(self,game):
        if game.is_in_package:
            package_id = game.package_data["parent"]["gameid"]
            return self.games[package_id]
    def games_for_pack(self,pack):
        gamelist = []
        if pack.is_package:
            for game in pack.package_data["contents"]:
                gamelist.append(self.games[game["gameid"]])
        return gamelist
    def delete(self, game):
        self.actions.append(add_action("delete",game=game.dict()))
        del self.games[game.gameid]
    def play(self, game):
        self.actions.append(add_action("play",game=game.dict()))
    def stop(self, game):
        self.actions.append(add_action("stop",game=game.dict()))
