import os
import sys
print (sys.version)
import pygame
import pygame.freetype
import json
import time

from code.apis import giantbomb, steamapi, gogapi, humbleapi, thegamesdb
#from code.interface import account, gameoptions, base_paths, logwindow, sourcesform, emulatorform
from code import games,syslog
from code.resources import icons,enc

screen = pygame.display.set_mode([1920,1080],pygame.FULLSCREEN|pygame.DOUBLEBUF)
pygame.freetype.init()

def init_config(app):
    crypter = enc.Crypter()
    from code.appdirs import appdirs
    path_base = appdirs.user_data_dir("MyBacklog").replace("\\","/")
    if not os.path.exists(path_base):
        os.makedirs(path_base)
    root = {"games":"",
                "local":path_base+"/local.json",
                "accounts":path_base+"/accounts.json",
                "root_config":path_base+"/root.json",
                "root":path_base,
                "rk":str(crypter.root_key),
                "icon_size":300
            }
    if os.path.exists(root["root_config"]):
        f = open(root["root_config"])
        d = json.loads(f.read())
        f.close()
        root.update(d)
    config = root
    crypter.root_key = eval(config["rk"])
    
    account = {"steam": {"api": "", "shortcut_folder": "", "id": "","userfile":""},
               "gog": {"user": "", "pass": ""},
               "humble": {"username": "", "password": ""}}
    if os.path.exists(root["accounts"]):
        try:
            saved_accounts = json.loads(crypter.read(open(root["accounts"]).read(),"{}"))
        except:
            raise
            saved_accounts = {}
        for k in saved_accounts:
            account[k].update(saved_accounts[k])
    set_accounts(account,app)
    
    for path in ["/cache","/cache/batches","/cache/icons","/cache/extract"]:
        if not os.path.exists(root["root"]+path):
            os.mkdir(root["root"]+path)
        
    return config
    
def set_accounts(account,app):
    gog = gogapi.Gog(app,account["gog"]["user"],account["gog"]["pass"])
    steam = steamapi.Steam(app,account["steam"]["api"],account["steam"]["id"],account["steam"]["userfile"],account["steam"]["shortcut_folder"])
    humble = humbleapi.Humble(app,account["humble"]["username"],account["humble"]["password"])
    #thegamesdb = thegamesdb.thegamesdb(app)
    #giantbomb = giantbomb.giantbomb(app)
    games.sources.SteamSource.api = steam
    games.sources.GogSource.api = gog

#~ def save_config(config):
    #~ f = open(config["root_config"],"w")
    #~ f.write(json.dumps(config,indent=4,sort_keys=True))
    #~ f.close()
        
def init_gamelist(app,config):
    gamelist = games.Games()
    print("loading games",config["games"])
    gamelist.load(config["games"],config["local"])
    return gamelist
    
font = pygame.freetype.SysFont("JosefinSlab-Regular.ttf",16)

icon_cache = {}
text_cache = {}

def get_text(game,selected):
    if (game.name,selected) not in text_cache:
        text = game.name+" ... "+game.playtime_hours_minutes+" last:"+game.last_played_nice
        color = [250,250,250]
        if selected:
            color = [250,150,150]
        graphic,size = font.render(text,color)
        text_cache[(game.name,selected)] = (graphic,size)
    return text_cache[(game.name,selected)]

class MyBacklogApp:
    running = True
    selected = 0
    gamelist = None
    running_game = None
    timer_started = 0
    scrolling = 0
    scroll_speed = 0.0
    offset = 0
    show = 20
    game_list = []
    def __init__(self):
        pass
    def log(self,*text):
        print(text)
    def input(self):
        if not self.game_list:
            self.game_list = self.gamelist.list()
        for evt in pygame.event.get():
            if evt.type==pygame.QUIT or (evt.type==pygame.KEYDOWN and evt.key==pygame.K_ESCAPE):
                self.running = False
            if evt.type==pygame.KEYDOWN and evt.key==pygame.K_UP:
                self.scrolling = -1
                self.selected = self.selected-1
            if evt.type==pygame.KEYDOWN and evt.key==pygame.K_DOWN:
                self.scrolling = 1
                self.selected = self.selected+1
            if evt.type==pygame.KEYUP and evt.key==pygame.K_UP:
                self.scrolling = 0
                self.scroll_speed = 0
            if evt.type==pygame.KEYUP and evt.key==pygame.K_DOWN:
                self.scrolling = 0
                self.scroll_speed = 0
            if evt.type==pygame.KEYDOWN and evt.key==pygame.K_RETURN:
                if not self.running_game:
                    self.run_game(self.gamelist.list()[self.selected])
                else:
                    self.stop_game(self.running_game)
        self.scroll_speed += self.scrolling*0.02
        if self.scroll_speed>1:
            self.selected = self.selected+1
            self.scroll_speed = 0.8
        if self.scroll_speed<-1:
            self.selected = self.selected-1
            self.scroll_speed = -0.8
        while self.selected>=self.offset+self.show:
            self.offset+=1
        while self.selected<self.offset:
            self.offset-=1
        if self.running_game:
            time.sleep(1)
    def draw(self):
        screen.fill([0,0,0])
        x,y=20,1
        if self.running_game:
            screen.blit(font.render("Playing "+self.running_game.name+" [enter to stop]",[250,150,150])[0],[5,5])
        else:
            for i,game in enumerate(self.game_list[self.offset:self.offset+self.show]):
                graphic,size = get_text(game,i+self.offset==self.selected)
                screen.blit(graphic,dest=[x,y])
                icon = icons.icon_for_game(game,size[1],icon_cache,self.config["root"],"icon","pygame")
                if icon:
                    screen.blit(icon,dest=[0,y])
                y += size[1]+2
        pygame.display.flip()
    def run_game(self,game,track_time=True,launch=True):
        if self.running_game: return
        if track_time:
            self.timer_started = time.time()
        print ("run game",game.name,game.gameid)

        self.running_game = game
        if launch:
            game.run_game(self.config["root"])
    def stop_game(self,game):
        self.running_game = None
        game.played()
        elapsed_time = time.time()-self.timer_started
        game.playtime += elapsed_time
        game.priority = -1
        text_cache.clear()
        self.save()
    def save(self):
        self.gamelist.save(self.config["games"],self.config["local"])

app = MyBacklogApp()
app.config = init_config(app)
app.gamelist = init_gamelist(app,app.config)

while app.running:
    app.draw()
    app.input()