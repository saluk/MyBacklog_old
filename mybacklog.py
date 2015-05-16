#!python3

#STDLIB
import json
import os
import time

import requests

#backloglib
from code.apis import giantbomb, steamapi, gogapi, humbleapi, thegamesdb
from code.interface import account
from code.resources import extract_icons
from code import games

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = "C:\\Python33\\Lib\\site-packages\\PyQt5\\plugins\\platforms"

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtWebKit
from PyQt5.QtWebKitWidgets import *
from PyQt5.QtNetwork import *

#steam_session = steamapi.login_for_chat()

def playrequest(game):
    try:
        r = requests.post("http://dawnsoft.org:9600/users/saluk/play",data={"game":game.name})
    except:
        pass
    #steamapi.set_username(steam_session,"saluk [Playing %s]"%game.name)
def stoprequest():
    try:
        r = requests.post("http://dawnsoft.org:9600/users/saluk/play",data={"game":""})
    except:
        pass
    #steamapi.set_username(steam_session,"saluk")
def uploadrequest(games):
    try:
        r = requests.post("http://dawnsoft.org:9600/users/saluk/upload_games",data={"games":games.save_data()})
    except:
        pass
def downloadrequest():
    r = requests.get("http://dawnsoft.org:9600/users/saluk/download_games")
    j = r.json()
    return j["games"]


def make_callback(f, *args):
    return lambda: f(*args)


class RunGameThread(QThread):
    process = None
    stopfunc = None
    def run(self):
        while self.process and self.process.returncode is None:
            self.process.communicate()


class Cookies(QNetworkCookieJar):
    def __init__(self):
        super(Cookies, self).__init__()
        self.cookies = {}
        if os.path.exists("cache/qtcookies"):
            with open("cache/qtcookies", "r") as f:
                self.cookies = json.loads(f.read())

    def cookiesForUrl(self, url):
        cookies = []
        for name in self.cookies:
            c = self.cookies[name]
            qnc = QNetworkCookie(c["name"], c["value"])
            qnc.setDomain(c["domain"])
            qnc.setPath(c["path"])
            cookies.append(qnc)
        return cookies

    def setCookiesFromUrl(self, cookielist, url):
        for c in cookielist:
            self.cookies[c.name().data().decode("utf8")] = {
                "name": c.name().data().decode("utf8"),
                "path": c.path(),
                "value": c.value().data().decode("utf8"),
                "domain": c.domain()}
        print(self.cookies)
        with open("cache/qtcookies", "w") as f:
            f.write(json.dumps(self.cookies))


class Browser(QWidget):
    def __init__(self, url, app):
        super(Browser, self).__init__()
        self.app = app
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        button = QPushButton("Do Import")
        layout.addWidget(button)
        button.clicked.connect(self.do_import)
        
        #self.cookiem = Cookies()
        self.webkit = QWebView()
        #self.webkit.page().networkAccessManager().setCookieJar(self.cookiem)
        layout.addWidget(self.webkit)
        
        self.webkit.load(QUrl(url))
        self.show()

    def do_import(self):
        html = self.webkit.page().mainFrame().toHtml()
        f = open("mygog_shelf.html","w",encoding="utf8")
        f.write(html)
        f.close()
        self.app.import_gog_html()
        self.deleteLater()


