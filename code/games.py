#!python3
import os
import time
import datetime
import json
import hmac
import copy
from code import sources,syslog

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
def sec_to_ts(sec):
    """Convert an amount of seconds as a string into a time delta"""
    return ttos(time.localtime(sec))
def ts_to_sec(ts):
    """Convert an amount of seconds as a string into a time delta"""
    return time.mktime(stot(ts))

PRIORITIES = {-1:"now playing",0:"unprioritized",1:"soon",2:"later",3:"much later",5:"next year",99:"probably never"}

class InvalidId(Exception):
    pass
BAD_GAMEID = InvalidId("Do not save me")

def get_source(s):
    return sources.all[s]
    
def source_id(s):
    return s["source"] + "_" + str(s.get("id2",s.get("id","")))

class Game:
    args = [("name","s"),("playtime","f"),("lastplayed","d"),("genre","s"),("icon_url","s"),("logo_url","s"),
    ("notes","s"),("priority","p"),("priority_date","d"),("website","s"),("import_date","d"),("finish_date","d")]
    def __init__(self,**kwargs):
        dontsavekeys = set(dir(self))
        self.gameid = BAD_GAMEID

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
        self.images = []
        self.notes = ""
        self.priority = 0
        self.priority_date = ""
        self.local_files = []

        self.website = ""
        self.savekeys = set(dir(self)) - dontsavekeys
        for k in kwargs:
            if k == "icon_url":
                self.images.append({"size":"icon","url":kwargs[k]})
            elif k == "logo_url":
                self.images.append({"size":"logo","url":kwargs[k]})
            elif hasattr(self,k):
                setattr(self,k,kwargs[k])
        if "minutes" in kwargs:
            self.playtime = datetime.timedelta(minutes=kwargs["minutes"]).total_seconds()
        self.games = None
        if "games" in kwargs:
            self.games = kwargs["games"]
    @property
    def icon_url(self):
        for image in self.images:
            if image["size"]=="icon": return image["url"]
        return ""
    @property
    def logo_url(self):
        for image in self.images:
            if image["size"]=="logo": 
                return image["url"]
        return self.icon_url
    @icon_url.setter
    def icon_url(self,url):
        assert url is not None
        for image in self.images:
            if image["size"]=="icon": image["url"] = url
            return
        self.images.append({"size":"icon","url":url})
    @logo_url.setter
    def logo_url(self,url):
        for image in self.images:
            if image["size"]=="logo": image["url"] = url
            return
        self.images.append({"size":"logo","url":url})
    @property
    def name_stripped(self):
        if not self.name:
            return ""
        s = [x.lower() for x in self.name if x.lower() in "abcdefghijklmnopqrstuvwxyz1234567890 "]
        s = "".join(s).replace(" ","_")
        return s
    @property
    def name_ascii(self):
        if not self.name:
            return ""
        s = self.name.encode("ascii","ignore").decode()
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
        #FIXME: this is a really bad hack, especially with sources
        a = self.args[:]
        for i,s in enumerate(self.sources):
            print(get_source(s["source"]))
            print(get_source(s["source"]).extra_args)
            args = []
            for arg in get_source(s["source"]).args():
                args.append(arg)
            a.extend(args)
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
    @property
    def running_source(self):
        """Get the source that will control running the game"""
        for s in self.sources:
            source = get_source(s["source"])
            if source.runnable:
                return source,s
    def run_game(self,cache_root):
        source,data = self.running_source
        return source.run_game(self,data,cache_root)
    def game_is_running(self):
        source,data = self.running_source
        return source.game_is_running(self,data)
    @property
    def rom_extension(self):
        """What extensions roms have"""
        ext = ""
        for s in self.sources:
            ext+=get_source(s["source"]).rom_extension(self)
        return ext
    def dict(self):
        d = {}
        for k in self.savekeys:
            d[k] = getattr(self,k)
        d["sources"] = copy.deepcopy(d["sources"])
        d["images"] = copy.deepcopy(d["images"])
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
            string += source_id(s) + ";"
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
            self.local_files.append(file)
        else:
            file = self.local_files[0]
        file["type"] = "exe"
        if self.sources[0]["source"] in ["gba","snes","n64","nds"]:
            file["type"] = "rom"
        file["path"] = value
        print("set path:",self.local_files)
    def update_dynamic_fields(self):
        if not self.website and self.sources and get_source(self.sources[0]["source"]).generate_website:
            self.website = get_source(self.sources[0]["source"]).generate_website(self,self.sources[0])
    def get_source(self,source_type):
        for s in self.sources:
            if s["source"]==source_type:
                return s
    def update_local_data(self,local_data):
        #If we don't have local info to save, don't save anything
        if not self.local_files:
            return
        if self.gameid not in local_data:
            local_data[self.gameid] = {}
        local_data[self.gameid]["files"] = self.local_files
    def inject_local_data(self,local_data):
        if self.gameid not in local_data:
            return
        self.local_files = local_data[self.gameid]["files"]

test1 = Game(name="blah")
test2 = test1.copy()
test2.name = "blah2"
assert test1.name!=test2.name

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
def nicediff(diff):
    s = ""
    add = diff.get("_add_",[])
    set = diff.get("_set_",[])
    n = {}
    for d in add:
        n[d["k"]] = d
    for d in set:
        n[d["k"]] = d
    for k in sorted(n.keys()):
        s+=k+":"+str(n[k]["v"])+"  "
    return s

