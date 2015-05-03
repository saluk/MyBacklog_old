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

import json
f = open("../data/gamesv002.json")
old_data = json.loads(f.read())
f.close()

f = open("../data/gamesv003.json","w")
f.write(json.dumps(v002_to_v003(old_data),indent=2,sort_keys=True))
f.close()