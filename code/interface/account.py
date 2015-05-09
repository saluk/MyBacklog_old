import json

from code.apis import giantbomb, steamapi, gogapi, humbleapi, thegamesdb
from code.resources import winicons
from code import data

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtWebKit
from PyQt5.QtWebKitWidgets import *
from PyQt5.QtNetwork import *

def make_callback(f, *args):
    return lambda: f(*args)

class AccountForm(QWidget):
    def __init__(self, app, message="", highlight_fields=[]):
        super(AccountForm, self).__init__()
        self.app = app

        #Layout
        layout = QGridLayout()
        if not message:
            layout.addWidget(QLabel("Edit Accounts"))
        else:
            layout.addWidget(QLabel(message))

        def highlight(w):
            w.setFont(QFont("Times",10,QFont.Bold,True))
            pass

        #Fields
        self.fields = {"steam":{},"gog":{}}
        w = QLabel("Steam ID")
        s = "In steam, if you view your profile, the url will look like 'http://steamcommunity.com/id/[your_account_id]/'. Enter the value for [your_account_id] here."
        w.setToolTip(s)
        if "steam_id" in highlight_fields:
            highlight(w)
        layout.addWidget(w,1,0)
        w = QLineEdit(self.app.steam.user_id)
        w.setToolTip(s)
        layout.addWidget(w,1,1)
        self.fields["steam"]["id"] = w

        s = "You can register for a web api key here: http://steamcommunity.com/dev/apikey"
        w = QLabel("Steam API Key")
        w.setToolTip(s)
        if "steam_api" in highlight_fields:
            highlight(w)
        layout.addWidget(w,2,0)
        w = QLineEdit(self.app.steam.api_key)
        w.setToolTip(s)
        layout.addWidget(w,2,1)
        self.fields["steam"]["api"] = w

        w = QLabel("Steam shortcuts")
        if "steam_shortcut" in highlight_fields:
            highlight(w)
        layout.addWidget(w,3,0)
        w = QLineEdit(self.app.steam.shortcut_folder)
        layout.addWidget(w,3,1)
        button = QPushButton("Set Path")
        layout.addWidget(button,3,2)
        button.clicked.connect(make_callback(self.set_filepath,w))
        self.fields["steam"]["shortcut_folder"] = w

        w = QLabel("GOG Username")
        if "gog_user" in highlight_fields:
            highlight(w)
        layout.addWidget(w,5,0)
        w = QLineEdit(self.app.gog.username)
        layout.addWidget(w,5,1)
        self.fields["gog"]["user"] = w

        w = QLabel("GOG Password")
        if "gog_password" in highlight_fields:
            highlight(w)
        layout.addWidget(w,6,0)
        w = QLineEdit(self.app.gog.password)
        layout.addWidget(w,6,1)
        self.fields["gog"]["pass"] = w

        #Save button
        button = QPushButton("Save")
        layout.addWidget(button,7,0)
        button.clicked.connect(self.save_close)

        print(self.fields)
        self.setLayout(layout)

    def set_filepath(self,w):
        filename = QFileDialog.getOpenFileName(self,"Open Executable",w.text(),"Executable (*.vdf)")[0]
        w.setText(filename.replace("/","\\"))

    def save_close(self):
        save = {}
        for key_type in self.fields:
            save[key_type] = {}
            for key in self.fields[key_type]:
                save[key_type][key] = self.fields[key_type][key].text()
        f = open("data/account.json","w")
        f.write(json.dumps(save))
        f.close()
        self.app.set_accounts(save)
        self.delete()

    def delete(self):
        self.deleteLater()