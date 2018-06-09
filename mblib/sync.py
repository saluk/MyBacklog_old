import requests
import shutil, os

from mblib import games

app = None
user = "saluk"
host = "dawnsoft.org:8000"

def get_server_revision():
    r = requests.get("http://%s/games_revision?user=%s"%(host,user))
    return r.json()["server_revision"]

def download_games():
    print("DOWNLOAD GAMES")
    game_file = app.config["games"]
    downloading = game_file+".d"
    r = requests.get("http://%s/game_database?user=%s"%(host,user),stream=True)
    read = 0
    with open(downloading,"wb") as f:
        while 1:
            next = r.raw.read(128)
            if not len(next):
                break
            read += len(next)
            f.write(next)
    print("read",read)
    
def refresh_games():
    print("REFRESHING GAMES")
    game_file = app.config["games"]
    gamedb = app.games
    downloading = game_file+".d"
    downloaded = games.Games()
    downloaded.load(downloading)
    #force update all games from server into games
    for g in downloaded.games.values():
        gamedb.force_update_game(g.gameid,g)
    #Delete games that are gone on server
    for gameid in list(gamedb.games.keys()):
        if gameid in gamedb.games and gameid not in downloaded.games:
            print("DELETING",gamedb.games[gameid])
            del gamedb.games[gameid]
    #Update local revision to match server
    gamedb.revision = downloaded.revision

def download():
    print("check to download")
    if not app:
        return
    games = app.games
    revision = get_server_revision()
    if not revision:
        return
    if revision < games.revision:
        raise Exception("MAJOR ERROR, server is older than client. shouldn't happen")
    if revision == games.revision:
        #We are already in sync
        return
    download_games()
    refresh_games()
    
def upload():
    print("UPLOAD GAMES")
    game_file = app.config["games"]
    with open(game_file,"rb") as f:
        data = f.read()
    r = requests.put("http://%s/game_database?user=%s"%(host,user),data=data,headers={"Content-Type":"application/ubjson"})
    print(r.json())
    if r.json().get("error",""):
        raise Exception(r.text)
