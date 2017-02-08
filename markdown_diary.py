#!/usr/bin/env python3
""" markdown-diary

TODO: Write description
"""


import os
import sys
import tempfile
import uuid
import re
import datetime

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


class DiaryApp(QtWidgets.QMainWindow):

    def __init__(self, parent=None):

        QtWidgets.QMainWindow.__init__(self, parent)

        renderer = HighlightRenderer()

        self.toMarkdown = mistune.Markdown(renderer=renderer)
        self.initUI()

        self.loadSettings()

        self.openDiary(self.recent_diaries[0])

    def __del__(self):

        pass

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

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.stack)
        layout.addWidget(self.tree)

        self.window.setLayout(layout)

    def initToolbar(self):

        self.markdownAction = QtWidgets.QAction(
                QtGui.QIcon.fromTheme("down"), "Markdown", self)
        self.markdownAction.setShortcut("Ctrl+M")
        self.markdownAction.setStatusTip("Toggle markdown rendering")
        self.markdownAction.triggered.connect(self.markdownToggle)

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

    def loadTree(self, metadata):

        entries = []

        for note in metadata:
            entries.append(QtWidgets.QTreeWidgetItem(
                [note["date"], note["title"]]))

        self.tree.addTopLevelItems(entries)

    def loadSettings(self):

        self.recent_diaries = ["/home/dc/bin/markdown-diary/temp/diary.md"]

    def markdownToggle(self):

        if self.stack.currentIndex() == 1:
            self.stack.setCurrentIndex(0)
        else:
            self.stack.setCurrentIndex(1)
            self.markdown()

    def markdown(self):

            css_include = ('<link rel="stylesheet" href="file:///'
                           'home/dc/bin/markdown-diary/github-markdown.css">\n'
                           '<link rel="stylesheet" href="file:///'
                           'home/dc/bin/markdown-diary/github-pygments.css">\n'
                           '<style>\n'
                           '    .markdown-body {\n'
                           '        box-sizing: border-box;\n'
                           '        min-width: 200px;\n'
                           '        max-width: 980px;\n'
                           '        margin: 0 auto;\n'
                           '        padding: 45px;\n'
                           '    }\n'
                           '</style>\n')

            css_article_start = '<article class="markdown-body">\n'
            css_article_end = '</article>\n'
            html = css_include
            html += css_article_start
            html += self.toMarkdown(self.text.toPlainText())
            html += css_article_end

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

        self.note_date = print(datetime.date.today().isoformat())
        self.noteId = uuid.uuid1()

        self.text.clear()

    def saveNote(self):

        with open(self.diary) as df, tempfile.NamedTemporaryFile(
                mode="w", prefix=".diary_", suffix=".tmp",
                dir=os.path.dirname(self.diary), delete=False) as tmpf:
            tmpf.write(self.text.toPlainText())
        os.replace(tmpf.name, self.diary)

    def openDiary(self, diary):

        with open(diary) as f:
            self.diaryData = f.read()

        self.noteMetadata = self.getNotesMetadata(self.diaryData)
        self.loadTree(self.noteMetadata)

        self.text.setText(self.getNote(self.diaryData,
                          self.noteMetadata[-1]["note_id"]))
        self.stack.setCurrentIndex(1)
        self.markdown()

    def getNotesMetadata(self, diaryData):

        reHeader = re.compile(
            r"""^<!---                         # Beggining of Markdown comment
                (?:\n|\r\n)                    # Unix|Windows non-capturing \n
                markdown-diary\ note\ metadata # Mandatory first line
                (.*?)                          # Any characters including \n
                --->                           # End of Markdown comment
                """, re.MULTILINE | re.VERBOSE | re.DOTALL)

        matches = reHeader.finditer(diaryData)

        metadata = []
        for match in matches:
            metaDict = {}
            for line in diaryData[
                    match.start():match.end()].splitlines()[2:-1]:
                key, val = line.partition("=")[::2]
                metaDict[key.strip()] = val.strip()

            date = diaryData[match.end():].splitlines()[1]
            title = diaryData[match.end():].splitlines()[3].strip("# ")

            metaDict["date"] = date
            metaDict["title"] = title

            metadata.append(metaDict)

        return metadata

    def getNote(self, diaryData, noteId):

        reHeader = re.compile(
            r"""^<!---
                (?:\n|\r\n)
                markdown-diary\ note\ metadata
                (.*?)
                note_id\ =\                     # Hashtag for PEP8 compiance
                """ + noteId +
            r"""(.*?)
                --->
                (?:\n|\r\n)*
                [0-9]{4}-[0-9]{2}-[0-9]{2}      # Date in a YYYY-MM-DD format
                (?:\n|\r\n)*
                """, re.MULTILINE | re.VERBOSE | re.DOTALL)

        reHeaderNext = re.compile(
                r'^<!---(?:\n|\r\n)markdown-diary note metadata(?:\n|\r\n)',
                re.MULTILINE)

        header = reHeader.search(diaryData)
        nextHeader = reHeaderNext.search(diaryData, header.end())

        if nextHeader is None:
            return diaryData[header.end():]
        else:
            return diaryData[header.end(): nextHeader.start()]


def main():

    app = QtWidgets.QApplication(sys.argv)

    main = DiaryApp()
    main.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
