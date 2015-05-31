import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

def make_callback(f, *args):
    return lambda: f(*args)

class LogForm(QWidget):
    def __init__(self, app):
        super(LogForm, self).__init__()
        self.app = app

        #Layout
        layout = QGridLayout()
        layout.addWidget(QLabel("Log Window"))
        
        w = QTextEdit()
        layout.addWidget(w)
        self.text_edit = w

        self.setLayout(layout)
        
        self.set_text()

    def set_text(self):
        self.text_edit.setText(self.app.log.read())
        self.text_edit.moveCursor(QTextCursor.End)
        
    def add_text(self,text):
        self.text_edit.append(text)
        self.text_edit.moveCursor(QTextCursor.End)