class ListGamesForPack(QWidget):
    def __init__(self, game, app):
        #  Currently only enable splitting of a game from a single source
        #  If a game has multiple sources, it must be split into each source before a bundle can be made
        #  The BUNDLE can only be from one source, however the individual titles can have multiple sources
        assert len(game.sources) == 1
        super(ListGamesForPack, self).__init__()
        self.game = game
        self.app = app
        
        self.oldid = game.gameid
        
        #Layout
        layout = QGridLayout()
        layout.addWidget(QLabel("Editing Package:"+game.gameid))
        
        current_games = self.app.games.games_for_pack(self.game)
        
        #Fields
        self.fields = {}
        for i in range(15):
            label = QLabel("Game %d"%i)
            layout.addWidget(label,i+1,0)
            
            gname = ""
            next_game = None
            if current_games:
                next_game = current_games.pop(0)
                gname = next_game.name
            
            edit = QLineEdit(gname)
            layout.addWidget(edit,i+1,1)
            self.fields[i] = {"w":edit,"g":next_game}
            
        #Save button
        button = QPushButton("Save + Close")
        layout.addWidget(button)
        button.clicked.connect(self.save_close)
        
        self.setLayout(layout)

    def save_close(self):
        self.app.games.multipack[self.game.sources[0]["id"]] = []
        pack_games = []
        for field in self.fields:
            field = self.fields[field]
            name = field["w"].text()
            if not name:
                continue
            game = None
            if field["g"]:
                game = field["g"].copy()
            if not game:
                game = self.game.copy()
            game.package_data = {"type":"content",
                                "parent":{"gameid":self.game.gameid,"name":self.game.name},
                                "source_info":game.create_package_data()}
            game.name = name
            game.gameid = game.generate_gameid()

            self.app.games.multipack[self.game.sources[0]["id"]].append(game.gameid)

            game = self.app.games.update_game(game.gameid,game)
            pack_games.append({"gameid":game.gameid,"name":game.name})
        self.game.package_data = {"type":"bundle",
                                  "contents":pack_games,
                                  "source_info":self.game.create_package_data()}
        self.app.games.save()
        self.app.update_gamelist_widget()
        self.deleteLater()

class EditGame(QWidget):
    def __init__(self, game, app, new=False):
        super(EditGame, self).__init__()
        self.game = game.copy()
        self.app = app
        self.games = app.games

        self.oldid = None
        if not new:
            self.oldid = game.gameid
        
        #Layout
        layout = QGridLayout()
        if new:
            layout.addWidget(QLabel("Adding new game"))
        else:
            layout.addWidget(QLabel("Editing:"+game.gameid))
        
        #Fields
        self.fields = {}
        for i,prop in enumerate(game.valid_args):
            prop,proptype = prop
            label = QLabel("%s:"%prop.capitalize())
            layout.addWidget(label,i+1,0)
            edit = QLineEdit(str(getattr(game,prop)))
            layout.addWidget(edit,i+1,1)
            self.fields[prop] = {"w":edit,"t":proptype}
            
            if prop=="install_path":
                button = QPushButton("Set Path")
                layout.addWidget(button,i+1,2)
                button.clicked.connect(make_callback(self.set_filepath,edit))

        name = "Make Package"
        if game.is_package:
            name = "Edit Package"
        button = QPushButton(name)
        layout.addWidget(button, i+2, 0)
        button.clicked.connect(make_callback(self.make_package))
            
        #Save button
        button = QPushButton("Save + Close")
        layout.addWidget(button)
        button.clicked.connect(self.save_close)

        #Delete button
        button = QPushButton("Delete")
        layout.addWidget(button)
        button.clicked.connect(self.delete)
        
        self.setLayout(layout)

    def set_filepath(self,w):
        filename = QFileDialog.getOpenFileName(self,"Open Executable",w.text(),"Executable (*.exe *.lnk *.cmd *.bat)")[0]
        w.setText(filename.replace("/","\\"))

    def make_package(self):
        self.lg = ListGamesForPack(self.game,self.app)
        self.lg.show()

    def save_close(self):
        game = self.game.copy()
        for field in self.fields:
            value = self.fields[field]["w"].text()
            t = self.fields[field]["t"]
            if t == "i":
                value = int(value)
            elif t == "f":
                value = float(value)
            setattr(game,field,value)
        newid = game.gameid
        if newid!=self.oldid:
            if self.oldid in self.games.games:
                self.games.games[newid] = self.games.games[self.oldid]
                del self.games.games[self.oldid]
        print("save", newid, self.oldid)
        print(game.priority,self.games.games[self.oldid].priority)
        print(game in self.games.games.values())
        self.games.update_game(self.game.gameid,game,force=True)
        self.games.save()
        self.app.update_game_row(self.game)
        self.deleteLater()
        self.parent().deleteLater()

    def delete(self):
        self.games.delete(self.game)
        self.games.save()
        self.deleteLater()
        self.parent().deleteLater()
        row = self.app.get_row_for_game(self.game)
        if row:
            self.app.games_list_widget.setRowHidden(row,True)

