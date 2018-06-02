import os
import sys
import subprocess
import webbrowser
import psutil

run_with_steam = 1
#   NEW METHOD TO RUN THROUGH STEAM:
#   Export function which creates shortcuts to all non-steam games that aren't in steam yet
#   Manually creat shortcut for often played game, and put it in cache/steamshortcuts
#   When running a game, if a steam shortcut exists in cache/steamshortcuts, run that

class Source:
    extra_args = []
    source_args = []
    generate_website = None
    runnable = True
    def __init__(self,name,app):
        """app = app should contain fields for api's sources may need"""
        self.name = name
        self.app = app
    def args(self):
        return self.extra_args
    def is_installed(self,game,source):
        return True
    def needs_download(self,game,source):
        if self.is_installed(game,source):
            return False
        return True
    def download_link(self,game,source):
        return ""
    def download_method(self,game,source):
        if game.download_link:
            webbrowser.open(game.download_link)
    def uninstall(self):
        return
    def run_game(self,game,source,cache_root):
        return
    def rom_extension(self,game):
        return ""
    def game_is_running(self, game, data):
        """By default return true and force user to control when to stop the timer"""
        return True

class ExeSource(Source):
    """Definition of a source of games"""
    def args(self):
        """Return editable arguments that are unique to this source
        Defaults to install_path as that is pretty common"""
        return [("install_path","s")]+self.extra_args
    def is_installed(self,game,source):
        return os.path.exists(game.get_path())
    def uninstall(self,game,source):
        if game.install_folder:
            subprocess.Popen(["explorer.exe",game.install_folder], cwd=game.install_folder, stdout=sys.stdout, stderr=sys.stderr)
    def get_run_args(self,game,source,cache_root,write_batch=True):
        """Returns the method to run the game. Defaults to using a batch file to run the install_path exe"""
        folder = game.install_folder #Navigate to executable's directory
        root = folder.split("\\",1)[0]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        import winshell, shlex
        path = game.get_path()
        if path.endswith(".lnk"):
            with winshell.shortcut(path) as link:
                print(dir(link))
                args = [link.path] + shlex.split(link.arguments)
                folder = link.working_directory
                search = os.path.basename(link.path)
                print(folder)
        else:
            #Make batch file to run
            filepath = os.path.basename(path)
            exe,args = filepath.split(".exe")
            exe = exe+".exe"
            search = exe
            if write_batch:
                with open(cache_root+"/cache/batches/"+game.gameid+".bat", "w") as f:
                    f.write('%s\ncd "%s"\n'%(root,folder))
                    f.write('"%s" %s\n'%(exe,args))
            args = [game.gameid+".bat"]
            folder = os.path.abspath(cache_root+"/cache/batches/")
        return args,folder,search
    def run_game(self,game,source,cache_root):
        creationflags = 0
        shell = True
        if sys.platform=='darwin':
            shell = False
        args,folder,search = self.get_run_args(game,source,cache_root)
        print("run args:",args,folder)

        if args and folder:
            print(args)
            curdir = os.path.abspath(os.curdir)
            os.chdir(folder)
            print(os.path.abspath(os.curdir))
            self.running = subprocess.Popen(args, cwd=folder, stdout=sys.stdout, stderr=sys.stderr, creationflags=creationflags, shell=shell)
            print("subprocess open")
            os.chdir(curdir)
    def game_is_running(self, game, data):
        args,folder,search = self.get_run_args(game,data,"",write_batch=False)
        print("search:",search)
        procs = [proc.name() for proc in psutil.process_iter() if search.lower() in proc.name().lower()]
        return bool(procs)
            
class HumbleSource(ExeSource):
    source_args = [("id","s"),("package","s")]

