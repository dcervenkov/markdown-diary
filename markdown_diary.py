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
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
# from PyQt5.QtCore import pyqtRemoveInputHook # enable for debugging

from markdownhighlighter import MarkdownHighlighter
import markdown_math
import style
import diary


class MyQTextEdit(QtWidgets.QTextEdit):  # pylint: disable=too-few-public-methods
    """Modified QTextEdit that highlights all search matches
    """

    def __init__(self, parent=None):

        super(MyQTextEdit, self).__init__(parent)

    def highlightSearch(self, pattern):
        """Highlight all search occurences

        The search is case insensitive.

        Args:
            pattern (str): The text to be highlighted
        """

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


class DiaryApp(QtWidgets.QMainWindow):  # pylint: disable=too-many-public-methods,too-many-instance-attributes
    """Diary application class inheriting from QMainWindow
    """

    def __init__(self, parent=None):

        self.maxRecentItems = 10

        self.markdownAction = None
        self.newNoteAction = None
        self.saveNoteAction = None
        self.deleteNoteAction = None
        self.openDiaryAction = None
        self.searchLineAction = None
        self.recentDiariesActions = None

        self.searchLine = None
        self.toolbar = None
        self.fileMenu = None
        self.noteMenu = None
        self.noteDate = None
        self.noteId = None

        QtWidgets.QMainWindow.__init__(self, parent)

        renderer = markdown_math.HighlightRenderer()
        self.toMarkdown = markdown_math.MarkdownWithMath(renderer=renderer)

        self.tempFiles = []

        self.initUI()

        self.settings = QtCore.QSettings(
            "markdown-diary", application="settings")
        self.loadSettings()

        if len(self.recentDiaries):
            self.loadDiary(self.recentDiaries[0])
        else:
            self.text.setDisabled(True)
            self.saveNoteAction.setDisabled(True)
            self.newNoteAction.setDisabled(True)
            self.deleteNoteAction.setDisabled(True)
            self.markdownAction.setDisabled(True)
            self.searchLineAction.setDisabled(True)

    def closeEvent(self, event):
        """Check if there are unsaved changes and display dialog if there are

        This redefines the basic close event to give the user a chance to save
        his work. It also saves the current settings.

        Args:
            event (QEvent):
        """

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
        """Initialize the UI - create widgets, set their pars, etc."""

        self.window = QtWidgets.QWidget(self)
        self.splitter = QtWidgets.QSplitter()
        self.initToolbar()
        self.initMenu()

        self.text = MyQTextEdit(self)
        self.text.setAcceptRichText(False)
        self.text.setFont(QtGui.QFont("Ubuntu Mono"))
        self.text.textChanged.connect(self.setTitle)

        self.web = QWebEngineView(self)

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
        """Initialize toolbar - create QActions and bind to functions, etc."""

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
        self.deleteNoteAction.triggered.connect(
            lambda: self.deleteNote())  # pylint: disable=unnecessary-lambda

        self.searchLine = QtWidgets.QLineEdit(self)
        self.searchLine.setFixedWidth(200)
        self.searchLine.setPlaceholderText("Search...")
        self.searchLine.setClearButtonEnabled(True)

        self.searchLineAction = QtWidgets.QWidgetAction(self)
        self.searchLineAction.setDefaultWidget(self.searchLine)
        self.searchLineAction.setShortcut("Ctrl+F")
        self.searchLineAction.triggered.connect(
            lambda: self.searchLine.setFocus())  # pylint: disable=unnecessary-lambda
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

    def initMenu(self):
        """Create the main application menu - File, etc."""

        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.openDiaryAction)
        self.fileMenu.addSeparator()

        self.recentDiariesActions = []
        for _ in range(self.maxRecentItems):
            action = QtWidgets.QAction(self)
            action.setVisible(False)
            self.recentDiariesActions.append(action)
            self.fileMenu.addAction(action)

        self.noteMenu = self.menuBar().addMenu("&Note")
        self.noteMenu.addAction(self.newNoteAction)
        self.noteMenu.addAction(self.saveNoteAction)
        self.noteMenu.addAction(self.deleteNoteAction)

    def loadTree(self, metadata):
        """Load notes tree from diary metadata

         Load notes tree from diary metadata and populate the QTreeWidget
         with it.
        """

        entries = []

        for note in metadata:
            entries.append(QtWidgets.QTreeWidgetItem(
                [note["note_id"], note["date"], note["title"]]))

        self.tree.clear()
        self.tree.addTopLevelItems(entries)

    def loadSettings(self):
        """Load settings via self.settings QSettings object"""

        self.recentDiaries = self.settings.value("diary/recent", [])
        self.updateRecent()

        self.resize(self.settings.value(
            "window/size", QtCore.QSize(600, 400)))

        self.move(self.settings.value(
            "window/position", QtCore.QPoint(200, 200)))

        self.splitter.setSizes(
            [int(val) for val in self.settings.value("window/splitter", [70, 30])])

        toolBarArea = int(self.settings.value("window/toolbar_area",
                                              QtCore.Qt.TopToolBarArea))
        # addToolBar() actually just moves the specified toolbar if it
        # was already added, which is what we want
        self.addToolBar(QtCore.Qt.ToolBarArea(toolBarArea), self.toolbar)

        self.mathjax = self.settings.value(
            "mathjax/location",
            "https://cdn.mathjax.org/mathjax/latest/MathJax.js")

    def writeSettings(self):
        """Save settings via self.settings QSettings object"""

        self.settings.setValue("window/size", self.size())
        self.settings.setValue("window/position", self.pos())
        self.settings.setValue("window/splitter", self.splitter.sizes())
        self.settings.setValue("window/toolbar_area", self.toolBarArea(
            self.toolbar))

        if len(self.recentDiaries):
            self.settings.setValue("diary/recent", self.recentDiaries)

    def markdownToggle(self):
        """Switch between displaying Markdown source and rendered HTML"""

        if self.stack.currentIndex() == 1:
            self.stack.setCurrentIndex(0)
        else:
            self.stack.setCurrentIndex(1)
            self.displayHTMLRenderedMarkdown(self.text.toPlainText())

    def createHTML(self, markdownText):
        """Create full, valid HTML from Markdown source

        Args:
            markdownText (str): Markdown source to convert to HTML

        Returns:
            Full HTML page text.
        """

        html = style.header

        # We load MathJax only when there is a good chance there is
        # math in the note. We first perform inline math search as
        # as that should be faster then the re.DOTALL multiline
        # block math search, which gets executed only if we don't
        # find inline math.
        mathInline = re.compile(r"\$(.+?)\$")
        mathBlock = re.compile(r"^\$\$(.+?)^\$\$",
                               re.DOTALL | re.MULTILINE)

        if mathInline.search(markdownText or mathBlock.search(markdownText)):

            html += style.mathjax
            mathjaxScript = (
                '<script type="text/javascript" src="{}?config='
                'TeX-AMS-MML_HTMLorMML"></script>\n').format(self.mathjax)
            html += mathjaxScript

        html += self.toMarkdown(markdownText)  # pylint: disable=not-callable
        html += style.footer
        return html

    def displayHTMLRenderedMarkdown(self, markdownText):
        """Display HTML rendered Markdown"""

        html = self.createHTML(markdownText)

        # Without a real file, intra-note tag links (#header1) won't work
        with tempfile.NamedTemporaryFile(
                mode="w", prefix=".markdown-diary_", suffix=".tmp",
                dir=tempfile.gettempdir(), delete=False) as tmpf:
            tmpf.write(html)
            self.tempFiles.append(tmpf)

        # QWebEngineView resolves relative links (like # tags) with respect to
        # the baseUrl
        mainPath = os.path.realpath(__file__)
        self.web.setHtml(html, baseUrl=QtCore.QUrl.fromLocalFile(mainPath))

        if self.searchLine.text() != "":
            self.search()

    def newNote(self):
        """Create an empty note and add it to the QTreeWidget

        The note is not added to the diary until it is saved.
        """

        self.noteDate = datetime.date.today().isoformat()
        self.noteId = str(uuid.uuid1())

        newEntry = QtWidgets.QTreeWidgetItem(
            [self.noteId, self.noteDate, ""])

        self.tree.addTopLevelItem(newEntry)

        self.text.clear()
        self.stack.setCurrentIndex(0)
        self.text.setFocus()

    def saveNote(self):
        """Save the displayed note

        Either updates an existing note or adds a new one to a diary.
        """

        # Notes should begin with a title, so strip any whitespace,
        # including newlines from the beggining
        self.diary.saveNote(
            self.text.toPlainText().lstrip(), self.noteId, self.noteDate)
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
        """Delete a specified note

         If there are unsaved changes, prompt the user. Refresh note tree
         after deletion.

        Args:
            noteId (str, optional): UUID of the note to delete
        """

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
        """Display a file open dialog and load the selected diary

         Enable relevant toolbar items (new note, save note, etc.), in case
         no diary was open before and they were disabled.
        """

        fname = QtWidgets.QFileDialog.getOpenFileName(
            caption="Open Diary",
            filter="Markdown Files (*.md);;All Files (*)")[0]

        if fname:
            if self.isValidDiary(fname):
                self.loadDiary(fname)

                self.text.setDisabled(False)
                self.saveNoteAction.setDisabled(False)
                self.newNoteAction.setDisabled(False)
                self.deleteNoteAction.setDisabled(False)
                self.markdownAction.setDisabled(False)
                self.searchLineAction.setDisabled(False)
            else:
                print("ERROR:" + fname + "is not a valid diary file!")

    def isValidDiary(self, fname):
        """Check if a file path leads to a valid diary

        Args:
            fname (str): Path to a diary file to be validated.

        Returns:
            bool: True for valid, False for invalid diary.
        """

        # TODO Implement checks
        return True

    def loadDiary(self, fname):
        """Load diary from file

        Display last note from the diary.

        Args:
            fname (str): Path to a file containing a diary.
        """

        self.updateRecent(fname)
        self.diary = diary.Diary(fname)
        self.loadTree(self.diary.metadata)

        lastNoteId = self.diary.metadata[-1]["note_id"]
        self.tree.setCurrentItem(
            self.tree.findItems(lastNoteId, QtCore.Qt.MatchExactly)[0])
        self.stack.setCurrentIndex(1)

    def updateRecent(self, fname=""):
        """Update list of recently opened diaries

         When fname is specified, adds/moves the specified diary to the
         beggining of a list. Otherwise just populates the list in the file
         menu.

        Args:
             fname (str, optional): The most recent diary to be added/moved
                to the top of the list.
        """

        if fname != "":
            if fname in self.recentDiaries:
                self.recentDiaries.remove(fname)

            self.recentDiaries.insert(0, fname)

            if len(self.recentDiaries) > 10:
                del self.recentDiaries[:-10]

        for recent in self.recentDiariesActions:
            recent.setVisible(False)

        for i, recent in enumerate(self.recentDiaries):
            self.recentDiariesActions[i].setText(os.path.basename(recent))
            self.recentDiariesActions[i].setData(recent)
            self.recentDiariesActions[i].setVisible(True)
            # Multiple signals can be connected, so to avoid old signals we
            # disconnect them
            self.recentDiariesActions[i].triggered.disconnect()
            self.recentDiariesActions[i].triggered.connect(
                lambda: self.loadDiary(recent))

    def itemSelectionChanged(self):
        """Display a new selected note

         Prompts the user if there is unsaved work. If there is an active
         search, reruns it on the new note.
        """

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
            self.search()

    def displayNote(self, noteId):
        """Display a specified note"""

        self.text.setText(self.diary.getNote(self.diary.data, noteId))
        self.setTitle()
        self.noteId = noteId
        self.noteDate = self.diary.getNoteMetadata(
            self.diary.metadata, noteId)["date"]
        self.displayHTMLRenderedMarkdown(self.text.toPlainText())

    def search(self):
        """Search and highlight text in all notes

         Highlights text occurrences in the editor and web view. Searches all
         notes for the text and removes non-matching from the note tree. The
         text to search for is taken from the searchLine widget.
        """

        # Search in the editor
        self.text.highlightSearch(self.searchLine.text())

        # Search in the WebView
        self.web.findText("", QWebEnginePage.HighlightAllOccurrences)
        self.web.findText(self.searchLine.text(),
                          QWebEnginePage.HighlightAllOccurrences)
        self.web.findText(self.searchLine.text())

        # Search for matching notes
        entries = self.diary.searchNotes(self.searchLine.text())
        self.loadTree(entries)

    def searchNext(self):
        """Move main highlight (and scroll) to the next search match"""

        self.web.findText(self.searchLine.text(),
                          QWebEnginePage.FindWrapsAroundDocument)

        if len(self.text.extraSelections()):
            if not self.text.find(self.searchLine.text()):
                self.text.moveCursor(QtGui.QTextCursor.Start)
                self.text.find(self.searchLine.text())

    def setTitle(self):
        """Set the application title; add '*' if editor in dirty state"""

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
    """Run the whole QApplication"""

    app = QtWidgets.QApplication(sys.argv)
    # pyqtRemoveInputHook() # enable for debugging

    diaryApp = DiaryApp()
    diaryApp.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
