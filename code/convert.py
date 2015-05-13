import copy
import data

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

def vunknown(inp):
    """Games have multiple run scenarios which may or may not be tied to a source

        "Grand Theft Auto V": {
            "finish_date": "",
            "finished": 0,
            "gameid": "Grand Theft Auto V",
            "genre": "openworld",
            "hidden": 0,
            "icon_url": "http://media.steampowered.com/steamcommunity/public/images/apps/271590/1e72f87eb927fa1485e68aefaff23c7fd7178251.jpg",
            "import_date": "00:46:13 2015-04-25",
            "install_path": "",
            "is_package": 0,
            "lastplayed": "23:52:07 2015-05-03",
            "name": "Grand Theft Auto V",
            "notes": "",
            "packageid": "",
            "playtime": 17884.00986123085,
            "priority": -1,
            "sources": [
                {
                    "id": 271590,
                    "source": "steam"
                }
            ],
            "website": ""
        },
        "A Story About My Uncle": {
            "finish_date": "",
            "finished": 0,
            "gameid": "A Story About My Uncle",
            "genre": "adventure",
            "hidden": 0,
            "icon_url": "https://www.gog.com/upload/images/2014/05/f4f7f44c4f3d2750d95ce276743ef8c2207638c4_bbC_20.jpg",
            "import_date": "",
            "install_path": "C:\\GOG Games\\A Story About My Uncle\\Launch A Story About My Uncle.lnk",
            "is_package": 0,
            "lastplayed": "18:33:10 2015-04-25",
            "name": "A Story About My Uncle",
            "notes": "",
            "packageid": "",
            "playtime": 9104.872521877289,
            "priority": -1,
            "sources": [
                {
                    "id": "story_about_my_uncle_a",
                    "source": "gog"
                }
            ],
            "website": ""
        },
        "Alone In The Dark": {
            "finish_date": "",
            "finished": 0,
            "gameid": "Alone In The Dark",
            "genre": "action",
            "hidden": 0,
            "icon_url": "",
            "import_date": "",
            "install_path": "",
            "is_package": 1,
            "lastplayed": null,
            "name": "Alone In The Dark",
            "notes": "",
            "packageid": "",
            "playtime": 0,
            "priority": 0,
            "sources": [
                {
                    "id": "alone_in_the_dark",
                    "source": "gog"
                }
            ],
            "website": ""
        },

    >>>

        "Grand Theft Auto V": {
            "finish_date": "",
            "finished": 0,
            "gameid": "Grand Theft Auto V",
            "genre": "openworld",
            "hidden": 0,
            "icon_url": "http://media.steampowered.com/steamcommunity/public/images/apps/271590/1e72f87eb927fa1485e68aefaff23c7fd7178251.jpg",
            "import_date": "00:46:13 2015-04-25",
            "is_package": 0,
            "lastplayed": "23:52:07 2015-05-03",
            "name": "Grand Theft Auto V",
            "notes": "",
            "packageid": "",
            "playtime": 17884.00986123085,
            "priority": -1,
            "sources": [
                {
                    "id": 271590,
                    "source": "steam"
                }
            ],
            "website": "",
            "tasks": [
                {"task":"run",
                "method":"steam_launch"},
            ]
        },
        "A Story About My Uncle": {
            "finish_date": "",
            "finished": 0,
            "gameid": "A Story About My Uncle",
            "genre": "adventure",
            "hidden": 0,
            "icon_url": "https://www.gog.com/upload/images/2014/05/f4f7f44c4f3d2750d95ce276743ef8c2207638c4_bbC_20.jpg",
            "import_date": "",
            "is_package": 0,
            "lastplayed": "18:33:10 2015-04-25",
            "name": "A Story About My Uncle",
            "notes": "",
            "packageid": "",
            "playtime": 9104.872521877289,
            "priority": -1,
            "sources": [
                {
                    "id": "story_about_my_uncle_a",
                    "source": "gog"
                }
            ],
            "website": "",
            "tasks": [
                {"task":"run",
                "method":"shell",
                "path":"C:\\GOG Games\\A Story About My Uncle\\Launch A Story About My Uncle.lnk"},
            ]
        },

        Note, is_package:true = no automatic run tasks
        "Alone In The Dark": {
            "finish_date": "",
            "finished": 0,
            "gameid": "Alone In The Dark",
            "genre": "action",
            "hidden": 0,
            "icon_url": "",
            "import_date": "",
            "is_package": 1,
            "lastplayed": null,
            "name": "Alone In The Dark",
            "notes": "",
            "packageid": "",
            "playtime": 0,
            "priority": 0,
            "sources": [
                {
                    "id": "alone_in_the_dark",
                    "source": "gog"
                }
            ],
            "website": ""
        },

    """
    #Clear output
    out = {}
    #Copy over multipack info for now
    out["multipack"] = inp["multipack"]
    #Clear actions for now
    out["actions"] = []

    out["games"] = {}
    print("starting:",len(inp["games"]))
    ran = 0
    for key in inp["games"]:
        ran += 1
        game = copy.deepcopy(inp["games"][key])
        if not game["name"]:
            print("ERROR",key)
            continue

        def conv(g):
            print("convert",g["name"],g["sources"])
            if g["is_package"]:
                del g["install_path"]
                return g
            g["tasks"] = []
            sources = [x["source"] for x in g["sources"]]
            if "steam" in sources:
                g["tasks"].append({"task":"run","method":"steam_launch"})
            elif g["install_path"]:
                g["tasks"].append({"task":"run","method":"shell","path":g["install_path"]})
            del g["install_path"]
            return g

        out["games"][key] = conv(game)
    print("looped",ran,"times")
    print(len(out["games"]),len(inp["games"]))
    return out


import json
f = open("../data/gamesv003.json")
old_data = json.loads(f.read())
f.close()

f = open("../data/gamesv004.json","w")
f.write(json.dumps(v003_to_v004(old_data),indent=2,sort_keys=True))
f.close()