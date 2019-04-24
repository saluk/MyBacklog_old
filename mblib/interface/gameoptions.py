import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from mblib.resources import icons
from mblib import games

def make_callback(f, *args):
    return lambda: f(*args)
    
def ts_to_qtdt(s):
    s = time.mktime(games.stot(s))
    qtdt = QDateTime()
    qtdt.setTime_t(s)
    return qtdt
    
def qtdt_to_ts(qtdt):
    s = qtdt.toTime_t()
    return games.ttos(time.localtime(s))

class ListGamesForPack(QWidget):
    def __init__(self, game, app, edit_widget):
        #  Currently only enable splitting of a game from a single source
        #  If a game has multiple sources, it must be split into each source before a bundle can be made
        #  The BUNDLE can only be from one source, however the individual titles can have multiple sources
        assert len(game.sources) == 1
        super(ListGamesForPack, self).__init__()
        self.game = game
        self.app = app
        self.edit_widget = edit_widget

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
        self.app.games.force_update_game(self.game.gameid,self.game)
        self.app.save()
        self.app.update_gamelist_widget()
        self.deleteLater()
        self.edit_widget.deleteLater()

class EditGame(QWidget):
    def __init__(self, game, app, new=False, parented=False):
        super(EditGame, self).__init__()
        self.app = app
        self.games = app.games
        self.parented = parented
        self.new = new
        self.init(game)
    def init(self,game):
        game.update_dynamic_fields()
        
        self.game = game.copy()
        self.oldid = None
        if not self.new:
            self.oldid = game.gameid

        #Layout
        baselayout = QGridLayout()
        if self.new:
            baselayout.addWidget(QLabel("Adding new game"))
        else:
            baselayout.addWidget(QLabel("Editing:"+game.gameid))

        layout = QGridLayout()
        scrollwidget = QWidget()
        layout.setContentsMargins(1,1,1,1)
        scrollwidget.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidget(scrollwidget)

        #layout = widget.layout()
        #baselayout.addLayout(other_layout,1,0)
        baselayout.addWidget(scroll)

        #baselayout.addLayout(layout,1,0)


        #Fields
        self.fields = {}
        self.source_fields = {}
        for i,prop in enumerate(game.valid_args):
            self.addwidget(i,game,prop,layout)
        for i2,source in enumerate(game.sources):
            i+=1
            layout.addWidget(QLabel(source["source"]),i,0)
            source_layout = QGridLayout()
            print(source["source"],games.get_source(source["source"]),games.get_source(source["source"]).source_args)
            for i3,prop in enumerate(games.get_source(source["source"]).source_args):
                self.addwidget(i3,source,prop,source_layout,mode="source",source_index=i2)
            layout.addLayout(source_layout,i+1,0,1,3)
            

        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scrollwidget.adjustSize()

        buttons_layout = QGridLayout()
        name = "Make Package"
        if game.is_package:
            name = "Edit Package"
        button = QPushButton(name)
        buttons_layout.addWidget(button, 0, 0)
        button.clicked.connect(make_callback(self.make_package))

        #Save button
        save_method = "Save + Close"
        if self.parented:
            save_method = "Save"
        button = QPushButton(save_method)
        buttons_layout.addWidget(button,0,1)
        button.clicked.connect(self.save_close)

        #Delete button
        button = QPushButton("Delete")
        buttons_layout.addWidget(button,0,2)
        button.clicked.connect(self.delete)

        baselayout.addLayout(buttons_layout,2,0)

        self.setLayout(baselayout)
        
    def addwidget(self,i,resource,prop,layout,mode="game",source_index=None):
        prop,proptype = prop
        
        def get_value(p):
            if mode=="game":
                return getattr(resource,prop)
            elif mode=="source":
                return resource[prop]
        
        label_name = "%s:"%prop.capitalize()
        print("EDIT PROPERTY:",prop,i)

        label = QLabel(label_name)
        layout.addWidget(label,i,0)

        if prop=="notes":
            edit = QTextEdit(str(get_value(prop)))
            edit.setMinimumSize(10,20)
            edit.setMinimumHeight(10)
            edit.setMaximumHeight(100)
            button = QPushButton("...")
            button.setFixedWidth(32)
            layout.addWidget(button,i,2)
            button.clicked.connect(make_callback(self.expand_notes,resource,prop,edit,i,layout))
            self.expand_notes_button = button
        elif proptype == "d":
            edit = QDateTimeEdit()
            edit.setCalendarPopup(True)
            edit.setDateTime(ts_to_qtdt(get_value(prop)))
        elif proptype == "f":
            edit = QLineEdit("%.2f"%get_value(prop))
            validator = QDoubleValidator(0.0,3153600000.0,2)
            edit.setValidator(validator)
        elif proptype == "p":
            priorities = games.PRIORITIES
            pkeys = sorted(priorities.keys())
            edit = QComboBox()
            for pi,k in enumerate(pkeys):
                edit.addItem(priorities[k])
                if k == get_value(prop):
                    edit.setCurrentIndex(pi)
        else:
            edit = QLineEdit(str(get_value(prop)))
        if prop == "website":
            button = QPushButton("->")
            button.setFixedWidth(32)
            layout.addWidget(button,i,2)
            button.clicked.connect(make_callback(self.goto_website,edit))
        edit.setMaximumWidth(108)
        layout.addWidget(edit,i,1)
        
        if mode=="game":
            self.fields[prop] = {"w":edit,"t":proptype}
        elif mode=="source":
            self.source_fields[prop] = {"w":edit,"t":proptype,"source":resource,"source_index":source_index}

        if prop=="install_path":
            button = QPushButton("...")
            button.setFixedWidth(32)
            layout.addWidget(button,i,2)
            button.clicked.connect(make_callback(self.set_filepath,edit))
            
            button = QPushButton("-->")
            button.setFixedWidth(32)
            layout.addWidget(button,i,3)
            button.clicked.connect(make_callback(self.open_filepath,edit))

    def expand_notes(self,game,prop,edit,i,layout):
        if edit.maximumHeight()<100:
            edit.setMinimumSize(10,20)
            edit.setMinimumHeight(100)
            edit.setMaximumHeight(100)
        else:
            edit.setMinimumHeight(10)
            edit.setMaximumHeight(10)
        edit.updateGeometry()
        self.layout().update()
        
    def goto_website(self,widget):
        QDesktopServices.openUrl(QUrl(widget.text(),QUrl.TolerantMode))

    def set_filepath(self,w):
        filename = QFileDialog.getOpenFileName(self,"Open Executable",w.text(),"Executable/Rom (*.app *.exe *.lnk *.cmd *.bat %s)"%self.game.rom_extension)[0]
        w.setText(filename.replace("/","\\"))
        
    def open_filepath(self,w):
        import os
        s = w.text()
        if not os.path.isdir(s):
            s = os.path.split(s)[0]
        filename = QDesktopServices.openUrl(QUrl("file:///"+s,QUrl.TolerantMode))

    def make_package(self):
        self.lg = ListGamesForPack(self.game,self.app,self)
        self.lg.show()
    def save_close(self):
        game = self.game
        for field in self.fields:
            self.save_prop(field,self.fields[field])
        new_sources = []
        for field in self.source_fields:
            self.save_prop(field,self.source_fields[field])
        game.generate_gameid()
        newid = game.gameid
        print("save", newid, self.oldid)
        if self.oldid and self.oldid in self.games.games:
            print("Updated old:",game.priority,self.games.games[self.oldid].priority)
        print(game in self.games.games.values())
        self.app.operation("force_update",self.app,game,self.oldid)

        if not self.parented:
            self.deleteLater()
            self.parent().deleteLater()
    def save_prop(self,field,props):
        t = props["t"]
        w = props["w"]
        source = props.get("source",None)
        print(source)
        if t == "i":
            value = int(w.text())
        elif t == "f":
            value = float(w.text())
        elif t == "d":
            value = qtdt_to_ts(w.dateTime())
            if "1969" in value:
                value = ""
        elif t == "p":
            priorities = games.PRIORITIES
            pkeys = sorted(priorities.keys())
            i = w.currentIndex()
            value = pkeys[i]
        else:
            value = getattr(w,"text",(getattr(w,"toPlainText",str)))()
        if source:
            i = self.game.sources.index(source)
            source[field] = value
            self.game.sources[i] = source
        else:
            setattr(self.game,field,value)
    def delete(self):
        self.games.delete(self.game)
        row = self.app.get_row_for_game(self.game)
        if row:
            self.app.games_list_widget.removeRow(row)
        self.app.dosearch()
        self.app.save()

        if not self.parented:
            self.deleteLater()
            self.parent().deleteLater()
        else:
            self.parented.deleteLater()