def icon_for_game(game,size,icon_cache):
    if game.icon_url:
        fpath = "cache/icons/"+game.icon_url.replace("http","").replace("https","").replace(":","").replace("/","")
        if not os.path.exists(fpath):
            r = requests.get(game.icon_url)
            f = open(fpath,"wb")
            f.write(r.content)
            f.close()
    elif game.get_exe():
        exe_path = game.get_exe()
        fpath = "cache/icons/"+exe_path.replace("http","").replace("https","").replace(":","").replace("/","").replace("\\","")
        if not os.path.exists(fpath):
            p = extract_icons.get_icon(exe_path)
            import shutil
            if p:
                shutil.copy(p,fpath)
    elif game.get_gba():
        gba_path = game.get_gba()
        fpath = "cache/icons/"+gba_path.replace("http","").replace(":","").replace("/","").replace("\\","")
        if not os.path.exists(fpath):
            p = extract_icons.get_gba(gba_path)
            import shutil
            if p:
                shutil.copy(p,fpath)
    else:
        fpath = "icons/blank.png"
    if os.path.exists(fpath) and not fpath+"_%d"%size in icon_cache:
        qp = QPixmap(fpath)
        if not qp.isNull():
            qp = qp.scaled(size,size)
        icon_cache[fpath] = qp
    if fpath in icon_cache:
        return QIcon(icon_cache[fpath])

class GameOptions(QWidget):
    def __init__(self, game, app):
        super(GameOptions, self).__init__()
        self.game = game.copy()
        self.app = app
        self.games = app.games

        #Layout
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop)

        label_section = QGridLayout()
        label_section.addWidget(QLabel(game.name),1,0)
        icon = icon_for_game(game,128,self.app.gicons)
        if icon:
            iconw = QLabel()
            iconw.setPixmap(icon.pixmap(128,128))
            label_section.addWidget(iconw,0,0)

        layout.addLayout(label_section,0,0)

        if game.is_installed():
            if not game.missing_steam_launch():
                run = QPushButton("Play Game")
            else:
                run = QPushButton("Play Game (no steam)")
            run.setBackgroundRole(QPalette.Highlight)
            run.clicked.connect(make_callback(self.app.run_game,game))
            layout.addWidget(run)

            run_no_timer = QPushButton("Play without time tracking")
            run_no_timer.clicked.connect(make_callback(self.app.run_game_notimer,game))
            layout.addWidget(run_no_timer)

        if game.needs_download():
            download = QPushButton("Download")
            download.clicked.connect(make_callback(self.app.download,game))
            layout.addWidget(download)

        edit = QPushButton("Edit")
        edit.clicked.connect(make_callback(self.app.edit_game,game))
        layout.addWidget(edit)

        if game.is_installed():
            edit = QPushButton("Uninstall")
            edit.clicked.connect(make_callback(self.app.uninstall_game,game))
            layout.addWidget(edit)

        self.setLayout(layout)

