#!/usr/bin/env python3
""" markdown-diary

TODO: Write description
"""


import sys

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5 import QtWebKitWidgets


class Main(QtWidgets.QMainWindow):

    def __init__(self, parent=None):

        QtWidgets.QMainWindow.__init__(self, parent)
        self.initUI()

    def initUI(self):

        self.window = QtWidgets.QWidget(self)

        self.text = QtWidgets.QTextEdit(self)
        self.web = QtWebKitWidgets.QWebView(self)

        self.setCentralWidget(self.window)

        self.setWindowTitle("Markdown Diary")

        self.stack = QtWidgets.QStackedWidget()
        self.stack.addWidget(self.text)
        self.stack.addWidget(self.web)

        tree_model = QtWidgets.QFileSystemModel()
        tree_model.setRootPath("/")
        self.tree = QtWidgets.QTreeView()
        self.tree.setModel(tree_model)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.stack)
        layout.addWidget(self.tree)

        self.window.setLayout(layout)

def main():

    app = QtWidgets.QApplication(sys.argv)

    main = Main()
    main.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
