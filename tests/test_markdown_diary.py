# To be run using `python3 -m unittest` from the root dir (`../`)

import sys
import unittest
from shutil import copyfile
import os

from PyQt5 import QtCore
from PyQt5 import QtWidgets

import markdown_diary
import diary as d

app = QtWidgets.QApplication(sys.argv)

tempDiaryFileName = 'tests/diary_temp.md'
diaryFileName = 'tests/diary.md'
noteFileName = 'tests/note.md'
HTMLNoteFileName = 'tests/note.html'
rawHTMLNoteFileName = 'tests/note_raw.html'


class DiaryTest(unittest.TestCase):

    def setUp(self):

        # create a temporary diary for each test
        copyfile(diaryFileName, tempDiaryFileName)

        self.diary = d.Diary(tempDiaryFileName)

    def tearDown(self):

        # Delete the temporary diary
        os.remove(tempDiaryFileName)

    def testSavingOfDiary(self):

        self.diary.updateDiaryOnDisk('TEST')

        with open(tempDiaryFileName) as f:
            diaryData = f.read()

        self.assertEqual(diaryData, 'TEST')

    def testSaveNote(self):

        testNote = "Save test"
        testNote2 = "Save test 2"
        testNoteId = "123"
        testNoteDate = "2015-03-15"
        testNoteDate2 = "2015-03-16"

        self.diary.saveNote(testNote, testNoteId, testNoteDate)
        note = self.diary.getNote(testNoteId)
        date = self.diary.getNoteMetadata(testNoteId)["date"]

        self.assertEqual(note, testNote)
        self.assertEqual(date, testNoteDate)

        # Test saving an existing note (updating)
        self.diary.saveNote(testNote2, testNoteId, testNoteDate2)
        note = self.diary.getNote(testNoteId)
        date = self.diary.getNoteMetadata(testNoteId)["date"]

        self.assertEqual(note, testNote2)
        self.assertEqual(date, testNoteDate2)

    def testCreateNoteHeader(self):

        testHeader = ("\n"
                      "<!---\n"
                      "markdown-diary note metadata\n"
                      "note_id = 123\n"
                      "--->\n"
                      "2015-03-15\n"
                      "\n")

        header = self.diary.createNoteHeader("123", "2015-03-15")
        self.assertEqual(header, testHeader)

    def testUpdatingOfNote(self):

        self.diary.updateNote(
            'TEST', 'a3ea0c44-ed00-11e6-a9cf-c48508000000', '1999-01-01')
        note = self.diary.getNote('a3ea0c44-ed00-11e6-a9cf-c48508000000')
        noteDate = self.diary.getNoteMetadata(
            'a3ea0c44-ed00-11e6-a9cf-c48508000000')['date']

        self.assertEqual(note, 'TEST\n')
        self.assertEqual(noteDate, '1999-01-01')

    def testDeletingOfNote(self):

        self.diary.deleteNote('a3ea0c44-ed00-11e6-a9cf-c4850828558c')

        with open(tempDiaryFileName) as f:
            diaryData = f.read()

        metadata = self.diary.getMetadata(diaryData)

        refMetadata = [{'version': '3',
                        'title': 'Short note',
                        'note_id': 'a3ea0c44-ed00-11e6-a9cf-c48508000000',
                        'date': '2015-05-05'},
                       {'version': '3',
                        'title': 'Short note 2',
                        'note_id': 'a3ea0c44-ed00-11e6-a9cf-c48508000001',
                        'date': '2015-05-09'}]

        self.assertListEqual(metadata, refMetadata)

    def testGettingOfMetadataFromDiary(self):

        with open(diaryFileName) as f:
            diaryData = f.read()

        metadata = self.diary.getMetadata(diaryData)

        refMetadata = [{'version': '3',
                        'title': 'Short note',
                        'note_id': 'a3ea0c44-ed00-11e6-a9cf-c48508000000',
                        'date': '2015-05-05'},
                       {'version': '3',
                        'title': 'Updated Markdown Test',
                        'note_id': 'a3ea0c44-ed00-11e6-a9cf-c4850828558c',
                        'date': '2015-05-06'},
                       {'version': '3',
                        'title': 'Short note 2',
                        'note_id': 'a3ea0c44-ed00-11e6-a9cf-c48508000001',
                        'date': '2015-05-09'}]

        self.assertListEqual(metadata, refMetadata)

    def testGettingOfNote(self):

        with open(diaryFileName) as f:
            diaryData = f.read()

        note = self.diary.getNote('a3ea0c44-ed00-11e6-a9cf-c48508000000')

        refNote = ("# Short note"
                   "\n\n"
                   "Test"
                   "\n\n")

        self.assertMultiLineEqual(note, refNote)

    def testGettingNonexistentNote(self):

        note = self.diary.getNote('nonexistentid')
        self.assertIsNone(note)

    def testGettingNoteMetadata(self):

        noteMetadata = self.diary.getNoteMetadata(
            'a3ea0c44-ed00-11e6-a9cf-c48508000000')

        refMetadata = {'version': '3',
                       'title': 'Short note',
                       'note_id': 'a3ea0c44-ed00-11e6-a9cf-c48508000000',
                       'date': '2015-05-05'}

        self.assertEqual(noteMetadata, refMetadata)

    def testGettingNonexistentMetadata(self):

        metadata = self.diary.getNoteMetadata('nonexistentid')
        self.assertIsNone(metadata)

    def testSavingOfExternallyChangedDiary(self):

        with open(tempDiaryFileName, 'a') as f:
            f.write("An externally added line")

        self.diary.updateDiaryOnDisk("A whole diary")

        self.assertNotEqual(self.diary.data, "A whole diary")

    def testChangeNoteDate(self):

        refNote = self.diary.getNote('a3ea0c44-ed00-11e6-a9cf-c48508000000')
        self.diary.changeNoteDate(
            'a3ea0c44-ed00-11e6-a9cf-c48508000000', '1234-05-05')
        self.diary.changeNoteDate(
            'a3ea0c44-ed00-11e6-a9cf-c48508000000', '1234-05-05')

        noteMetadata = self.diary.getNoteMetadata(
            'a3ea0c44-ed00-11e6-a9cf-c48508000000')
        note = self.diary.getNote('a3ea0c44-ed00-11e6-a9cf-c48508000000')

        refMetadata = {'version': '3',
                       'title': 'Short note',
                       'note_id': 'a3ea0c44-ed00-11e6-a9cf-c48508000000',
                       'date': '1234-05-05'}

        self.assertEqual(noteMetadata, refMetadata)
        self.assertMultiLineEqual(note, refNote)

    def testIsValidDate(self):

        self.assertFalse(self.diary.isValidDate('bla-bla'))
        self.assertFalse(self.diary.isValidDate('0'))
        self.assertFalse(self.diary.isValidDate('2015-3-14'))
        self.assertTrue(self.diary.isValidDate('2015-03-14'))

    def testSearchNotes(self):

        refIds = ['a3ea0c44-ed00-11e6-a9cf-c4850828558c',
                  'a3ea0c44-ed00-11e6-a9cf-c48508000001']
        ids = [metadatum['note_id'] for metadatum in self.diary.searchNotes("2")]
        self.assertEqual(ids, refIds)