class Games:
    def __init__(self,log=None):
        self.games = {}
        self.source_map = {}
        self.multipack = {}
        self.local = {}
        self.source_definitions = {}
        self.log = log or syslog.SysLog()
    def find(self,search):
        if search in self.games:
            return self.games[search]
        def match(search,game):
            if search.lower().strip()==game.name.lower().strip():
                return True
        possible = [g for g in self.games.values() if match(search,g)]
        print(possible)
        if possible:
            return possible[0]
    def load(self,game_db_file,local_db_file):
        self.load_local(local_db_file)
        self.load_games(game_db_file)
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
            self.games[k].inject_local_data(self.local["game_data"])
        if not self.multipack:
            self.multipack = load_data.get("multipack",{})
        self.source_definitions.update(sources.default_definitions.copy())
        loaded_defs =load_data.get("source_definitions",{}).copy()
        for source in loaded_defs:
            if source not in self.source_definitions:
                self.source_definitions[source] = loaded_defs[source]
            self.source_definitions[source].update(loaded_defs[source])
        self.log.write("source definitions: ",self.source_definitions)
    def load_local(self,file):
        if not os.path.exists(file):
            print("Warning, no local save file to load:",file)
            return
        f = open(file,"r")
        d = f.read()
        f.close()
        self.local_translate_json(d)
    def local_translate_json(self,d):
        self.local = {"game_data":{},"emulators":{}}
        load_data = json.loads(d)
        self.local.update(load_data)
    def save_games_data(self):
        save_data = {"games":{}}
        for k in self.games:
            if k == BAD_GAMEID:
                continue
            save_data["games"][k] = self.games[k].dict()
            self.games[k].update_local_data(self.local["game_data"])
        save_data["multipack"] = self.multipack
        save_data["source_definitions"] = self.source_definitions
        return json.dumps(save_data)
    def save(self,game_db_file,local_db_file):
        sd = self.save_games_data()
        with open(game_db_file,"w") as f:
            f.write(sd)
        sl = json.dumps(self.local)
        with open(local_db_file,"w") as f:
            f.write(sl)
    def build_source_map(self):
        """Builds a dictionary map of source_id:game to make it easier to search for a game from
        a given source"""
        self.source_map = {}
        for gameid in self.games:
            game = self.games[gameid]
            keys = []
            for s in game.sources:
                keys.append(source_id(s))
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
            for g in self.source_map.get(source_id(s),[]):
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
        #print("similar games:",list)
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
            if game.priority != cur_game.priority:
                print("set priority date to",now())
                game.priority_date = now()
            diff = changed(cur_game.dict(),game.dict())
            if diff:
                print("UPDATE CHANGED GAME")
                if oldid in self.games:
                    del self.games[oldid]
                self.games[game.gameid] = game
                self.log.write("GAMEDB: Update ",cur_game.gameid," ",nicediff(diff))
            else:
                print("UPDATE... did not change game")
        else:
            print("ADD GAME ACTION")
            print("adding",game.gameid,game.source_match)
            game.data_changed_date = now()
            self.games[game.gameid] = game
            self.log.write("GAMEDB: Add (",game.gameid,",",game.name,")")
        return game
    def update_game(self,gameid,game):
        assert(isinstance(game,Game))
        game.games = self

        cur_game = self.find_matching_game(game)
        assert game is not cur_game

        if not cur_game:
            game.gameid = self.correct_gameid(gameid,gameid)
            print("ADD GAME ACTION")
            print("adding",game.gameid,game.source_match)
            game.data_changed_date = now()
            self.games[game.gameid] = game
            self.log.write("GAMEDB: Add (",game.gameid,",",game.name,")")
            return game
        previous_data = cur_game.dict()
        gameid = self.update_id(cur_game.gameid,gameid)
        if gameid!=cur_game.gameid:
            del self.games[cur_game.gameid]
            cur_game.gameid = gameid
            self.games[gameid] = cur_game
        if game.name != cur_game.name:
            cur_game.name = game.name
        if game.images:
            cur_game.images = game.images[:]
        if "desteam" not in game.notes and game.playtime > cur_game.playtime:
            cur_game.playtime = game.playtime
        if game.finished:
            cur_game.finished = 1
        if game.lastplayed and (not cur_game.lastplayed or stot(game.lastplayed)>stot(cur_game.lastplayed)):
            cur_game.lastplayed = game.lastplayed
        if game.sources != cur_game.sources:
            cur_game.sources = game.sources
        if cur_game.priority_date and stot(game.lastplayed) > stot(game.priority_date):
            cur_game.priority = -1
            print("Set Game Priority")
        genres = []
        for g in [game,cur_game]:
            for x in g.genre.split(";"):
                x = x.strip().lower()
                if not x:
                    continue
                if x not in genres:
                    genres.append(x)
        cur_game.genre = "; ".join(genres)
        cur_game.package_data = game.package_data.copy()
        diff = changed(previous_data,cur_game.dict())
        if diff:
            cur_game.data_changed_date = now()
            print("update 2",cur_game.gameid,cur_game.source_match,">",game.name.encode("utf8"),game.source_match)
            self.log.write("GAMEDB: Update ",previous_data["gameid"]," ",nicediff(diff))
        else:
            print("no updates to",cur_game.gameid,cur_game.source_match)
        return cur_game
    def list(self,sort="priority"):
        v = self.games.values()
        if not sort:
            return v
        elif sort=="priority":
            def k(g):
                if g.finished:
                    return (g.finished,0,-time.mktime(stot(g.lastplayed)),g.name)
                #return (g.finished,g.priority,-time.mktime(stot(g.lastplayed)),g.name)
                return (g.finished,1,-time.mktime(stot(g.lastplayed)),g.name)
            return sorted(v,key=k)
        elif sort=="added":
            def key(game):
                if game.import_date:
                    return -time.mktime(stot(game.import_date))
                return -time.mktime(stot("23:39:03 1970-07-16"))
            return sorted(v,key=key)            
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
        if game.gameid in self.games:
            del self.games[game.gameid]
