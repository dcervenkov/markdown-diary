# To be run using `python3 -m unittest` from the root dir (`../`)

import sys
import unittest
from shutil import copyfile
import os

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

        # create a temporary diary to be used in tests
        copyfile(diaryFileName, tempDiaryFileName)

        self.diary = d.Diary(tempDiaryFileName)

    def tearDown(self):

        # Delete the temporary diary
        os.remove(tempDiaryFileName)

    def test__init__(self):

        pass

    def test_saving_of_a_diary(self):

        self.diary.saveDiary('TEST')

        with open(tempDiaryFileName) as f:
            diaryData = f.read()

        self.assertEqual(diaryData, 'TEST')

    def testSaveNote(self):

        pass

    def testCreateNoteHeader(self):

        pass

    def test_updating_of_a_note(self):

        self.diary.updateNote('TEST', 'a3ea0c44-ed00-11e6-a9cf-c48508000000', '1999-01-01')
        note = self.diary.getNote(self.diary.data, 'a3ea0c44-ed00-11e6-a9cf-c48508000000')
        noteDate = self.diary.getNoteMetadata(
            self.diary.metadata, 'a3ea0c44-ed00-11e6-a9cf-c48508000000')['date']

        self.assertEqual(note, 'TEST\n')
        self.assertEqual(noteDate, '1999-01-01')

    def test_deleting_of_a_note(self):

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

    def test_getting_of_metadata_from_diary(self):

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

    def test_getting_of_a_note(self):

        with open(diaryFileName) as f:
            diaryData = f.read()

        note = self.diary.getNote(diaryData, 'a3ea0c44-ed00-11e6-a9cf-c48508000000')

        refNote = ("# Short note"
                   "\n\n"
                   "Test"
                   "\n\n")

        self.assertMultiLineEqual(note, refNote)

    def test_getting_note_metadata(self):

        noteMetadata = self.diary.getNoteMetadata(
            self.diary.metadata, 'a3ea0c44-ed00-11e6-a9cf-c48508000000')

        refMetadata = {'version': '3',
                        'title': 'Short note',
                        'note_id': 'a3ea0c44-ed00-11e6-a9cf-c48508000000',
                        'date': '2015-05-05'}

        self.assertEqual(noteMetadata, refMetadata)


class DiaryAppTest(unittest.TestCase):

    def setUp(self):

        self.diary_app = markdown_diary.DiaryApp()

    def testLoadTree(self):

        pass

    def testLoadSettings(self):

        pass

    def test_creating_HTML_from_Markdown(self):

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

    def test_displaying_of_HTML_rendered_Markdown(self):

        self.maxDiff = None

        copyfile(diaryFileName, tempDiaryFileName)
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
        self.assertListEqual(self.diary_app.recentNotes, ['d4', 'b2', 'a1', 'c3'])

    def testUpdateRecentDiaries(self):

        self.diary_app.recentDiaries = ['a1', 'b2', 'c3']
        self.diary_app.updateRecentDiaries('b2')

        self.assertListEqual(self.diary_app.recentDiaries, ['b2', 'a1', 'c3'])

        self.diary_app.updateRecentDiaries('d4')
        self.assertListEqual(self.diary_app.recentDiaries, ['d4', 'b2', 'a1', 'c3'])


if __name__ == '__main__':
    unittest.main()
