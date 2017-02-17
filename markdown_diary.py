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
from PyQt5.QtCore import pyqtRemoveInputHook

from markdownhighlighter import MarkdownHighlighter
import markdown_math
import style
import diary


class MyQTextEdit(QtWidgets.QTextEdit):

    def __init__(self, parent=None):

        super(MyQTextEdit, self).__init__(parent)

    def highlightSearch(self, pattern):

        self.moveCursor(QtGui.QTextCursor.Start)
        color = QtGui.QColor("yellow")

        extraSelections = []

        while self.find(pattern):
            extra = QtWidgets.QTextEdit.ExtraSelection()
            extra.format.setBackground(color)
            extra.cursor = self.textCursor()
            extraSelections.append(extra)

        self.setExtraSelections(extraSelections)

        self.moveCursor(QtGui.QTextCursor.Start)
        self.find(pattern)


class DiaryApp(QtWidgets.QMainWindow):

    def __init__(self, parent=None):

        QtWidgets.QMainWindow.__init__(self, parent)

        renderer = markdown_math.HighlightRenderer()
        self.toMarkdown = markdown_math.MarkdownWithMath(renderer=renderer)

        self.tempFiles = []

        self.initUI()

        self.settings = QtCore.QSettings(
                "markdown-diary", application="settings")
        self.loadSettings()

        self.loadDiary(self.recent_diaries[0])

    def closeEvent(self, event):

        if self.text.document().isModified():
            discardMsg = ("You have unsaved changes. "
                          "Do you want to discard them?")
            reply = QtWidgets.QMessageBox.question(
                    self, 'Message', discardMsg,
                    QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.No:
                event.ignore()
                return

        self.writeSettings()

    def initUI(self):

        self.window = QtWidgets.QWidget(self)
        self.splitter = QtWidgets.QSplitter()
        self.initToolbar()

        self.text = MyQTextEdit(self)
        self.text.setAcceptRichText(False)
        self.text.setFont(QtGui.QFont("Ubuntu Mono"))
        self.text.textChanged.connect(self.setTitle)

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
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Id", "Date", "Title"])
        self.tree.setColumnHidden(0, True)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(1, QtCore.Qt.DescendingOrder)
        self.tree.itemSelectionChanged.connect(self.itemSelectionChanged)
        self.tree.itemDoubleClicked.connect(self.markdownToggle)

        self.splitter.addWidget(self.stack)
        self.splitter.addWidget(self.tree)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.splitter)

        self.window.setLayout(layout)

    def initToolbar(self):

        self.markdownAction = QtWidgets.QAction(
                QtGui.QIcon.fromTheme("down"), "Toggle Markdown", self)
        self.markdownAction.setShortcut("Ctrl+M")
        self.markdownAction.setStatusTip("Toggle markdown rendering")
        self.markdownAction.triggered.connect(self.markdownToggle)

        self.newNoteAction = QtWidgets.QAction(
                QtGui.QIcon.fromTheme("document-new"), "New note", self)
        self.newNoteAction.setShortcut("Ctrl+N")
        self.newNoteAction.setStatusTip("Create a new note")
        self.newNoteAction.triggered.connect(self.newNote)

        self.saveNoteAction = QtWidgets.QAction(
                QtGui.QIcon.fromTheme("document-save"), "Save note", self)
        self.saveNoteAction.setShortcut("Ctrl+S")
        self.saveNoteAction.setStatusTip("Save note")
        self.saveNoteAction.triggered.connect(self.saveNote)

        self.openDiaryAction = QtWidgets.QAction(
                QtGui.QIcon.fromTheme("document-open"), "Open diary", self)
        self.openDiaryAction.setShortcut("Ctrl+O")
        self.openDiaryAction.setStatusTip("Open diary")
        self.openDiaryAction.triggered.connect(self.openDiary)

        self.deleteNoteAction = QtWidgets.QAction(
                QtGui.QIcon.fromTheme("remove"), "Delete Note", self)
        self.deleteNoteAction.setShortcut("Del")
        self.deleteNoteAction.setStatusTip("Delete note")
        self.deleteNoteAction.triggered.connect(lambda: self.deleteNote())

        self.searchLine = QtWidgets.QLineEdit(self)
        self.searchLine.setFixedWidth(200)
        self.searchLine.setPlaceholderText("Search...")
        self.searchLine.setClearButtonEnabled(True)

        self.searchLineAction = QtWidgets.QWidgetAction(self)
        self.searchLineAction.setDefaultWidget(self.searchLine)
        self.searchLineAction.setShortcut("Ctrl+F")
        self.searchLineAction.triggered.connect(
                lambda: self.searchLine.setFocus())
        self.searchLine.textChanged.connect(self.search)
        self.searchLine.returnPressed.connect(self.searchNext)

        self.toolbar = self.addToolBar("Main toolbar")
        self.toolbar.setFloatable(False)
        self.toolbar.setAllowedAreas(
                QtCore.Qt.TopToolBarArea | QtCore.Qt.BottomToolBarArea)
        self.toolbar.addAction(self.markdownAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.newNoteAction)
        self.toolbar.addAction(self.saveNoteAction)
        self.toolbar.addAction(self.deleteNoteAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.openDiaryAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.searchLineAction)

    def loadTree(self, metadata):

        entries = []

        for note in metadata:
            entries.append(QtWidgets.QTreeWidgetItem(
                [note["note_id"], note["date"], note["title"]]))

        self.tree.clear()
        self.tree.addTopLevelItems(entries)

    def loadSettings(self):

        self.recent_diaries = ["/home/dc/bin/markdown-diary/temp/diary.md"]

        self.resize(self.settings.value(
            "window/size", QtCore.QSize(600, 400)))

        self.move(self.settings.value(
            "window/position", QtCore.QPoint(200, 200)))

        self.splitter.setSizes(list(map(int, self.settings.value(
            "window/splitter", [70, 30]))))

        toolBarArea = int(self.settings.value("window/toolbar_area",
                                              QtCore.Qt.TopToolBarArea))
        # addToolBar() actually just moves the specified toolbar if it
        # was already added, which is what we want
        self.addToolBar(QtCore.Qt.ToolBarArea(toolBarArea), self.toolbar)

        self.mathjax = self.settings.value(
                "mathjax/location",
                "https://cdn.mathjax.org/mathjax/latest/MathJax.js")

    def writeSettings(self):

        self.settings.setValue("window/size", self.size())
        self.settings.setValue("window/position", self.pos())
        self.settings.setValue("window/splitter", self.splitter.sizes())
        self.settings.setValue("window/toolbar_area", self.toolBarArea(
            self.toolbar))

    def markdownToggle(self):

        if self.stack.currentIndex() == 1:
            self.stack.setCurrentIndex(0)
        else:
            self.stack.setCurrentIndex(1)
            self.markdown()

    def markdown(self):

        html = style.header

        # We load MathJax only when there is a good chance there is
        # math in the note. We first perform inline math search as
        # as that should be faster then the re.DOTALL multiline
        # block math search, which gets executed only if we don't
        # find inline math.
        math_inline = re.compile(r"\$(.+?)\$")
        math_block = re.compile(r"^\$\$(.+?)^\$\$",
                                re.DOTALL | re.MULTILINE)

        if (math_inline.search(self.text.toPlainText()) or
                math_block.search(self.text.toPlainText())):

            html += style.mathjax
            mathjax_script = (
                '<script type="text/javascript" src="{}?config='
                'TeX-AMS-MML_HTMLorMML"></script>\n').format(self.mathjax)
            html += mathjax_script

        html += self.toMarkdown(self.text.toPlainText())
        html += style.footer

        # Without a real file, intra-note tag links (#header1) won't work
        with tempfile.NamedTemporaryFile(
                mode="w", prefix=".markdown-diary_", suffix=".tmp",
                dir=tempfile.gettempdir(), delete=False) as tmpf:
            tmpf.write(html)
            self.tempFiles.append(tmpf)

        # QWebView resolves relative links (like # tags) with respect to
        # the baseUrl
        mainPath = os.path.realpath(__file__)
        self.web.setHtml(html, baseUrl=QtCore.QUrl.fromLocalFile(mainPath))

        if self.searchLine.text() != "":
            self.search(self.searchLine.text())

    def newNote(self):

        self.noteDate = datetime.date.today().isoformat()
        self.noteId = str(uuid.uuid1())

        # TODO Add note to tree

        self.text.clear()
        self.stack.setCurrentIndex(0)

    def saveNote(self):

        self.diary.saveNote(
                self.text.toPlainText(), self.noteId, self.noteDate)
        self.text.document().setModified(False)
        self.setTitle()
        self.loadTree(self.diary.metadata)

        # TODO This block is here to disallow reloading of self.text
        # which moves the cursor up. Make it more elegant than this!
        self.tree.blockSignals(True)
        self.tree.setCurrentItem(
                self.tree.findItems(self.noteId, QtCore.Qt.MatchExactly)[0])
        self.tree.blockSignals(False)

    def deleteNote(self, noteId=None):

        deleteMsg = "Do you really want to delete the note?"
        reply = QtWidgets.QMessageBox.question(
                self, 'Message', deleteMsg,
                QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.No:
            return

        if noteId is None:
            noteId = self.noteId
        nextNoteId = self.tree.itemBelow(self.tree.currentItem()).text(0)
        self.diary.deleteNote(noteId)
        self.loadTree(self.diary.metadata)
        self.tree.setCurrentItem(
                self.tree.findItems(nextNoteId, QtCore.Qt.MatchExactly)[0])

    def openDiary(self):

        fname = QtWidgets.QFileDialog.getOpenFileName(
                caption="Open Diary",
                filter="Markdown Files (*.md);;All Files (*)")[0]

        if fname:
            if self.isValidDiary(fname):
                self.loadDiary(fname)
            else:
                print("ERROR:" + fname + "is not a valid diary file!")

    def isValidDiary(self, fname):

        # TODO Implement checks
        return True

    def loadDiary(self, fname):

        self.diary = diary.Diary(fname)
        self.loadTree(self.diary.metadata)

        lastNoteId = self.diary.metadata[-1]["note_id"]
        self.tree.setCurrentItem(
                self.tree.findItems(lastNoteId, QtCore.Qt.MatchExactly)[0])
        self.stack.setCurrentIndex(1)

    def itemSelectionChanged(self):

        if self.text.document().isModified():
            discardMsg = ("You have unsaved changes. "
                          "Do you want to discard them?")
            reply = QtWidgets.QMessageBox.question(
                    self, 'Message', discardMsg,
                    QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.No:
                self.tree.blockSignals(True)
                self.tree.setCurrentItem(self.tree.findItems(
                            self.noteId, QtCore.Qt.MatchExactly)[0])
                self.tree.blockSignals(False)
                return

        if len(self.tree.selectedItems()) != 1:
            return

        item = self.tree.selectedItems()[0]

        self.displayNote(item.text(0))

        if self.searchLine.text() != "":
            self.search(self.searchLine.text())

    def displayNote(self, noteId):

        self.text.setText(self.diary.getNote(self.diary.data, noteId))
        self.setTitle()
        self.noteId = noteId
        self.noteDate = self.diary.getNoteMetadata(
                self.diary.metadata, noteId)["date"]
        self.markdown()

    def search(self, text):

        # Search in the editor
        self.text.highlightSearch(self.searchLine.text())

        # Search in the WebView
        self.web.findText("", QtWebKitWidgets.QWebPage.HighlightAllOccurrences)
        self.web.findText(self.searchLine.text(),
                          QtWebKitWidgets.QWebPage.HighlightAllOccurrences)
        self.web.findText(self.searchLine.text())

        # Search for matching notes
        entries = self.diary.searchNotes(self.searchLine.text())
        self.loadTree(entries)

    def searchNext(self):

        self.web.findText(self.searchLine.text(),
                          QtWebKitWidgets.QWebPage.FindWrapsAroundDocument)

        if len(self.text.extraSelections()):
            if not self.text.find(self.searchLine.text()):
                self.text.moveCursor(QtGui.QTextCursor.Start)
                self.text.find(self.searchLine.text())

    def setTitle(self):

        if self.text.document().isModified():
            self.setWindowTitle("*Markdown Diary")
        else:
            self.setWindowTitle("Markdown Diary")

    def __del__(self):

        # Delete temporary files
        # We put it into __del__ deliberately, so if one wants, one can avoid
        # the temporary files being deleted by killing the process. This might
        # be useful, e.g., in case of accidental over-write.
        for f in self.tempFiles:
            os.unlink(f.name)


def main():

    app = QtWidgets.QApplication(sys.argv)
    pyqtRemoveInputHook()

    main = DiaryApp()
    main.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