class MyBacklog(QMainWindow):
    def __init__(self):
        #super(MainWindow,self).__init__(None,Qt.WindowStaysOnTopHint)
        super(MyBacklog,self).__init__(None)
        self.setWindowTitle("MyBacklog")
        self.setWindowIcon(QIcon(QPixmap("icons/steam.png")))
        self.main_form = GamelistForm(self)

        menus = {}
        for folder in ["file","import","cleanup","sync","view"]:
            menus[folder] = self.menuBar().addMenu("&"+folder.capitalize())
            for x in dir(self.main_form):
                if x.startswith(folder+"_"):
                    name = " ".join([y.capitalize() for y in x.split("_")[1:]])
                    menus[folder].addAction(QAction("&"+name,self,triggered=getattr(self.main_form,x)))
        menus["view"] = self.menuBar().addMenu("&Add Game")
        for source in games.sources.all:
            menus["view"].addAction(QAction("&"+source,self,triggered=lambda : self.main_form.add_game(source)))

        menus["file"].addAction(QAction("&Exit",self,triggered=self.really_close))
        self.exit_requested = False

        self.setCentralWidget(self.main_form)

        self.trayicon = QSystemTrayIcon(QIcon(QPixmap("icons/steam.png")))
        self.trayicon.show()
        self.trayicon.activated.connect(self.click_tray_icon)
    def click_tray_icon(self):
        self.show()
    def really_close(self):
        self.exit_requested = True
        self.trayicon.hide()
        self.close()
    def closeEvent(self, event):
        if self.exit_requested:
            event.accept()
        else:
            event.ignore()
            self.hide()

DATA_GAMEID = 101
DATA_SORT = 12
DATA_EDIT = 145
class WILastPlayed(QTableWidgetItem):
    def __lt__(self, other):
        first = self.data(DATA_SORT)
        last = other.data(DATA_SORT)
        if not first:
            first = 0
        if not last:
            last = 0
        return first<last

a = WILastPlayed()
b = WILastPlayed()
a.setText("Wed")
a.setData(DATA_SORT,"a")
b.setText("Mon")
b.setData(DATA_SORT,"b")
assert a<b
assert b>a