class SteamSource(Source):
    """Needs .api to be set to steamapi.Steam"""
    extra_args = []
    source_args = [("id","s")]
    def run_game(self,game,source,cache_root):
        if "id" not in source:
            return
        webbrowser.open("steam://rungameid/%s"%source["id"])
    def missing_steam_launch(self,game,source):
        return False
    def download_method(self,game,source):
        if "id" not in source:
            return
        webbrowser.open("steam://install/%s"%source["id"])
    def uninstall(self,game,source):
        if "id" not in source:
            return
        webbrowser.open("steam://uninstall/%s"%source["id"])
    def is_installed(self,game,source):
        if "id" not in source:
            return
        return self.api.is_installed(source["id"])
    def generate_website(self,game,source):
        if "id" in source:
            return "http://store.steampowered.com/app/%s"%source["id"]
        return ""
    def game_is_running(self, game, data):
        if self.app.steam.running_game_id() == data["id"]:
            return True

class GogSource(ExeSource):
    """Needs .api to be set to gogapi.Gog"""
    extra_args = []
    source_args = [("id","s"),("id2","s")]
    def args(self):
        return [("install_path","s")]+self.extra_args
    def download_link_downloader(self,game,source):
        if "id" not in source:
            return ""
        return "gogdownloader://%s/installer_win_en"%source["id"]
    def download_link_galaxy(self,game,source):
        if "id2" not in source:
            return ""
        return "goggalaxy://openGameView/%s"%source["id2"]
    download_link = download_link_galaxy
    def generate_website(self,game,source):
        if "id" in source:
            return "https://www.gog.com/game/%s"%source["id"]
        return ""
    def run_game(self,game,source,cache_root):
        if game.get_path():
            return super(GogSource,self).run_game(game,source,cache_root)
        webbrowser.open("goggalaxy://openGameView/%s"%source["id2"])
    def is_installed(self,game,source):
        if game.get_path():
            return True
        if "id2" not in source:
            return False
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\GOG.com\\Games") as key:
            gog_games = [winreg.EnumKey(key,i) for i in range(winreg.QueryInfoKey(key)[0])]
        for gog_game in gog_games:
            gamereg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\GOG.com\\Games\\"+gog_game)
            if winreg.QueryValueEx(gamereg,"gameID")[0] != source["id2"]:
                continue
            return True

class EmulatorSource(ExeSource):
    source_args = []
    def args(self):
        return [("install_path","s")]+self.extra_args
    def get_run_args(self,game,source,cache_root,write_batch=False):
        emu_info = game.games.local["emulators"][self.name]
        args = emu_info["args"]+[game.get_path()]
        path,exe = os.path.split(args[0])
        return args,path,exe
    def rom_extension(self,game):
        emu_info = game.games.local["emulators"][self.name]
        return emu_info.get("rom_extension","*.*")

class OfflineSource(Source):
    def args(self):
        return self.extra_args
    def is_installed(self,game,source):
        return False

class LinkSource(OfflineSource):
    source_args = [("id","s")]
    def is_installed(self,game,source):
        return False

default_definitions = {
    "gog":{
        "class":"GogSource",
        "editable":False
    },
    "steam":{
        "class":"SteamSource",
        "editable":False
    },
    "offline":{
        "class":"OfflineSource",
    },
    "none":{
        "class":"ExeSource",
        "editable":False
    },
    "humble":{
        "class":"HumbleSource",
        "editable":False
    },
    "origin":{
        "class":"ExeSource"
    },
    "gamersgate":{
        "class":"ExeSource"
    },
    "itch":{
        "class":"ExeSource"
    },
    "offline":{
        "class":"OfflineSource"
    },
    "gba":{
        "class":"EmulatorSource"
    },
    "snes":{
        "class":"EmulatorSource"
    },
    "n64":{
        "class":"EmulatorSource"
    },
    "nds":{
        "class":"EmulatorSource"
    },
    "thegamesdb":{
        "class":"LinkSource"
    },
    "giantbomb":{
        "class":"LinkSource"
    }
}
all = {}
def register_sources(definitions,app):
    for sourcekey in definitions:
        source = definitions[sourcekey]
        cls = eval(source["class"])
        inst = cls(name=sourcekey,app=app)
        for key in source:
            if key in ["class"]:
                continue
            setattr(inst,key,source[key])
        all[sourcekey] = inst
        
classes = []
for x in dir():
    if "Source" in x and not x == "Source":
        classes.append(x)
        
assert(classes)