import json

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

def make_callback(f, *args):
    return lambda: f(*args)

class PathsForm(QWidget):
    def __init__(self, app, message="", highlight_fields=[],dock=False):
        super(PathsForm, self).__init__()
        self.app = app

        #Layout
        layout = QGridLayout()
        if not message:
            layout.addWidget(QLabel("Edit Paths"))
        else:
            layout.addWidget(QLabel(message))

        def highlight(w):
            w.setFont(QFont("Times",10,QFont.Bold,True))
            pass

        #Fields
        self.fields = {"games":"","local":"","accounts":""}
        
        w = QLabel("Game database file")
        s = "If you put this file in a dropbox or otherwise synced location, your database will be accessible from multiple devices."
        w.setToolTip(s)
        if "games" in highlight_fields:
            highlight(w)
        layout.addWidget(w,1,0)
        w = QLineEdit(self.app.config["games"])
        w.setToolTip(s)
        layout.addWidget(w,1,1)
        button = QPushButton("...")
        layout.addWidget(button,1,2)
        button.clicked.connect(make_callback(self.set_filepath,w))
        self.fields["games"] = w
        
        w = QLabel("Local game data file")
        s = "Data only relevant to this machine, such as paths to game executables, are stored here. Don't store in a shared location."
        w.setToolTip(s)
        if "local" in highlight_fields:
            highlight(w)
        layout.addWidget(w,2,0)
        w = QLineEdit(self.app.config["local"])
        w.setToolTip(s)
        layout.addWidget(w,2,1)
        button = QPushButton("...")
        layout.addWidget(button,2,2)
        button.clicked.connect(make_callback(self.set_filepath,w))
        self.fields["local"] = w
        
        w = QLabel("Path to accounts file")
        s = "File can be put in a shared location but might be a security risk. Passwords to game stores are stored here."
        w.setToolTip(s)
        if "accounts" in highlight_fields:
            highlight(w)
        layout.addWidget(w,3,0)
        w = QLineEdit(self.app.config["accounts"])
        w.setToolTip(s)
        layout.addWidget(w,3,1)
        button = QPushButton("...")
        layout.addWidget(button,3,2)
        button.clicked.connect(make_callback(self.set_filepath,w))
        self.fields["accounts"] = w

        #Save button
        if not dock:
            button = QPushButton("Save")
            layout.addWidget(button,9,0)
            button.clicked.connect(self.save_close)

        print(self.fields)
        self.setLayout(layout)

    def set_filepath(self,w):
        filename = QFileDialog.getSaveFileName(self,"Set filename",w.text(),"JSON (*.json)")[0]
        w.setText(filename.replace("/","\\"))

    def save_close(self):
        save = {}
        for field in self.fields:
            save[field] = self.fields[field].text()
        self.app.config.update(save)
        self.app.save_config()
        self.delete()

    def delete(self):
        self.deleteLater()