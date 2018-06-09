import json

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from mblib.apis import steamapi

def make_callback(f, *args):
    return lambda: f(*args)

class AccountForm(QWidget):
    def __init__(self, app, message="", highlight_fields=[], dock=False):
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
        i = 1
        self.fields = {"steam":{},"gog":{},"humble":{}}
        w = QLabel("Steam ID")
        s = "In steam, if you view your profile, the url will look like 'http://steamcommunity.com/id/[your_account_id]/'. Enter the value for [your_account_id] here."
        w.setToolTip(s)
        if "steam_id" in highlight_fields:
            highlight(w)
        layout.addWidget(w,i,0)
        print("APP=",app)
        w = QLineEdit(self.app.steam.user_id)
        w.setToolTip(s)
        layout.addWidget(w,i,1)
        self.fields["steam"]["id"] = w
        
        help = QPushButton("?")
        def h(parent,s=s):
            d = QDialog(self)
            d.setLayout(QGridLayout())
            text = QLabel(s)
            text.setTextInteractionFlags(Qt.TextSelectableByMouse|Qt.TextSelectableByKeyboard)
            d.layout().addWidget(text)
            d.show()
        help.clicked.connect(h)
        layout.addWidget(help,i,2)

        i+=1
        s = "You can register for a web api key here: http://steamcommunity.com/dev/apikey"
        w = QLabel("Steam API Key")
        w.setToolTip(s)
        if "steam_api" in highlight_fields:
            highlight(w)
        layout.addWidget(w,i,0)
        w = QLineEdit(self.app.steam.api_key)
        w.setToolTip(s)
        layout.addWidget(w,i,1)
        w.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.fields["steam"]["api"] = w
        
        help = QPushButton("?")
        def h(parent,s=s):
            d = QDialog(self)
            d.setLayout(QGridLayout())
            text = QLabel(s)
            text.setTextInteractionFlags(Qt.TextSelectableByMouse|Qt.TextSelectableByKeyboard)
            d.layout().addWidget(text)
            d.show()
        help.clicked.connect(h)
        layout.addWidget(help,i,2)

        i+=1
        w = QPushButton("Search For Steam Files")
        w.clicked.connect(make_callback(self.assign_steam,w))
        layout.addWidget(w,i,2)

        i+=1
        w = QLabel("Steam user file")
        if "steam_userfile" in highlight_fields:
            highlight(w)
        layout.addWidget(w,i,0)
        w = QLineEdit(self.app.steam.userfile)
        layout.addWidget(w,i,1)
        button = QPushButton("Set Path")
        layout.addWidget(button,i,2)
        button.clicked.connect(make_callback(self.set_filepath,w))
        self.fields["steam"]["userfile"] = w

        i+=1
        w = QLabel("Steam shortcuts")
        if "steam_shortcut" in highlight_fields:
            highlight(w)
        layout.addWidget(w,i,0)
        w = QLineEdit(self.app.steam.shortcut_folder)
        layout.addWidget(w,i,1)
        button = QPushButton("Set Path")
        layout.addWidget(button,i,2)
        button.clicked.connect(make_callback(self.set_filepath,w))
        self.fields["steam"]["shortcut_folder"] = w

        i+=1
        w = QLabel("GOG Username")
        if "gog_user" in highlight_fields:
            highlight(w)
        layout.addWidget(w,i,0)
        w = QLineEdit(self.app.gog.username)
        layout.addWidget(w,i,1)
        self.fields["gog"]["user"] = w

        i+=1
        w = QLabel("GOG Password")
        if "gog_password" in highlight_fields:
            highlight(w)
        layout.addWidget(w,i,0)
        w = QLineEdit(self.app.gog.password)
        layout.addWidget(w,i,1)
        w.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.fields["gog"]["pass"] = w

        i+=1
        w = QLabel("Humble Username")
        if "humble_username" in highlight_fields:
            highlight(w)
        layout.addWidget(w,i,0)
        w = QLineEdit(self.app.humble.username)
        layout.addWidget(w,i,1)
        self.fields["humble"]["username"] = w

        i+=1
        w = QLabel("Humble Password")
        if "humble_password" in highlight_fields:
            highlight(w)
        layout.addWidget(w,i,0)
        w = QLineEdit(self.app.humble.password)
        layout.addWidget(w,i,1)
        w.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.fields["humble"]["password"] = w

        i+=1
        #Save button
        if not dock:
            button = QPushButton("Save")
            layout.addWidget(button,i,0)
            button.clicked.connect(self.save_close)

        print(self.fields)
        self.setLayout(layout)

    def assign_steam(self,w):
        users = steamapi.find_steam_files()
        print(users)
        if not users:
            d = QDialog(self)
            d.setLayout(QGridLayout())
            text = QLabel("No steam user settings found")
            text.setTextInteractionFlags(Qt.TextSelectableByMouse|Qt.TextSelectableByKeyboard)
            d.layout().addWidget(text)
            d.show()
        if users:
            d = QDialog(self)
            d.setLayout(QGridLayout())
            text = QLabel("Steam user(s) found, which steam user to link?")
            text.setTextInteractionFlags(Qt.TextSelectableByMouse|Qt.TextSelectableByKeyboard)
            d.layout().addWidget(text)
            for un in users:
                b = QPushButton(un)
                b.clicked.connect(make_callback(self.assign_steam_user,users[un]))
                d.layout().addWidget(b)
            d.show()
            self.assign_steam_dialog = d

    def assign_steam_user(self,ud):
        self.fields["steam"]["userfile"].setText(ud["local"])
        self.fields["steam"]["shortcut_folder"].setText(ud["shortcut"])
        self.fields["steam"]["id"].setText(str(ud["account_id"]))
        self.assign_steam_dialog.close()

    def set_filepath(self,w):
        filename = QFileDialog.getOpenFileName(self,"Open Executable",w.text(),"Executable (*.vdf)")[0]
        w.setText(filename.replace("/","\\"))

    def save_close(self):
        save = {}
        for key_type in self.fields:
            save[key_type] = {}
            for key in self.fields[key_type]:
                save[key_type][key] = self.fields[key_type][key].text()
        f = open(self.app.config["accounts"],"wb")
        f.write(self.app.crypter.write(json.dumps(save)))
        f.close()
        self.app.set_accounts(save)
        self.delete()

    def delete(self):
        self.deleteLater()
