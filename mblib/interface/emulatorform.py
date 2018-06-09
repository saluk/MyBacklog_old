import json
import copy

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from mblib import sources

def make_callback(f, *args):
    return lambda: f(*args)

class EmulatorForm(QWidget):
    def __init__(self, app, message="", highlight_fields=[], dock=False):
        super(EmulatorForm, self).__init__()
        self.app = app
        
        layout = QGridLayout()
        scrollwidget = QWidget()
        layout.setContentsMargins(1,1,1,1)
        scrollwidget.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidget(scrollwidget)
        
        baselayout = QGridLayout()
        self.setLayout(baselayout)

        #Layout
        if not message:
            baselayout.addWidget(QLabel("Edit Emulators"))
        else:
            baselayout.addWidget(QLabel(message))
            
        baselayout.addWidget(scroll)
        

        def highlight(w):
            w.setFont(QFont("Times",10,QFont.Bold,True))
            pass

        #Fields
        self.fields = {}
        i = 1
        for emu in sorted(sources.all.keys()):
            if sources.all[emu].__class__.__name__ != "EmulatorSource":
                continue
            self.fields[emu] = copy.deepcopy(self.app.games.local["emulators"].get(emu,{}))
            
            w = QLabel(emu.capitalize()+" emulator path")
            if emu+"_exe" in highlight_fields:
                highlight(w)
            layout.addWidget(w,i,0)

            emu_args = self.fields[emu].get("args",[])
            if not emu_args:
                arg0 = ""
                argrest = []
            else:
                arg0 = emu_args[0]
                argrest = emu_args[1:]
            w = QLineEdit(arg0)
            layout.addWidget(w,i,1)
            self.fields[emu]["w1"] = w
            
            button = QPushButton("...")
            layout.addWidget(button,i,2)
            button.clicked.connect(make_callback(self.set_exepath,w))
            
            w = QLineEdit(" ".join(argrest))
            layout.addWidget(w,i+1,1)
            self.fields[emu]["w2"] = w
            
            rom_extension = self.fields[emu].get("rom_extension","*.*")
            w = QLineEdit(rom_extension)
            layout.addWidget(w,i+2,1)
            self.fields[emu]["w3"] = w
            
            i+=3

        #Save button
        if not dock:
            button = QPushButton("Save")
            baselayout.addWidget(button,i,0)
            button.clicked.connect(self.save_close)

        print(self.fields)
        scrollwidget.adjustSize()

    def set_exepath(self,w):
        filename = QFileDialog.getOpenFileName(self,"Open Executable",w.text(),"Executable (*)")[0]
        w.setText(filename.replace("/","\\"))

    def save_close(self):
        for emu in self.fields:
            args = [x for x in [self.fields[emu]["w1"].text()]+self.fields[emu]["w2"].text().split(" ") if x.strip()]
            self.app.games.local["emulators"][emu] = {"args":args,"rom_extension":self.fields[emu]["w3"].text()}
        self.app.save()
        self.delete()

    def delete(self):
        self.deleteLater()
