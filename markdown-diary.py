#!/usr/bin/env python3
""" markdown-diary

TODO: Write description
"""


import os
import sys
import tempfile

from PyQt5 import QtGui, QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtWebKitWidgets

from markdownhighlighter import MarkdownHighlighter

import mistune
import pygments
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html


class HighlightRenderer(mistune.Renderer):
    def block_code(self, code, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                mistune.escape(code)
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except pygments.util.ClassNotFound:
            return '\n<pre><code>%s</code></pre>\n' % \
                mistune.escape(code)

        formatter = html.HtmlFormatter()
        return pygments.highlight(code, lexer, formatter)


class Main(QtWidgets.QMainWindow):

    def __init__(self, parent=None):

        QtWidgets.QMainWindow.__init__(self, parent)

        renderer = HighlightRenderer()

        self.toMarkdown = mistune.Markdown(renderer=renderer)
        self.initUI()

        self.diary = "/home/dc/bin/markdown-diary/temp/diary.md"

    def initUI(self):

        self.window = QtWidgets.QWidget(self)
        self.initToolbar()

        self.text = QtWidgets.QTextEdit(self)
        self.text.setAcceptRichText(False)
        self.text.setFont(QtGui.QFont("Ubuntu Mono"))

        self.web = QtWebKitWidgets.QWebView(self)

        # This displays incorrectly
        # self.webSettings = QtWebKit.QWebSettings.globalSettings()
        # self.webSettings.setUserStyleSheetUrl(
        #     QtCore.QUrl("file:///home/dc/bin/markdown-diary/github-markdown.css"))

        self.highlighter = MarkdownHighlighter(self.text)

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

        self.markdownAction = QtWidgets.QAction(
                QtGui.QIcon.fromTheme("down"), "Markdown", self)
        self.markdownAction.setShortcut("Ctrl+M")
        self.markdownAction.setStatusTip("Toggle markdown rendering")
        self.markdownAction.triggered.connect(self.markdown)

        self.newNoteAction = QtWidgets.QAction(
                QtGui.QIcon.fromTheme("add"), "New note", self)
        self.newNoteAction.setShortcut("Ctrl+N")
        self.newNoteAction.setStatusTip("Create a new note")
        self.newNoteAction.triggered.connect(self.newNote)

        self.saveNoteAction = QtWidgets.QAction(
                QtGui.QIcon.fromTheme("document-save"), "Save", self)
        self.saveNoteAction.setShortcut("Ctrl+S")
        self.saveNoteAction.setStatusTip("Save note")
        self.saveNoteAction.triggered.connect(self.saveNote)

        self.openDiaryAction = QtWidgets.QAction(
                QtGui.QIcon.fromTheme("document-open"), "Open diary", self)
        self.openDiaryAction.setShortcut("Ctrl+O")
        self.openDiaryAction.setStatusTip("Open diary")
        self.openDiaryAction.triggered.connect(self.openDiary)

        self.toolbar = self.addToolBar("Main toolbar")
        self.toolbar.addAction(self.markdownAction)
        self.toolbar.addAction(self.newNoteAction)
        self.toolbar.addAction(self.saveNoteAction)
        self.toolbar.addAction(self.openDiaryAction)

    def initTree(self):

        entries = []
        for i in range(1, 11):
            entries.append(QtWidgets.QTreeWidgetItem(["2017-01-01", "Entry " + str(i)]))
        self.tree.addTopLevelItems(entries)

    def markdown(self):

        # TODO: Refactor css_include
        css_include = """
<link rel="stylesheet" href="file:///home/dc/bin/markdown-diary/github-markdown.css">
<link rel="stylesheet" href="file:///home/dc/bin/markdown-diary/github-pygments.css">
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

        if self.stack.currentIndex() == 1:
            self.stack.setCurrentIndex(0)
        else:
            self.stack.setCurrentIndex(1)

            # Without a real file, intra-note tag links (#header1) won't work
            with tempfile.NamedTemporaryFile(
                    mode="w", prefix=".markdown-diary_", suffix=".tmp",
                    dir=tempfile.gettempdir(), delete=False) as tmpf:
                tmpf.write(html)

            # QWebView resolves relative links (like # tags) with respect to
            # the baseUrl
            self.web.setHtml(html, baseUrl=QtCore.QUrl(
                "file://" + tmpf.name))

        # TODO: Delete tmp files

    def newNote(self):

        print("New note")

    def saveNote(self):

        with open(self.diary) as df, tempfile.NamedTemporaryFile(
                mode="w", prefix=".diary_", suffix=".tmp",
                dir=os.path.dirname(self.diary), delete=False) as tmpf:
            tmpf.write(self.text.toPlainText())
        os.replace(tmpf.name, self.diary)

    def openDiary(self):

        with open(self.diary) as f:
            self.diaryData = f.read()
        self.text.setText(self.getNote())

    def getNote(self):

        return self.diaryData


def main():

    app = QtWidgets.QApplication(sys.argv)

    main = Main()
    main.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
