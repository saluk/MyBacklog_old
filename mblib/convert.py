import copy
import games

def v002_to_v003(inp):
    """Take source information out of root and put into sources,
    and change the key to be a key generated from the name.
    Also, record the date added to the database.:

    "steam_218090": {
            "finished": 0,
            "genre": "strategy",
            "gogid": "",
            "hidden": 0,
            "humble_machinename": "",
            "humble_package": "",
            "icon_url": "http://media.steampowered.com/steamcommunity/public/images/apps/218090/acc842bdd4d3ef30d7cc2d2ba2da3700e07b9f6a.jpg",
            "install_path": "",
            "is_package": 0,
            "lastplayed": null,
            "name": "Unity of Command",
            "notes": "",
            "packageid": "",
            "playtime": 0.0,
            "priority": 0,
            "source": "steam",
            "steamid": 218090,
            "website": ""
        },

    >

    "Unity of Command": {
    "sources":[
        {"source":"steam","id":218090}
    ],
    "icon_url": "http://media.steampowered.com/steamcommunity/public/images/apps/218090/acc842bdd4d3ef30d7cc2d2ba2da3700e07b9f6a.jpg",
    "name": "Unity of Command",
    "finished": 0,
    "genre": "strategy",
    "hidden": 0,
    "lastplayed": null,
    "notes": "",
    "playtime": 0.0,
    "priority": 0,
    "import_date": null
    }
    """
    out = {}
    out["multipack"] = inp["multipack"]
    out["actions"] = []

    source_keys = [("steamid","id"),("gogid","id"),("humble_machinename","id"),("humble_package","package")]
    other_keys = ["finished","genre","hidden","icon_url","install_path","is_package","lastplayed",
                  "name","notes","packageid","playtime","priority","website"]
    out["games"] = {}
    print("starting:",len(inp["games"]))
    ran = 0
    for key in inp["games"]:
        ran += 1
        game = inp["games"][key]
        if not game["name"]:
            print("ERROR",key)
            continue
        new = {}

        def matchgame(a,b):
            for k in ["steamid","gogid","humble_machinename","install_path"]:
                if a[k] != b[k]:
                    return False
            return True

        new["import_date"] = ""
        for a in inp["actions"]:
            if a["type"] == "addgame" and matchgame(a["game"],game):
                new["import_date"] = a["time"]

        new["finish_date"] = ""
        for a in inp["actions"]:
            if a["type"] == "updategame" and matchgame(a["game"],game):
                changes = a["changes"].get("_set_",[])
                for c in changes:
                    if c.get("k","") == "finished" and c.get("ov",None) != 1 and c.get("v",None):
                        new["finish_date"] = a["time"]

        new["sources"] = []
        sourceinfo = {}
        sourceinfo["source"] = game["source"]
        for s in source_keys:
            if game[s[0]]:
                sourceinfo[s[1]] = game[s[0]]
        new["sources"].append(sourceinfo)
        for k in other_keys:
            new[k] = game[k]

        dest_key = game["name"]
        i = 0
        while dest_key in out["games"]:
            dest_key = game["name"] + "."+str(i)
            i += 1
            print("conflict",dest_key)
        new["gameid"] = dest_key
        out["games"][dest_key] = new
    print("looped",ran,"times")
    print(len(out["games"]),len(inp["games"]))
    return out

def v003_to_v004(inp):
    """
    Convert gameid field and key to the simplified game.name_stripped
    """
    out = {}
    out["multipack"] = inp["multipack"]
    out["actions"] = []
    out["games"] = {}
    print("starting:",len(inp["games"]))
    ran = 0
    for key in inp["games"]:
        ran += 1
        game = inp["games"][key]
        if not game["name"]:
            print("ERROR",key)
            continue
        new = copy.deepcopy(game)

        game = data.Game(**game)
        new["gameid"] = game.name_stripped
        dest_key = new["gameid"]+".0"
        i = 0
        while dest_key in out["games"]:
            dest_key = game.name_stripped + "."+str(i)
            i += 1
            print("conflict",dest_key)
        new["gameid"] = dest_key
        out["games"][dest_key] = new
    print("looped",ran,"times")
    print(len(out["games"]),len(inp["games"]))
    return out

