#!/usr/bin/env python3
""" markdown-diary

TODO: Write description
"""


import sys

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5 import QtWebKitWidgets
from PyQt5 import QtWebKit

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

        # This displays incorrectly
        # self.webSettings = QtWebKit.QWebSettings.globalSettings()
        # self.webSettings.setUserStyleSheetUrl(
        #     QtCore.QUrl("file:///home/dc/bin/markdown-diary/github-markdown.css"))

        self.setCentralWidget(self.window)

        self.setWindowTitle("Markdown Diary")

        self.stack = QtWidgets.QStackedWidget()
        self.stack.addWidget(self.text)
        self.stack.addWidget(self.web)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(2)
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

        css_include = """
<link rel="stylesheet" href="file:///home/dc/bin/markdown-diary/github-markdown.css">
<style>
    .markdown-body {
        box-sizing: border-box;
        min-width: 200px;
        max-width: 980px;
        margin: 0 auto;
        padding: 45px;
    }
</style>
"""
        css_article_start = '<article class="markdown-body">\n'
        css_article_end = '</article>\n'
        html = css_include
        html += css_article_start
        html += self.toMarkdown(self.text.toPlainText())
        html += css_article_end

        self.web.setHtml(html)

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
