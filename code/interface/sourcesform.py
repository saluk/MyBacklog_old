import json
import copy

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from code import sources

def make_callback(f, *args):
    return lambda: f(*args)

class SourcesForm(QWidget):
    def __init__(self, app, message="", highlight_fields=[], dock=False):
        super(SourcesForm, self).__init__()
        self.app = app
        
        superlayout = QGridLayout()

        #Layout
        layout = QGridLayout()
        self.layout = layout
        if not message:
            superlayout.addWidget(QLabel(message or "Edit Sources"),0,0)
        else:
            superlayout.addWidget(QLabel(message),0,0)
            
        
        self.layout.setContentsMargins(1,1,1,1)
        scrollwidget = QWidget()
        scrollwidget.setLayout(self.layout)
        scroll = QScrollArea()
        scroll.setWidget(scrollwidget)
        
        superlayout.addWidget(scroll,1,0)

        def highlight(w):
            w.setFont(QFont("Times",10,QFont.Bold,True))
            pass

        #Fields
        self.fields = {}
        self.i = 1
        for name in sorted(sources.all.keys()):
            source_inst = sources.all[name]
            self.add_source(name,source_inst.__class__.__name__,getattr(source_inst,"editable",True))

        button = QPushButton("Add Source")
        superlayout.addWidget(button,2,0)
        button.clicked.connect(lambda *args:self.add_source())
        
        #Save button
        button = QPushButton("Save")
        superlayout.addWidget(button,3,0)
        button.clicked.connect(self.save_close)

        print(self.fields)
        self.setLayout(superlayout)
        scrollwidget.adjustSize()
        
    def add_source(self,name="",classname="",editable=True):
        field = name
        if not field:
            field = self.i
        self.fields[field] = {}
    
        w = QLineEdit(name)
        self.layout.addWidget(w,self.i,0)
        self.fields[field]["w_name"] = w
        if not editable:
            w.setReadOnly(True)
        
        w = QComboBox()
        for clsname in sources.classes:
            if not editable and clsname != classname:
                continue
            w.addItem(clsname)
        w.setCurrentText(classname)
        self.layout.addWidget(w,self.i,1)
        self.fields[field]["w_class"] = w
        
        self.fields[field]["editable"] = editable
        
        self.i+=1

    def save_close(self):
        sd = self.app.games.source_definitions
        for field in self.fields.values():
            if not field["editable"]:
                continue
            name = field["w_name"].text().strip()
            if not name:
                continue
            classname = field["w_class"].currentText()
            if name not in sd:
                sd[name] = {}
            sd[name]["class"] = classname
        sources.register_sources(sd)
        self.app.save()
        self.delete()

    def delete(self):
        self.deleteLater()