def v004_to_v005(inp):
    """
    All games are given an update_date datetime field, defaults to very_old
    If there is an update command in actions, set the update_date to the most recent of those
    """
    out = {}
    out["multipack"] = inp["multipack"]
    out["actions"] = []
    out["games"] = {}
    print("starting:",len(inp["games"]))
    ran = 0
    for key in inp["games"]:
        ran += 1
        game = inp["games"][key]
        if not game["name"]:
            print("ERROR",key)
            continue
        new = copy.deepcopy(game)

        if new["lastplayed"]:
            new["data_changed_date"] = new["lastplayed"]
        elif new["finish_date"]:
            new["data_changed_date"] = new["finish_date"]
        elif new["import_date"]:
            new["data_changed_date"] = new["import_date"]
        else:
            new["data_changed_date"] = None

        def matchgame(a,b):
            for k in ["gameid"]:
                if a[k] != b[k]:
                    return False
            return True

        for a in inp["actions"]:
            if matchgame(a["game"],game):
                if not new["data_changed_date"] or data.stot(new["data_changed_date"])<data.stot(a["time"]):
                    new["data_changed_date"] = a["time"]

        out["games"][new["gameid"]] = new
    print("looped",ran,"times")
    print(len(out["games"]),len(inp["games"]))
    return out

def v005_to_v006(inp):
    """
    Games that are a package (is_package==True) will have:
    package_data: {"type":"bundle","contents":[(gameid,name) for all games in package]}

    Games that are in a package (is_package==False, but have package info elsewhere)
    package_data: {"type":"content","parent":[(gameid,name) for package],"source_info":{"gog_id","humble_package"}}
    source_info is just for auditing

    Games that are not a package, nor are they in a package (is_package==False, no other packaging keys),
    package_data: {}

    delete is_package identifyer (gotten with package_data)
    """

    gamelist = games.Games()
    gamelist.translate_json(json.dumps(inp))

    out = {}
    out["multipack"] = inp["multipack"]
    out["actions"] = []
    out["games"] = {}
    print("starting:",len(inp["games"]))
    ran = 0
    for key in inp["games"]:
        ran += 1
        game = inp["games"][key]
        if not game["name"]:
            print("ERROR",key)
            continue
        new = copy.deepcopy(game)

        game = games.Game(**game)

        package = gamelist.get_package_for_game_converter(game)

        def get_source_info(source):
            if source["source"] == "gog":
                return {"package_source":"gog","package_id":source["id"],"id_within_package":game.packageid}
            elif source["source"] == "humble":
                return {"package_source":"humble","package_id":source["package"],"id_within_package":source["id"]}

        assert len(game.sources)==1

        if game.is_package:
            print("Converting package:",game.gameid)
            inside = game.games_for_pack_converter(gamelist)
            new["package_data"] = {"type":"bundle","contents":[{"gameid":g.gameid,"name":g.name} for g in inside],
                                   "source_info":get_source_info(game.sources[0])}
        else:
            if package:
                print("Converting content item:",game.gameid)
                source_info = get_source_info(game.sources[0])
                new["package_data"] = {"type":"content","parent":{"gameid":package.gameid,"name":package.name},
                                       "source_info":source_info}
            else:
                new["package_data"] = {}
        del new["is_package"]
        del new["packageid"]

        out["games"][game.gameid] = new
    print("looped",ran,"times")
    print(len(out["games"]),len(inp["games"]))
    return out

