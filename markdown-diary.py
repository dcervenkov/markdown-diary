#!/usr/bin/env python3
""" markdown-diary

TODO: Write description
"""


import sys

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5 import QtWebKitWidgets

import mistune


class Main(QtWidgets.QMainWindow):

    def __init__(self, parent=None):

        QtWidgets.QMainWindow.__init__(self, parent)
        self.toMarkdown = mistune.Markdown()
        self.initUI()

    def initUI(self):

        self.window = QtWidgets.QWidget(self)
        self.initToolbar()

        self.text = QtWidgets.QTextEdit(self)
        self.web = QtWebKitWidgets.QWebView(self)

        self.setCentralWidget(self.window)

        self.setWindowTitle("Markdown Diary")

        self.stack = QtWidgets.QStackedWidget()
        self.stack.addWidget(self.text)
        self.stack.addWidget(self.web)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(2);
        self.tree.setHeaderLabels(["Date", "Title"])
        self.initTree()

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.stack)
        layout.addWidget(self.tree)

        self.window.setLayout(layout)

    def initToolbar(self):

        self.markdownAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("down"), "New", self)
        self.markdownAction.setShortcut("Ctrl+M")
        self.markdownAction.setStatusTip("Toggle markdown rendering.")
        self.markdownAction.triggered.connect(self.markdown)

        self.toolbar = self.addToolBar("Main toolbar")
        self.toolbar.addAction(self.markdownAction)

    def initTree(self):

        entries = []
        for i in range(1, 11):
            entries.append(QtWidgets.QTreeWidgetItem(["2017-01-01", "Entry " + str(i)]))
        self.tree.addTopLevelItems(entries)

    def markdown(self):

        self.web.setHtml(self.toMarkdown(self.text.toPlainText()))

        if self.stack.currentIndex() == 1:
            self.stack.setCurrentIndex(0)
        else:
            self.stack.setCurrentIndex(1)


def main():

    app = QtWidgets.QApplication(sys.argv)

    main = Main()
    main.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
