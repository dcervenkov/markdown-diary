#!/usr/bin/env python3
"""This module contains the main markdown-diary app code.

Markdown diary is a simple note taking app build on PyQt5. Its diaries are
stored as plain text markdown files. The app has support for several features
not included in plain markdown, such as tables, mathjax math rendering and
syntax highlighting.
"""
import os
import sys
import uuid
import re
import datetime

from PyQt5 import QtGui, QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
# from PyQt5.QtCore import pyqtRemoveInputHook # enable for debugging

from markdownhighlighter import MarkdownHighlighter
import markdown_math
import style
import diary


class DummyItemDelegate(QtWidgets.QItemDelegate):  # pylint: disable=too-few-public-methods
    """A class used to modify behavior and appearance of the QtTreeWidget.

    This class is used to disable editing for specific columns as well as
    increase row height.
    """

    def createEditor(self, parent, option, index):
        """Do nothing to disable editing."""
        pass

    def sizeHint(self, _option, _index):  # pylint: disable=no-self-use
        """Increase row size.

        This is used in the QTreeWidget.
        """
        return QtCore.QSize(1, 20)


class MyQTextEdit(QtWidgets.QTextEdit):  # pylint: disable=too-few-public-methods
    """Modified QTextEdit that highlights all search matches."""

    def highlightSearch(self, pattern):
        """Highlight all search occurences.

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

    def insertFromMimeData(self, source):
        """Insert supported formats in a specific way (i.e., Markdown-like)."""
        if source.hasUrls():
            for url in source.urls():
                path = url.path()
                if self.isWebImage(path):
                    fileName = os.path.basename(path)
                    diaryPath = self.parent().parent().parent().parent().diary.fname
                    relPath = os.path.relpath(
                        path, start=os.path.dirname(diaryPath))
                    imgMarkdown = '![{0}]({0} "{1}")\n'.format(
                        relPath, fileName)
                    self.insertPlainText(imgMarkdown)
                else:
                    super(MyQTextEdit, self).insertFromMimeData(source)
        else:
            super(MyQTextEdit, self).insertFromMimeData(source)

    @staticmethod
    def isWebImage(path):
        """Check if path leads to an image that can by displayed by browser."""
        if path.lower().endswith(('.gif', '.png', '.jpg', '.jpeg')):
            return True

        return False


class MyWebEnginePage(QWebEnginePage):
    """Modified QWebEnginePage that opens external links in the default system browser."""

    def __init__(self, parent=None):
        """Initialize the parent class."""
        super().__init__(parent)
        self.diaryPath = ""

    def acceptNavigationRequest(self, qurl, navtype, mainframe):
        """Open external links in the system browser, other links in this one.

        For some reason all links that don't have 'http://' or similar
        prepended, have 'file://' and the diary dir automatically prepended.
        I believe the reason is the following line in
        displayHTMLRenderedMarkdown():

        self.web.setHtml(html, baseUrl=QtCore.QUrl.fromLocalFile(mainPath))

        We need this line in order to show images and stylesheets, which are
        resolved relative to the baseUrl. So here we fix the link and open it
        in the system browser.
        """
        # print("Navigation Request intercepted:", qurl)
        if qurl.isLocalFile():  # delegate link to default browser
            diaryDirPath = os.path.dirname(self.diaryPath)
            url = qurl.toString().replace('file://', 'http://').replace(diaryDirPath + '/', '')
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
            return False
        else:
            # When setting QWebEngineView's content manually, the URL starts with 'data:text/html;'
            if qurl.toString().startswith("data"):
                # open in QWebEngineView
                return True
            else:
                # delegate link to default browser
                QtGui.QDesktopServices.openUrl(qurl)
                return False


class DiaryApp(QtWidgets.QMainWindow):  # pylint: disable=too-many-public-methods,too-many-instance-attributes
    """Diary application class inheriting from QMainWindow."""

    def __init__(self, parent=None):
        """Initialize member variables and GUI."""
        self.maxRecentItems = 10

        self.markdownAction = None
        self.newNoteAction = None
        self.saveNoteAction = None
        self.deleteNoteAction = None
        self.exportToHTMLAction = None
        self.exportToPDFAction = None
        self.newDiaryAction = None
        self.openDiaryAction = None
        self.searchLineAction = None
        self.recentDiariesActions = None
        self.clearRecentDiariesAction = None
        self.quitAction = None

        self.searchLine = None
        self.toolbar = None
        self.fileMenu = None
        self.noteMenu = None
        self.noteDate = None
        self.noteId = None
        self.recentDiaries = None
        self.recentNotes = None
        self.diary = None

        QtWidgets.QMainWindow.__init__(self, parent)

        renderer = markdown_math.HighlightRenderer()
        self.toMarkdown = markdown_math.MarkdownWithMath(renderer=renderer)

        self.tempFiles = []

        self.initUI()

        self.settings = QtCore.QSettings(
            "markdown-diary", application="settings")
        self.loadSettings()

        if self.recentDiaries and os.path.isfile(self.recentDiaries[0]):
            self.loadDiary(self.recentDiaries[0])
        else:
            self.text.setDisabled(True)
            self.saveNoteAction.setDisabled(True)
            self.newNoteAction.setDisabled(True)
            self.deleteNoteAction.setDisabled(True)
            self.exportToHTMLAction.setDisabled(True)
            self.exportToPDFAction.setDisabled(True)
            self.markdownAction.setDisabled(True)
            self.searchLineAction.setDisabled(True)

    def closeEvent(self, event):
        """Check if there are unsaved changes and display dialog if there are.

        This redefines the basic close event to give the user a chance to save
        his work. It also saves the current settings.

        Args:
            event (QEvent):
        """
        if self.text.document().isModified():
            reply = self.promptToSaveOrDiscard()

            if reply == QtWidgets.QMessageBox.Cancel:
                event.ignore()
                return

            elif reply == QtWidgets.QMessageBox.Save:
                self.saveNote()

        self.writeSettings()

    def initUI(self):
        """Initialize the UI - create widgets, set their pars, etc."""
        self.window = QtWidgets.QWidget(self)
        self.splitter = QtWidgets.QSplitter()
        self.initToolbar()
        self.initMenu()

        self.text = MyQTextEdit(self)
        self.text.setAcceptRichText(False)
        self.text.setFont(QtGui.QFont(
            QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)))
        self.text.textChanged.connect(self.setTitle)

        self.web = QWebEngineView(self)
        self.web.settings().setAttribute(QWebEngineSettings.FocusOnNavigationEnabled, False)
        self.page = MyWebEnginePage()
        self.web.setPage(self.page)

        self.highlighter = MarkdownHighlighter(self.text)

        self.setCentralWidget(self.window)

        self.setWindowTitle("Markdown Diary")

        self.stack = QtWidgets.QStackedWidget()
        self.stack.addWidget(self.text)
        self.stack.addWidget(self.web)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setUniformRowHeights(True)
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Id", "Date", "Title"])
        self.tree.setColumnHidden(0, True)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(1, QtCore.Qt.DescendingOrder)
        self.tree.itemSelectionChanged.connect(self.itemSelectionChanged)
        self.tree.itemChanged.connect(self.itemChanged)
        self.tree.itemDoubleClicked.connect(self.itemDoubleClicked)
        # Disable editing for the 'title' column
        self.tree.setItemDelegateForColumn(2, DummyItemDelegate())

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

        self.newDiaryAction = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("folder-new"), "New diary", self)
        self.newDiaryAction.setStatusTip("New diary")
        self.newDiaryAction.triggered.connect(self.newDiary)

        self.openDiaryAction = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("document-open"), "Open diary", self)
        self.openDiaryAction.setShortcut("Ctrl+O")
        self.openDiaryAction.setStatusTip("Open diary")
        self.openDiaryAction.triggered.connect(self.openDiary)

        self.clearRecentDiariesAction = QtWidgets.QAction("Clear list", self)
        self.clearRecentDiariesAction.setStatusTip("Clear list")
        self.clearRecentDiariesAction.triggered.connect(
            lambda: self.clearRecentDiaries())  # pylint: disable=unnecessary-lambda

        self.quitAction = QtWidgets.QAction("Quit", self)
        self.quitAction.setStatusTip("Quit the application")
        self.quitAction.setMenuRole(QtWidgets.QAction.QuitRole)
        self.quitAction.setShortcut(QtGui.QKeySequence.Quit)
        self.quitAction.triggered.connect(
            lambda: self.close()) # pylint: disable=unnecessary-lambda

        self.deleteNoteAction = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("remove"), "Delete Note", self)
        self.deleteNoteAction.setShortcut("Del")
        self.deleteNoteAction.setStatusTip("Delete note")
        self.deleteNoteAction.triggered.connect(
            lambda: self.deleteNote())  # pylint: disable=unnecessary-lambda

        self.exportToHTMLAction = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("document-export"), "Export to HTML", self)
        self.exportToHTMLAction.setStatusTip("Export to HTML")
        self.exportToHTMLAction.triggered.connect(self.exportToHTML)

        self.exportToPDFAction = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("document-export"), "Export to PDF", self)
        self.exportToPDFAction.setStatusTip("Export to PDF")
        self.exportToPDFAction.triggered.connect(self.exportToPDF)

        self.searchLine = QtWidgets.QLineEdit(self)
        self.searchLine.setFixedWidth(200)
        self.searchLine.setPlaceholderText("Search...")
        self.searchLine.setClearButtonEnabled(True)

        self.searchLineAction = QtWidgets.QWidgetAction(self)
        self.searchLineAction.setDefaultWidget(self.searchLine)
        self.searchLineAction.setShortcut(QtGui.QKeySequence.Find)
        self.searchLineAction.triggered.connect(self.selectSearch)
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
        self.fileMenu.addAction(self.newDiaryAction)
        self.fileMenu.addAction(self.openDiaryAction)
        self.fileMenu.addSeparator()

        self.recentDiariesActions = []
        for _ in range(self.maxRecentItems):
            action = QtWidgets.QAction(self)
            action.setVisible(False)
            self.recentDiariesActions.append(action)
            self.fileMenu.addAction(action)

        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.clearRecentDiariesAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.quitAction)

        self.noteMenu = self.menuBar().addMenu("&Note")
        self.noteMenu.addAction(self.newNoteAction)
        self.noteMenu.addAction(self.saveNoteAction)
        self.noteMenu.addAction(self.deleteNoteAction)
        self.noteMenu.addSeparator()
        self.noteMenu.addAction(self.exportToHTMLAction)
        self.noteMenu.addAction(self.exportToPDFAction)

    def loadTree(self, metadata):
        """Load notes tree from diary metadata.

        Load notes tree from diary metadata and populate the QTreeWidget
        with it.
        """
        entries = []

        for note in metadata:
            entries.append(QtWidgets.QTreeWidgetItem(
                [note["note_id"], note["date"], note["title"]]))

        for entry in entries:
            entry.setFlags(entry.flags() | QtCore.Qt.ItemIsEditable)

        self.tree.clear()
        self.tree.addTopLevelItems(entries)

    def loadSettings(self):
        """Load settings via self.settings QSettings object."""
        self.recentDiaries = self.settings.value("diary/recent_diaries", [])
        self.updateRecentDiaries()
        self.recentNotes = self.settings.value("diary/recent_notes", [])

        self.resize(self.settings.value(
            "window/size", QtCore.QSize(600, 400)))

        self.move(self.settings.value(
            "window/position", QtCore.QPoint(200, 200)))

        self.splitter.setSizes(
            [int(val) for val in self.settings.value(
                "window/splitter", [70, 30])])

        toolBarArea = int(self.settings.value("window/toolbar_area",
                                              QtCore.Qt.TopToolBarArea))
        # addToolBar() actually just moves the specified toolbar if it
        # was already added, which is what we want
        self.addToolBar(QtCore.Qt.ToolBarArea(toolBarArea), self.toolbar)

        self.mathjax = self.settings.value(
            "mathjax/location",
            "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js")

    def writeSettings(self):
        """Save settings via self.settings QSettings object."""
        self.settings.setValue("window/size", self.size())
        self.settings.setValue("window/position", self.pos())
        self.settings.setValue("window/splitter", self.splitter.sizes())
        self.settings.setValue("window/toolbar_area", self.toolBarArea(
            self.toolbar))

        if self.recentDiaries:
            self.settings.setValue("diary/recent_diaries", self.recentDiaries)

        if self.recentNotes:
            self.settings.setValue("diary/recent_notes", self.recentNotes)

    def markdownToggle(self):
        """Switch between displaying Markdown source and rendered HTML."""
        if self.stack.currentIndex() == 1:
            self.stack.setCurrentIndex(0)
        else:
            self.stack.setCurrentIndex(1)
            self.displayHTMLRenderedMarkdown(self.text.toPlainText())
            if self.searchLine.text() != "":
                # Search in the WebView
                self.web.findText(self.searchLine.text())

    def createHTML(self, markdownText):
        """Create full, valid HTML from Markdown source.

        Args:
            markdownText (str): Markdown source to convert to HTML.

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

        if mathInline.search(markdownText) or mathBlock.search(markdownText):

            html += style.mathjax
            mathjaxScript = (
                '<script type="text/javascript" src="{}?config='
                'TeX-AMS-MML_HTMLorMML"></script>\n').format(self.mathjax)
            html += mathjaxScript

        html += self.toMarkdown(markdownText)  # pylint: disable=not-callable
        html += style.footer
        return html

    def displayHTMLRenderedMarkdown(self, markdownText):
        """Display HTML rendered Markdown."""
        html = self.createHTML(markdownText)

        # QWebEngineView resolves relative links (like images and stylesheets)
        # with respect to the baseUrl
        mainPath = self.diary.fname
        self.web.setHtml(html, baseUrl=QtCore.QUrl.fromLocalFile(mainPath))

        if self.searchLine.text() != "":
            # Search in the WebView
            self.web.findText(self.searchLine.text())

    def newNote(self):
        """Create an empty note and add it to the QTreeWidget.

        The note is not added to the diary until it is saved.
        """
        self.noteDate = datetime.date.today().isoformat()
        self.noteId = str(uuid.uuid1())

        self.text.clear()
        self.stack.setCurrentIndex(0)
        self.text.setFocus()
        self.text.setText("# <Untitled note>")
        self.saveNote()
        self.loadTree(self.diary.data)
        self.selectItemWithoutReload(self.noteId)

        # Select the '<Untitled note>' part of the new note for convenient
        # renaming
        cursor = self.text.textCursor()
        cursor.setPosition(2)
        cursor.setPosition(17, QtGui.QTextCursor.KeepAnchor)
        self.text.setTextCursor(cursor)

    def saveNote(self):
        """Save the displayed note.

        Either updates an existing note or adds a new one to a diary.
        """
        if self.text.toPlainText().lstrip() == "":
            QtWidgets.QMessageBox.information(
                self, 'Message', "You can't save an empty note!")
            return

        # Notes should begin with a title, so strip any whitespace,
        # including newlines from the beggining
        self.diary.saveNote(
            self.text.toPlainText().lstrip(), self.noteId, self.noteDate)
        self.text.document().setModified(False)
        self.setTitle()

        # Change the title in the tree, without reloading the tree (that would
        # cause the filtered results when searching to be lost)
        self.tree.blockSignals(True)

        # When there are no items in the tree (new diary) must add the item
        # first and select it
        if self.tree.topLevelItemCount() == 0:
            newItem = QtWidgets.QTreeWidgetItem(
                [self.noteId, self.noteDate, ""])
            self.tree.addTopLevelItem(newItem)
            self.tree.setCurrentItem(newItem)

        self.tree.currentItem().setText(2, self.diary.getNoteMetadata(
            self.noteId)["title"])

        self.tree.blockSignals(False)

    def deleteNote(self, noteId=None):
        """Delete a specified note.

         If there are unsaved changes, prompt the user. Refresh note tree
         after deletion.

        Args:
            noteId (str, optional): UUID of the note to delete
        """
        if noteId is None:
            noteId = self.noteId
        noteTitle = self.diary.getNoteMetadata(self.noteId)["title"]

        deleteMsg = "Do you really want to delete the note '" + noteTitle + "'?"
        reply = QtWidgets.QMessageBox.question(
            self, 'Message', deleteMsg,
            QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.No:
            return

        nextNoteId = self.tree.itemBelow(self.tree.currentItem()).text(0)
        self.diary.deleteNote(noteId)
        self.text.document().setModified(False)
        self.loadTree(self.diary.data)
        self.tree.setCurrentItem(
            self.tree.findItems(nextNoteId, QtCore.Qt.MatchExactly)[0])

    def newDiary(self):
        """Display a file save dialog and create diary at specified path.

        Enable relevant toolbar items (new note, save note, etc.), in case
        no diary was open before and they were disabled.
        """
        if self.text.document().isModified():
            reply = self.promptToSaveOrDiscard()

            if reply == QtWidgets.QMessageBox.Cancel:
                return

            elif reply == QtWidgets.QMessageBox.Discard:
                self.text.document().setModified(False)

            elif reply == QtWidgets.QMessageBox.Save:
                self.saveNote()

        fname = QtWidgets.QFileDialog.getSaveFileName(
            caption="Create a New Diary",
            filter="Markdown Files (*.md);;All Files (*)")[0]

        if fname:
            with open(fname, 'w'):
                os.utime(fname)

            self.loadDiary(fname)
            self.newNote()

    def openDiary(self):
        """Display a file open dialog and load the selected diary.

        Enable relevant toolbar items (new note, save note, etc.), in case
        no diary was open before and they were disabled.
        """
        if self.text.document().isModified():
            reply = self.promptToSaveOrDiscard()

            if reply == QtWidgets.QMessageBox.Cancel:
                return

            elif reply == QtWidgets.QMessageBox.Discard:
                self.text.document().setModified(False)

            elif reply == QtWidgets.QMessageBox.Save:
                self.saveNote()

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
                self.exportToHTMLAction.setDisabled(False)
                self.exportToPDFAction.setDisabled(False)
                self.markdownAction.setDisabled(False)
                self.searchLineAction.setDisabled(False)
            else:
                print("ERROR:" + fname + "is not a valid diary file!")

    @staticmethod
    def isValidDiary(fname):
        """Check if a file path leads to a valid diary.

        Args:
            fname (str): Path to a diary file to be validated.

        Returns:
            bool: True for valid, False for invalid diary.

        """
        # TODO Implement checks
        return True

    def loadDiary(self, fname):
        """Load diary from file.

        Display last note from the diary if it exists.

        Args:
            fname (str): Path to a file containing a diary.
        """
        if self.text.document().isModified():
            reply = self.promptToSaveOrDiscard()

            if reply == QtWidgets.QMessageBox.Cancel:
                return

            elif reply == QtWidgets.QMessageBox.Discard:
                self.text.document().setModified(False)

            elif reply == QtWidgets.QMessageBox.Save:
                self.saveNote()

        self.updateRecentDiaries(fname)
        self.diary = diary.Diary(fname)

        # Save the diary path to QWebEnginePage, so we can fix external links,
        # which (for some reason) look like file://DIARY_PATH/EXTERNAL_LINK
        self.page.diaryPath = fname

        self.loadTree(self.diary.data)

        # Display empty editor if the diary has no notes (e.g., new diary)
        if not self.diary.data:
            self.text.clear()
            self.stack.setCurrentIndex(0)
            return

        # Check if we saved a recent noteId for this diary and open it if we
        # did, otherwise open the newest note
        lastNoteId = ""
        for recentNote in self.recentNotes:
            if recentNote in (metaDict["note_id"] for metaDict in self.diary.data):
                lastNoteId = recentNote
                break

        if lastNoteId == "":
            lastNoteId = self.diary.data[-1]["note_id"]

        self.tree.setCurrentItem(
            self.tree.findItems(lastNoteId, QtCore.Qt.MatchExactly)[0])
        self.stack.setCurrentIndex(1)

    def updateRecentDiaries(self, fname=""):
        """Update list of recently opened diaries.

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

            if len(self.recentDiaries) > self.maxRecentItems:
                del self.recentDiaries[self.maxRecentItems:]

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
                lambda dummy=False, recent=recent: self.loadDiary(recent))

    def clearRecentDiaries(self):
        """Clear the list of recent diaries."""
        self.recentDiaries = []
        self.updateRecentDiaries()

    def updateRecentNotes(self, noteId):
        """Update list of recently viewed notes.

        Adds/moves the specified noteId to the beggining of the list.

        Args:
            noteId (str): The most recent note to be added/moved to the top
                of the list.
        """
        if noteId in self.recentNotes:
            self.recentNotes.remove(noteId)

        self.recentNotes.insert(0, noteId)

        if len(self.recentNotes) > self.maxRecentItems:
            del self.recentNotes[self.maxRecentItems:]

    @staticmethod
    def promptToSaveOrDiscard():
        """Display a message box asking whether to save or discard changes.

        Returns:
            One of the three options:
                QtWidgets.QMessageBox.Save
                QtWidgets.QMessageBox.Discard
                QtWidgets.QMessageBox.Cancel

        """
        msgBox = QtWidgets.QMessageBox()
        msgBox.setWindowTitle("Save or Discard")
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText("Save changes before closing note?")
        msgBox.setStandardButtons(
            QtWidgets.QMessageBox.Save |
            QtWidgets.QMessageBox.Discard |
            QtWidgets.QMessageBox.Cancel)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Save)
        return msgBox.exec()

    def itemSelectionChanged(self):
        """Display a new selected note.

        Prompts the user if there is unsaved work. If there is an active
        search, reruns it on the new note.
        """
        if len(self.tree.selectedItems()) == 0:  # pylint: disable=len-as-condition
            return

        newNoteId = self.tree.selectedItems()[0].text(0)

        if self.text.document().isModified():
            # Keep the cursor on the note in question while the dialog is
            # displayed
            self.tree.blockSignals(True)
            self.tree.setCurrentItem(self.tree.findItems(
                self.noteId, QtCore.Qt.MatchExactly)[0])
            self.tree.blockSignals(False)

            reply = self.promptToSaveOrDiscard()

            # We just save note/flag it as unmodified and recursively call
            # this method again
            if reply == QtWidgets.QMessageBox.Save:
                self.saveNote()
                self.tree.setCurrentItem(self.tree.findItems(
                    newNoteId, QtCore.Qt.MatchExactly)[0])

            elif reply == QtWidgets.QMessageBox.Discard:
                self.text.document().setModified(False)
                self.tree.setCurrentItem(self.tree.findItems(
                    newNoteId, QtCore.Qt.MatchExactly)[0])

            return

        self.displayNote(newNoteId)

        if self.searchLine.text() != "":
            # Search in the editor
            self.text.highlightSearch(self.searchLine.text())

            # Search in the WebView
            self.web.findText(self.searchLine.text())

    def displayNote(self, noteId):
        """Display a specified note."""
        self.text.setText(self.diary.getNote(noteId))
        self.setTitle()
        self.noteId = noteId
        self.updateRecentNotes(noteId)
        self.noteDate = self.diary.getNoteMetadata(noteId)["date"]
        self.displayHTMLRenderedMarkdown(self.text.toPlainText())

    def selectSearch(self):
        """Focus the search widget and select its contents."""
        self.searchLine.setFocus()
        self.searchLine.selectAll()

    def search(self):
        """Search and highlight text in all notes.

        Highlights text occurrences in the editor and web view. Searches all
        notes for the text and removes non-matching from the note tree. The
        text to search for is taken from the searchLine widget.
        """
        if self.searchLine.text() == "":
            self.loadTree(self.diary.data)
            self.selectItemWithoutReload(self.noteId)
            self.text.highlightSearch("")
            self.web.findText("")
            return

        # Search in the editor
        self.text.highlightSearch(self.searchLine.text())

        # Search in the WebView
        self.web.findText(self.searchLine.text())

        # Search for matching notes
        entries = self.diary.searchNotes(self.searchLine.text())
        self.loadTree(entries)

        if entries:
            # Select the matching item in the tree. Either the current one, if it
            # is among the matching items, or the last matching one.
            if self.noteId in (entry["note_id"] for entry in entries):
                self.selectItemWithoutReload(self.noteId)
            else:
                self.tree.setCurrentItem(self.tree.findItems(
                    entries[-1]["note_id"], QtCore.Qt.MatchExactly)[0])
                self.searchLine.setFocus()

    def searchNext(self):
        """Move main highlight (and scroll) to the next search match."""
        self.web.findText(self.searchLine.text())

        if self.text.extraSelections():
            if not self.text.find(self.searchLine.text()):
                self.text.moveCursor(QtGui.QTextCursor.Start)
                self.text.find(self.searchLine.text())

    def setTitle(self):
        """Set the application title; add '*' if editor in dirty state."""
        if self.text.document().isModified():
            self.setWindowTitle("*Markdown Diary")
        else:
            self.setWindowTitle("Markdown Diary")

        if hasattr(self, 'diary') and self.diary is not None:
            self.setWindowTitle(self.windowTitle() + " - " +
                                os.path.basename(self.diary.fname))

    def itemDoubleClicked(self, _item, column):
        """Decide action based on which column the user clicked.

        If the user clicked the title, toggle Markdown.
        """
        if column == 2:
            self.markdownToggle()

    def itemChanged(self, item, _column):
        """Update note when some of its metadata are changed in the TreeWidget.

        Currently only the date can be changed. The date is first validated,
        otherwise no action is taken.
        """
        noteId = item.text(0)
        noteDate = item.text(1)
        if self.diary.isValidDate(noteDate):
            self.diary.changeNoteDate(noteId, noteDate)
            self.noteDate = noteDate
            self.loadTree(self.diary.data)
            self.selectItemWithoutReload(noteId)
        else:
            print("Invalid date")
            self.loadTree(self.diary.data)
            self.selectItemWithoutReload(noteId)

    def selectItemWithoutReload(self, noteId):
        """Select an item in the QtTreeWidget without reloading the note."""
        self.tree.blockSignals(True)
        self.tree.setCurrentItem(
            self.tree.findItems(noteId, QtCore.Qt.MatchExactly)[0])
        self.tree.blockSignals(False)

    def exportToHTML(self):
        """Export the displayed note to HTML."""
        markdownText = self.diary.getNote(self.noteId)
        html = self.createHTML(markdownText)

        # To be able to load the CSS during normal operation correctly, we have
        # to use an absolute path. This is not desirable when exporting to
        # HTML, so we change it to a relative path.
        newhtml = ""
        stillInHead = True
        for line in html.splitlines():
            if stillInHead:
                if "github-markdown.css" in line:
                    newhtml += '<link rel="stylesheet" href="css/github-markdown.css">\n'
                elif "github-pygments.css" in line:
                    newhtml += '<link rel="stylesheet" href="css/github-pygments.css">\n'
                else:
                    newhtml += line + '\n'
                    if "</head>" in line:
                        stillInHead = False
            else:
                newhtml += line + '\n'

        fname = QtWidgets.QFileDialog.getSaveFileName(
            caption="Export Note to HTML",
            filter="HTML Files (*.html);;All Files (*)")[0]

        if fname:
            with open(fname, 'w') as f:
                os.utime(fname)
                f.write(newhtml)

    def exportToPDF(self):
        """Export the displayed note to PDF."""
        fname = QtWidgets.QFileDialog.getSaveFileName(
            caption="Export Note to PDF",
            filter="PDF Files (*.pdf);;All Files (*)")[0]

        if fname:
            # Make sure we export the current version of the text
            if self.stack.currentIndex() == 0:
                self.displayHTMLRenderedMarkdown(self.text.toPlainText())

            pageLayout = QtGui.QPageLayout(QtGui.QPageSize(
                QtGui.QPageSize.A4), QtGui.QPageLayout.Landscape, QtCore.QMarginsF(0, 0, 0, 0))
            self.web.page().printToPdf(fname, pageLayout)

    def __del__(self):
        """Clean up temporary files on exit."""
        # Delete temporary files
        # We put it into __del__ deliberately, so if one wants, one can avoid
        # the temporary files being deleted by killing the process. This might
        # be useful, e.g., in case of accidental over-write.
        for f in self.tempFiles:
            os.unlink(f.name)


def main():
    """Run the whole QApplication."""
    app = QtWidgets.QApplication(sys.argv)
    # pyqtRemoveInputHook() # enable for debugging

    diaryApp = DiaryApp()
    diaryApp.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