class DiaryAppTest(unittest.TestCase):

    def setUp(self):

        # create a temporary diary to be used in tests
        copyfile(diaryFileName, tempDiaryFileName)

        self.diary_app = markdown_diary.DiaryApp()
        self.diary_app.loadDiary(os.path.abspath(tempDiaryFileName))

    def tearDown(self):

        # Delete the temporary diary
        os.remove(tempDiaryFileName)

    def testLoadTree(self):

        pass

    def testLoadSettings(self):

        pass

    def testCreatingHTMLFromMarkdown(self):

        self.maxDiff = None
        with open(noteFileName) as f:
            note = f.read()

        with open(rawHTMLNoteFileName) as f:
            refNoteHtml = f.read()

        noteHtml = self.diary_app.createHTML(note)

        # CSS path is machine-dependent so we change it
        newNoteHtml = ""
        for line in noteHtml.splitlines():
            if 'github-markdown.css' in line:
                line = '<link rel="stylesheet" href="css/github-markdown.css">'
            if 'github-pygments.css' in line:
                line = '<link rel="stylesheet" href="css/github-pygments.css">'
            newNoteHtml += line
            newNoteHtml += '\n'
        noteHtml = newNoteHtml

        self.assertMultiLineEqual(noteHtml, refNoteHtml)

    def testDisplayingOfHTMLRenderedMarkdown(self):

        self.maxDiff = None

        self.diary_app.diary = d.Diary(tempDiaryFileName)

        with open(noteFileName) as f:
            note = f.read()

        with open(HTMLNoteFileName) as f:
            refNoteHtml = f.read().rstrip()

        self.diary_app.displayHTMLRenderedMarkdown(note)

        self.diary_app.web.loadFinished.connect(self._loadFinished)
        self.noteHtml = None
        app.exec_()

        # CSS path is machine-dependent so we change it
        newNoteHtml = ""
        for line in self.noteHtml.splitlines():
            if 'github-markdown.css' in line:
                line = '<link rel="stylesheet" href="css/github-markdown.css">'
            if 'github-pygments.css' in line:
                line = '<link rel="stylesheet" href="css/github-pygments.css">'
            newNoteHtml += line
            newNoteHtml += '\n'
        # Remove the added extra newline
        self.noteHtml = newNoteHtml[:-1]

        self.assertMultiLineEqual(self.noteHtml, refNoteHtml)

    def _loadFinished(self, result):

        self.diary_app.web.page().toHtml(self._saveHtml)

    def _saveHtml(self, html):

        self.noteHtml = html
        app.quit()

    def testOpenDiary(self):

        pass

    def testUpdateRecentNotes(self):

        self.diary_app.recentNotes = ['a1', 'b2', 'c3']
        self.diary_app.updateRecentNotes('b2')

        self.assertListEqual(self.diary_app.recentNotes, ['b2', 'a1', 'c3'])

        self.diary_app.updateRecentNotes('d4')
        self.assertListEqual(self.diary_app.recentNotes,
                             ['d4', 'b2', 'a1', 'c3'])

    def testUpdateRecentDiaries(self):

        self.diary_app.recentDiaries = ['a1', 'b2', 'c3']
        self.diary_app.updateRecentDiaries('b2')

        self.assertListEqual(self.diary_app.recentDiaries, ['b2', 'a1', 'c3'])

        self.diary_app.updateRecentDiaries('d4')
        self.assertListEqual(self.diary_app.recentDiaries,
                             ['d4', 'b2', 'a1', 'c3'])

    def testMimePaste(self):

        # Clear the current text so it's easier to test pasting
        self.diary_app.text.setText("")
        url = QtCore.QUrl('file://' + os.path.abspath('tests/files/test.png'))
        mime = QtCore.QMimeData()
        mime.setUrls([url])
        self.diary_app.text.insertFromMimeData(mime)
        self.assertEqual(self.diary_app.text.toPlainText(),
                         '![files/test.png](files/test.png "test.png")\n')

    def testMimePasteExternalPath(self):

        # Clear the current text so it's easier to test pasting
        self.diary_app.text.setText("")
        url = QtCore.QUrl('file://' + os.path.abspath('files/test.png'))
        mime = QtCore.QMimeData()
        mime.setUrls([url])
        self.diary_app.text.insertFromMimeData(mime)
        self.assertEqual(self.diary_app.text.toPlainText(),
                         '![../files/test.png](../files/test.png "test.png")\n')

    def testCreatingANewDiary(self):

        with open(tempDiaryFileName, 'w'):
            os.utime(tempDiaryFileName)

        self.diary_app.loadDiary(tempDiaryFileName)
        self.diary_app.newNote()
        # Doesn't need an assert as the error for which this tests caused an
        # AttributeError


if __name__ == '__main__':
    unittest.main()