class GameOptions(QWidget):
    def __init__(self, game, app, new=False):
        super(GameOptions, self).__init__()
        self.game = game.copy()
        self.app = app
        self.games = app.games
        self.new = new

        #Layout
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop)

        label_section = QGridLayout()
        icon = icons.icon_for_game(game,180,self.app.gicons,app.config["root"],"logo")
        if icon:
            iconw = QLabel()
            #iconw.setScaledContents(True)
            iconw.setPixmap(icon.pixmap(180,180))
            label_section.addWidget(iconw,0,0)

        layout.addLayout(label_section,0,0)
        layout.addWidget(QLabel(game.name))

        buttons = QGridLayout()
        buttons.setAlignment(Qt.AlignTop)

        play_options = []
        if game.is_installed():
            play_options.append(("Play",make_callback(self.app.run_game,game)))
            play_options.append(("Launch",make_callback(self.app.run_game_notimer,game)))
        play_options.append(("Track Time",make_callback(self.app.run_game_track_only,game)))

        run = QToolButton()
        run.setText(play_options[0][0])
        run.clicked.connect(play_options[0][1])
        run.setToolButtonStyle(Qt.ToolButtonTextOnly)
        run.setPopupMode(QToolButton.MenuButtonPopup)
        run.setFixedHeight(40)
        run.setMinimumWidth(100)
        run.setBackgroundRole(QPalette.Highlight)
        if play_options[1:]:
            m = QMenu()
            run.setMenu(m)
        for opt in play_options[1:]:
            action = m.addAction(opt[0])
            action.triggered.connect(opt[1])
        buttons.addWidget(run)


        if game.needs_download():
            download = QPushButton("Download")
            download.clicked.connect(make_callback(self.app.download,game))
            buttons.addWidget(download)

        if game.is_installed():
            w = QPushButton("Uninstall")
            w.clicked.connect(make_callback(game.uninstall))
            buttons.addWidget(w)
            
        if game.finished:
            w = QPushButton("Unfinish")
            w.clicked.connect(make_callback(self.app.operation,game,"unfinish"))
            buttons.addWidget(w)
        else:
            w = QPushButton("Finish")
            w.setStyleSheet("background-color:rgb(100,200,150);")
            w.clicked.connect(make_callback(self.app.operation,game,"finish"))
            buttons.addWidget(w)
            
        if game.hidden:
            w = QPushButton("Unhide")
            w.clicked.connect(make_callback(self.app.operation,"set",game,"hidden",0))
            buttons.addWidget(w)
        else:
            w = QPushButton("Hide")
            w.clicked.connect(make_callback(self.app.operation,"set",game,"hidden",1))
            buttons.addWidget(w)
        w = QPushButton("Gamesdb")
        w.clicked.connect(make_callback(self.app.gamesdb,game))
        buttons.addWidget(w)
        label_section.addLayout(buttons,0,1)

        self.edit_widget = EditGame(game,app,parented=self,new=self.new)
        #scroll = QScrollArea()
        #scroll.setWidget(self.edit_widget)
        layout.addWidget(self.edit_widget)

        self.setLayout(layout)