class GamelistForm(QWidget):
    def __init__(self, parent=None):
        super(GamelistForm, self).__init__(parent)
        
        self.timer_started = 0
        
        self.games = games.Games()
        self.games.load()
        self.gamelist = []

        account = {"steam": {"api": "", "shortcut_folder": "", "id": ""}, "gog": {"user": "", "pass": ""}}
        if os.path.exists("data/account.json"):
            account = json.loads(open("data/account.json").read())
        self.set_accounts(account)

        self.columns = [("s",None,None),("icon",None,None),("name","widget_name","name"),
                        ("genre","genre","genre"),("playtime",None,None),("lastplay",None,None)]
        self.changed = []

        self.hide_packages = True
        self.show_hidden = False
        self.show_installed = False #If True, games not installed are hidden
 
        buttonLayout1 = QVBoxLayout()
        
        self.searchbar = QWidget()
        self.searchbarlayout = QHBoxLayout()
        self.searchbar.setLayout(self.searchbarlayout)
        buttonLayout1.addWidget(self.searchbar)
        
        self.search_name = QLineEdit()
        self.searchbarlayout.addWidget(self.search_name)
        self.search_name.textChanged.connect(self.dosearch)
        
        self.search_genre = QLineEdit()
        self.searchbarlayout.addWidget(self.search_genre)
        self.search_genre.textChanged.connect(self.dosearch)

        self.search_platform = QLineEdit()
        self.searchbarlayout.addWidget(self.search_platform)
        self.search_platform.textChanged.connect(self.dosearch)

        self.sort = "priority"
        self.games_list_widget = QTableWidget()

        self.game_scroller = QScrollArea()
        self.game_scroller.setWidgetResizable(True)
        self.game_scroller.setWidget(self.games_list_widget)
        buttonLayout1.addWidget(self.game_scroller)
 
        self.buttonLayout1 = buttonLayout1
        mainLayout = QGridLayout()
        # mainLayout.addWidget(nameLabel, 0, 0)
        mainLayout.addLayout(buttonLayout1, 0, 1)

        self.setLayout(mainLayout)
        self.setWindowTitle("My Backlog")

        self.icons = {}
        for icon in os.listdir("icons"):
            self.icons[icon.split(".")[0]] = QPixmap("icons/%s"%icon)
        for source in games.sources.all:
            if source not in self.icons:
                self.icons[source] = QPixmap("icons/blank.png")
        self.gicons = {}

        self.timer = QTimer(self)
        self.timer.setInterval(300000)
        #self.timer.setInterval(5000)
        self.timer.timeout.connect(self.notify)
        
        self.update_gamelist_widget()
        self.setMinimumSize(740,600)
        self.setMaximumWidth(1080)
        self.adjustSize()

        self.running = None #Game currently being played

        self.game_options_dock = QDockWidget("Game Options",self)
        self.game_options_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.game_options_dock.setMaximumWidth(300)
        self.game_options_dock.setMinimumWidth(300)
        self.game_options_dock.setMaximumHeight(400)
        self.window().addDockWidget(Qt.LeftDockWidgetArea,self.game_options_dock)

    def set_accounts(self,account):
        self.gog = gogapi.Gog(account["gog"]["user"],account["gog"]["pass"])
        self.steam = steamapi.Steam(account["steam"]["api"],account["steam"]["id"],account["steam"]["shortcut_folder"])
        games.sources.SteamSource.api = self.steam
        games.sources.GogSource.api = self.gog

    def disable_edit_notify(self):
        try:
            self.games_list_widget.cellChanged.disconnect(self.cell_changed)
        except:
            pass

    def enable_edit_notify(self):
        self.games_list_widget.cellChanged.connect(self.cell_changed)

    def file_save(self):
        self.disable_edit_notify()
        self.games.save()
        for row in range(self.games_list_widget.rowCount()):
            gameid = self.games_list_widget.item(row,0).data(DATA_GAMEID)
            if gameid in self.changed:
                self.update_game_row(self.games.games[gameid],row)
        self.changed = []
        self.enable_edit_notify()

    def file_options(self):
        self.edit_account = account.AccountForm(self)
        self.edit_account.show()

    def notify(self):
        if self.running:
            self.parent().trayicon.showMessage("Still Playing","Are you still playing %s ?"%self.running.name)

    def get_row_for_game(self,game):
        for row in range(self.games_list_widget.rowCount()):
            gameid = self.games_list_widget.item(row,0).data(DATA_GAMEID)
            if gameid == game.gameid:
                return row
        
    def update_game_row(self,game,row=None):
        if row is None:
            row = self.get_row_for_game(game)
        if row is None:
            return

        def abreve(t,l):
            if len(t)<l:
                return t
            words = t.split(" ")
            for i in range(len(words)):
                t = " ".join(words)
                if len(t)<l:
                    return t
                words[-i] = words[-i].replace("a","").replace("e","").replace("i","").replace("o","").replace("u","")
            return " ".join(words)[:l]

        game.widget_name = game.name
        if game.is_in_package:
            package = self.games.get_package_for_game(game)
            if package:
                game.widget_name = "["+abreve(package.name,25)+"] "+game.name
        game.widget_name = abreve(game.widget_name,100)
        if game.finished:
            bg = QColor(100,200,150)
        elif game.is_package:
            bg = QColor(100,100,200)
        else:
            b = max(100,215-game.priority*40)
            bg = QColor(b,b,b)
            #bg = QColor(self.palette().Background)

        source = QTableWidgetItem("")
        source.setBackground(bg)
        source.setData(DATA_GAMEID,game.gameid)
        for s in game.sources:
            if s["source"] in self.icons:
                source.setIcon(QIcon(self.icons[s["source"]]))
        self.games_list_widget.setItem(row,0,source)
            
        label = QTableWidgetItem("")
        label.setBackground(bg)
        icon = icon_for_game(game,48,self.gicons)
        if icon:
            label.setIcon(icon)
        self.games_list_widget.setItem(row,1,label)
            
        name = QTableWidgetItem("GAME NAME")
        name.setBackground(bg)
        name.setText(game.widget_name)
        self.games_list_widget.setItem(row,2,name)

        genre = QTableWidgetItem("GAME GENRE")
        genre.setBackground(bg)
        genre.setText(game.genre)
        self.games_list_widget.setItem(row,3,genre)

        hours = QTableWidgetItem("GAME HOURS")
        hours.setBackground(bg)
        hours.setText("%.2d:%.2d"%game.hours_minutes)
        self.games_list_widget.setItem(row,4,hours)

        lastplayed = WILastPlayed("GAME LAST PLAYED")
        lastplayed.setBackground(bg)
        lastplayed.setText(game.last_played_nice)
        lastplayed.setData(DATA_SORT,games.stot(game.lastplayed))
        self.games_list_widget.setItem(row,5,lastplayed)

    def update_gamelist_widget(self):
        try:
            self.games_list_widget.cellChanged.disconnect(self.cell_changed)
        except TypeError:
            pass
        self.gamelist = []
        for g in self.games.list(self.sort):
            self.gamelist.append({"game":g,"widget":None})
        self.games_list_widget.clear()
        self.games_list_widget.setIconSize(QSize(48,48))
        self.games_list_widget.horizontalHeader().setVisible(True)
        self.games_list_widget.verticalHeader().setVisible(False)
        self.games_list_widget.setRowCount(len(self.gamelist)+1)
        self.games_list_widget.setColumnCount(6)
        self.games_list_widget.itemSelectionChanged.connect(self.selected_row)
        for i,g in enumerate(self.gamelist):
            self.update_game_row(g["game"],i)
        self.update_game_row(games.Game(name="Total Time Played"),i+1)
        self.dosearch()

        self.game_scroller.verticalScrollBar().setValue(0)
        self.games_list_widget.setHorizontalHeaderLabels([x[0] for x in self.columns])
        self.games_list_widget.resizeColumnsToContents()
        self.games_list_widget.setColumnWidth(0,48)
        self.games_list_widget.setColumnWidth(1,48)
        self.games_list_widget.setColumnWidth(2,350)
        self.games_list_widget.setColumnWidth(3,50)
        self.games_list_widget.setColumnWidth(4,50)
        self.games_list_widget.setColumnWidth(5,150)

        self.games_list_widget.setSortingEnabled(True)

        self.games_list_widget.cellChanged.connect(self.cell_changed)
        self.games_list_widget.cellDoubleClicked.connect(self.cell_activated)

        self.dosearch()
        self.update()

    def import_steam(self):
        try:
            games = self.steam.import_steam()
        except steamapi.ApiError:
            self.edit_account = account.AccountForm(self,"Steam API error - check settings",["steam_id","steam_api"])
            self.edit_account.show()
            return
        self.games.add_games(games)
        self.update_gamelist_widget()
        self.games.save()
        
    def cleanup_add_steam_shortcuts(self):
        self.steam.create_nonsteam_shortcuts(self.games.games)

    def import_humble(self):
        games = humbleapi.get_humble_gamelist()
        self.games.add_games(games)
        self.update_gamelist_widget()
        crash
        self.games.save()

    def import_gog(self):
        #self.browser = Browser("https://secure.gog.com/account/games",self)
        try:
            self.gog.better_get_shelf()
        except gogapi.BadAccount:
            self.edit_account = account.AccountForm(self,"Improper GOG account, please update gog username and password",["gog_user","gog_password"])
            self.edit_account.show()
            return
        self.import_gog_html()

    def import_gog_html(self):
        games = self.gog.import_gog(self.games.multipack)
        self.games.add_games(games)
        self.update_gamelist_widget()
        self.games.save()

    def sync_uploadgames(self):
        uploadrequest(self.games)

    def sync_downloadgames(self):
        games = downloadrequest()
        self.games = games.Games()
        self.games.translate_json(games)
        self.games.save()
        self.update_gamelist_widget()

    def cleanup_gamesdb(self):
        for g in self.games.games.values():
            gdbg = thegamesdb.find_game(g.name)
            if gdbg:
                data = thegamesdb.get_game_info(gdbg["id"])
                if data and "Game" in data:
                    print (data["Game"])
                    genre = data["Game"].get("Genres",{}).get("genre","")
                    coop = data["Game"].get("Co-op","No").lower().strip()=="yes"
                    if type(genre) not in [str,bytes]:
                        genre = [x for x in genre if type(x) in [str,bytes]][0]
                    print(genre,coop)
                    g.genre = genre.lower()
                    if coop:
                        g.genre = g.genre+"; co-op"
                    print(g.genre)
        self.games.save()

    def cleanup_giantbomb(self):
        for g in self.games.games.values():
            gdbg = giantbomb.find_game(g.name)
            if gdbg:
                data = thegamesdb.get_game_info(gdbg["id"])
                if data and "Game" in data:
                    print (data["Game"])
                    genre = data["Game"]["Genres"].get("genre","")
                    coop = data["Game"]["Co-op"]
                    if type(genre) not in [str,bytes]:
                        genre = [x for x in genre if type(x) in [str,bytes]][0]
                    print(genre,coop)
                    g.genre = genre.lower()
                    if coop:
                        g.genre = g.genre+"; co-op"
                    print(g.genre)
        self.games.save()

    def view_sort_by_added(self):
        self.sort = "added"
        self.update_gamelist_widget()

    def view_sort_by_priority(self):
        self.sort = "priority"
        self.update_gamelist_widget()

    def view_sort_by_changed(self):
        self.sort = "changed"
        self.update_gamelist_widget()

    def view_show_packages(self):
        self.hide_packages = not self.hide_packages
        self.update_gamelist_widget()

    def view_show_hidden(self):
        self.show_hidden = not self.show_hidden
        self.update_gamelist_widget()

    def view_show_installed(self):
        self.show_installed = not self.show_installed
        self.update_gamelist_widget()

    def run_game_notimer(self,game):
        return self.run_game(game,track_time=False)

    def run_game(self,game,track_time=True):
        if getattr(self,"stop_playing_button",None):
            return
        if track_time:
            self.timer_started = time.time()
        print ("run game",game.name,game.gameid)
        self.timer.start()
        
        if track_time:
            self.stop_playing_button = QPushButton("Stop Playing "+game.name)
            self.game_options_dock.widget().layout().addWidget(self.stop_playing_button)
            self.stop_playing_button.clicked.connect(make_callback(self.stop_playing,game))

        self.running = game
        game.run_game()
        self.games.play(game)
        playrequest(game)

    def stop_playing(self,game):
        self.running = None
        self.games.stop(game)
        self.timer.stop()
        #stoprequest()
        #self.buttonLayout1.removeWidget(self.stop_playing_button)
        if getattr(self,"stop_playing_button",None):
            self.stop_playing_button.deleteLater()
        self.stop_playing_button = None
        elapsed_time = time.time()-self.timer_started
        QMessageBox.information(self, "Success!",
                                    "You played for %d seconds" % elapsed_time)
        game.played()
        game.playtime += elapsed_time
        game.priority = -1
        self.games.save()
        self.update_gamelist_widget()

    def show_edit_widget(self,*args,**kwargs):
        self.egw = EditGame(*args,**kwargs)
        dock = QDockWidget("Edit",self)
        dock.setWidget(self.egw)
        self.window().addDockWidget(Qt.LeftDockWidgetArea,dock)
        return self.egw

    def selected_row(self):
        if self.games_list_widget.selectedItems():
            item = self.games_list_widget.selectedItems()[0]
            row = item.row()
            gameid = self.games_list_widget.item(row,0).data(DATA_GAMEID)
            if gameid not in self.games.games:
                return
            game = self.games.games[gameid]
            self.update_game_options(game)

            if getattr(self,"stop_playing_button",None):
                self.game_options_dock.widget().layout().addWidget(self.stop_playing_button)
                self.stop_playing_button.clicked.connect(make_callback(self.stop_playing,game))

    def cell_changed(self,row,col):
        gameid = self.games_list_widget.item(row,0).data(DATA_GAMEID)
        if gameid not in self.games.games:
            return
        game = self.games.games[gameid]
        self.games_list_widget.item(row,col).setBackground(QColor(200,10,10))
        if self.columns[col][2]:
            print("setting",gameid,self.columns[col][2],"to",self.games_list_widget.item(row,col).text())
            setattr(game,self.columns[col][2],self.games_list_widget.item(row,col).text())
        self.selected_row()
        self.changed.append(gameid)

    def cell_activated(self,row,col):
        if self.columns[col][2]:
            gameid = self.games_list_widget.item(row,0).data(DATA_GAMEID)
            game = self.games.games[gameid]
            self.games_list_widget.item(row,col).setText(getattr(game,self.columns[col][2]))

    def update_game_options(self,game):
        self.game_options = GameOptions(game,self)
        self.game_options_dock.setWidget(self.game_options)

        return self.game_options

    def edit_game(self,game):
        self.show_edit_widget(game,self)

    def uninstall_game(self,game):
        game.uninstall()

    def download(self,game):
        game.download_method()

    def add_game(self,source):
        game = games.Game(source=source)
        self.gamelist.append({"game":game,"widget":None})
        self.show_edit_widget(game,None,self,new=True)

    def dosearch(self,text=None):
        played = 0

        sn = self.search_name.text().lower()
        sg = self.search_genre.text().lower()
        sp = self.search_platform.text().lower()
        if sp == "emu":
            sp = "gba or snes or n64 or nds"
        for row in range(self.games_list_widget.rowCount()-1):
            gameid = self.games_list_widget.item(row,0).data(DATA_GAMEID)
            game = self.games.games[gameid]
            self.games_list_widget.setRowHidden(row,False)
            if game.is_package and self.hide_packages:
                self.games_list_widget.setRowHidden(row,True)
                continue
            if self.show_installed:
                if not game.is_installed():
                    self.games_list_widget.setRowHidden(row,True)
                    continue
            if game.hidden and not self.show_hidden:
                self.games_list_widget.setRowHidden(row,True)
                continue
            def match(search,field):
                searches = search.split(" or ")
                for s in searches:
                    if s in field:
                        return True
            if (sn and not match(sn,game.name.lower())) or \
            (sg and not match(sg,game.genre.lower())) or \
            (sp and not match(sp," ".join([s["source"] for s in game.sources]))):
                self.games_list_widget.setRowHidden(row,True)
                continue

            played += game.playtime

        #Total playtime
        total_hours = QTableWidgetItem("GAME HOURS")
        min = played/60.0
        hour = int(min/60.0)
        min = min-hour*60.0
        day = int(hour/24.0)
        if day:
            hour = hour-day*24.0
            total_hours.setText("%.2dd%.2d:%.2d"%(day,hour,min))
        else:
            total_hours.setText("%.2d:%.2d"%(hour,min))
        self.games_list_widget.setItem(row+1,4,total_hours)
 
if __name__ == '__main__':
    import sys
 
    app = QApplication(sys.argv)

    # app.setStyle('Fusion')
    # palette = QPalette()
    # palette.setColor(QPalette.Window, QColor(53,53,53))
    # palette.setColor(QPalette.WindowText, Qt.white)
    # palette.setColor(QPalette.Base, QColor(15,15,15))
    # palette.setColor(QPalette.AlternateBase, QColor(53,53,53))
    # palette.setColor(QPalette.ToolTipBase, Qt.white)
    # palette.setColor(QPalette.ToolTipText, Qt.white)
    # palette.setColor(QPalette.Text, Qt.white)
    # palette.setColor(QPalette.Button, QColor(53,53,53))
    # palette.setColor(QPalette.ButtonText, Qt.white)
    # palette.setColor(QPalette.BrightText, Qt.red)
    #
    # palette.setColor(QPalette.Highlight, QColor(142,45,197).lighter())
    # palette.setColor(QPalette.HighlightedText, Qt.black)
    # app.setPalette(palette)

    window = MyBacklog()
    window.show()
 
    sys.exit(app.exec_())