def v006_to_v007(inp):
    """
    Converts install_path to external local exe information

    "mother_1.0": {
            "gameid": "mother_1.0",
            "install_path": "C:\\emu\\gb\\mother12.gba",
            "lastplayed": "13:32:54 2015-01-19",
            "name": "Mother 1",
            "website": "",
            "sources": [
                {
                    "source": "gba"
                }
            ],
        },

    >>>

    local_db = {
        "game_data":{
            "mother_1.0":{
                "files": [
                    {"type":"rom","primary":True,"path":"C:\\emu\\gb\\mother12.gba","source":"gba"}
                ]
            }
        },
        "emulators":{
            "gba":{
                "path":"C:\\emu\\retroarch\\retroarch.exe",
                "cmd":"$program -c C:\\emu\\retroarch\\retroarch-gba.cfg $path"
            }
        }
    }
    """

    gamelist = games.Games()
    gamelist.translate_json(json.dumps(inp))

    out_games = {}
    out_local = {"game_data":{},"emulators":{}}
    out_games["multipack"] = inp["multipack"]
    out_games["actions"] = inp["actions"]
    out_games["games"] = {}
    print("starting:",len(inp["games"]))
    ran = 0
    for key in inp["games"]:
        ran += 1
        game = inp["games"][key]
        if not game["name"]:
            print("ERROR",key)
            continue
        new = copy.deepcopy(game)

        game = games.Game(**game)

        if game.install_path:
            li = []
            out_local["game_data"][game.gameid] = {"files":li}
            for s in game.sources:
                file = {"source":s,"primary":True}
                if s["source"] in ["gba","snes","n64","nds"]:
                    file.update({"type":"rom","path":game.install_path})
                else:
                    file.update({"type":"exe","path":game.install_path})
                li.append(file)

        del new["install_path"]
        out_games["games"][game.gameid] = new
    print("looped",ran,"times")
    print(len(out_games["games"]),len(inp["games"]))
    return out_games,out_local

def v007_to_v008(gdb_inp,ldb_inp):
    """
    Converts
    """

    gamelist = games.Games()
    gamelist.translate_json(json.dumps(gdb_inp))

    out_games = {}
    out_local = {"game_data":{},"emulators":{}}
    out_games["multipack"] = gdb_inp["multipack"]
    out_games["actions"] = gdb_inp["actions"]
    out_games["games"] = {}
    print("starting:",len(gdb_inp["games"]))
    ran = 0
    collisions = 0
    changed_keys = {}
    for key in gdb_inp["games"]:
        ran += 1
        game = gdb_inp["games"][key]
        if not game["name"]:
            print("ERROR",key)
            continue

        new = copy.deepcopy(game)

        game = games.Game(**game)
        orig = game.dict()
        oldid = game.gameid
        game.generate_gameid()
        new["gameid"] = game.gameid

        changed_keys[oldid] = new["gameid"]

        cur_local = ldb_inp["game_data"].get(oldid,None)

        if game.gameid in out_games["games"]:
            collisions += 1
            print("COLLISION:")
            print(new)
            print(out_games["games"][game.gameid])
        out_games["games"][game.gameid] = new
        if cur_local:
            out_local["game_data"][game.gameid] = cur_local

    for key in out_games["games"]:
        game = out_games["games"][key]
        if not game["package_data"]:
            continue
        if game["package_data"]["type"] == "bundle":
            for child in game["package_data"]["contents"]:
                child["gameid"] = changed_keys[child["gameid"]]
        elif game["package_data"]["type"] == "content":
            parent = game["package_data"]["parent"]
            if parent["gameid"] in changed_keys:
                parent["gameid"] = changed_keys[parent["gameid"]]

    print("looped",ran,"times")
    print(len(out_games["games"]),len(gdb_inp["games"]))
    print(collisions,len(gdb_inp["games"])-collisions)
    return out_games,out_local

import json
f = open("../data/gamesv007.json")
gdb = json.loads(f.read())
f.close()

l = open("../data/localv001.json")
ldb = json.loads(l.read())
l.close()

gdb,ldb = v007_to_v008(gdb,ldb)
g = open("../data/gamesv008.json","w")
g.write(json.dumps(gdb,indent=4,sort_keys=True))
g.close()

l = open("../data/localv002.json","w")
l.write(json.dumps(ldb,indent=4,sort_keys=True))
l.close()