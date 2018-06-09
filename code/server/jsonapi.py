import hug
import sys,os,traceback
import base64
sys.path.insert(0,"..\\..")
from code import games

def nice_user(user):
    fixed_user = "".join([x for x in user if x in "abcdefghijklmnopqrstuvwxyz0123456789"])
    if user!=fixed_user:
        raise Exception("Username must only contain english alpha and digits")
    return fixed_user
        
class User:
    def __init__(self, user):
        self.user = nice_user(user)
        self.up = os.path.join("__users__",user)
        self.game_path = os.path.join(self.up,"games.json")
    def is_ready(self):
        return os.path.exists(self.game_path)
    def make_ready(self):
        if not os.path.exists(self.up):
            os.mkdir(self.up)

@hug.format.content_type('application/ubjson')            
def raw(data, request=None, response=None):
    return data

@hug.get(examples="user=saluk",output=raw)
def game_database(user):
    user = User(user)
    if not user.is_ready():
        return {"error":"no_games_saved"}
    with open(user.game_path,"rb") as gamef:
        data = gamef.read()
    return data

@hug.put(examples="user=saluk")
def game_database(body,user,input=raw):
    user = User(user)
    user.make_ready()
    try:
        data = body.read()
        gdbmu = games.Games()
        gdbmu.load_games(filedata=data)
    except:
        traceback.print_exc()
        return {"error":"Not a valid game database"}
    try:
        gdbms = games.Games()
        gdbms.load_games(filename=user.game_path)
        if gdbms.revision>gdbmu.revision:
            return {"error":"server has newer revision","client_revision":gdbmu.revision,"server_revision":gdbms.revision}
    except:
        pass
    with open(user.game_path,"wb") as gamef:
        gamef.write(data)
    return {"msg":"success","size":len(data)}
    
@hug.get(examples="user=saluk")
def games_revision(user):
    user = User(user)
    if not user.is_ready():
        return {"server_revision":None}
    try:
        gdbm = games.Games()
        gdbm.load_games(filename=user.game_path)
    except:
        traceback.print_exc()
        return {"error":"Error loading game database"}
    return {"server_revision":gdbm.revision}
    
@hug.post(examples="user=saluk")
def bump_revision(user):
    user = User(user)
    if not user.is_ready():
        return {"error":"user not initialized"}
    try:
        gdbm = games.Games()
        gdbm.load_games(filename=user.game_path)
        gdbm.revision += 1
        gdbm.save(user.game_path)
    except:
        traceback.print_exc()
        return {"error":"Error loading game database"}
    return {"server_revision":gdbm.revision}