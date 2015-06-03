import os
import sys
import subprocess
import webbrowser

run_with_steam = 1
#   NEW METHOD TO RUN THROUGH STEAM:
#   Export function which creates shortcuts to all non-steam games that aren't in steam yet
#   Manually creat shortcut for often played game, and put it in cache/steamshortcuts
#   When running a game, if a steam shortcut exists in cache/steamshortcuts, run that

class Source:
    extra_args = [("source_0_name","s")]
    def __init__(self,name):
        self.name = name
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

class ExeSource(Source):
    """Definition of a source of games"""
    def args(self):
        """Return editable arguments that are unique to this source
        Defaults to install_path as that is pretty common"""
        return [("install_path","s")]+self.extra_args
    def is_installed(self,game,source):
        return game.get_path()
    def uninstall(self,game,source):
        if game.install_folder:
            subprocess.Popen(["explorer.exe",game.install_folder], cwd=game.install_folder, stdout=sys.stdout, stderr=sys.stderr)
    def get_run_args(self,game,source,cache_root):
        """Returns the method to run the game. Defaults to using a batch file to run the install_path exe"""
        folder = game.install_folder #Navigate to executable's directory
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
                print(folder)
        else:
            #Make batch file to run
            if 1:#not os.path.exists("cache/batches/"+game.gameid+".bat"):
                with open(cache_root+"/cache/batches/"+game.gameid+".bat", "w") as f:
                    f.write('cd "%s"\n'%folder)
                    filepath = path.split("\\")[-1]
                    exe,args = filepath.split(".exe")
                    exe = exe+".exe"
                    f.write('"%s" %s\n'%(exe,args))
            args = [game.gameid+".bat"]
            folder = os.path.abspath(cache_root+"/cache/batches/")
        return args,folder
    def run_game(self,game,source,cache_root):
        creationflags = 0
        shell = True
        if sys.platform=='darwin':
            shell = False
        args,folder = self.get_run_args(game,source,cache_root)
        print("run args:",args,folder)

        if args and folder:
            print(args)
            curdir = os.path.abspath(os.curdir)
            os.chdir(folder)
            print(os.path.abspath(os.curdir))
            self.running = subprocess.Popen(args, cwd=folder, stdout=sys.stdout, stderr=sys.stderr, creationflags=creationflags, shell=shell)
            print("subprocess open")
            os.chdir(curdir)

class SteamSource(Source):
    """Needs .api to be set to steamapi.Steam"""
    extra_args = []
    def args(self):
        return [("source_0_id","s")]+self.extra_args
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


class GogSource(ExeSource):
    """Needs .api to be set to gogapi.Gog"""
    extra_args = []
    def args(self):
        return [("source_0_id","s"),("install_path","s")]+self.extra_args
    def download_link(self,game,source):
        if "id" not in source:
            return ""
        return "gogdownloader://%s/installer_win_en"%source["id"]


class EmulatorSource(ExeSource):
    def args(self):
        return self.extra_args
    def get_run_args(self,game,source,cache_root):
        emu_info = game.games.local["emulators"][self.name]
        args = emu_info["args"]+[game.get_path()]
        exe = args[0]
        path = os.path.split(exe)[0]
        return args,path


class OfflineSource(Source):
    def args(self):
        return self.extra_args
    def is_installed(self,game,source):
        return True


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
        "class":"ExeSource",
        "extra_args":[("source_0_id","s")],
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
    }
}
all = {}
def register_sources(definitions):
    for sourcekey in definitions:
        source = definitions[sourcekey]
        cls = eval(source["class"])
        inst = cls(name=sourcekey)
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