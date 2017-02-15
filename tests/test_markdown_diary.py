# To be run using `python3 -m unittest discover` from the root dir (`../`)

import sys
import unittest

from PyQt5 import QtWidgets

import markdown_diary
import diary as d

app = QtWidgets.QApplication(sys.argv)

diaryFileName = 'tests/diary.md'
noteFileName = 'tests/note.md'
htmlNoteFileName = 'tests/note.html'


class DiaryTest(unittest.TestCase):

    def test__init__(self):

        d.Diary(diaryFileName)

    def testSaveDiary(self):

        pass

    def testSaveNote(self):

        pass

    def testCreateNoteHeader(self):

        pass

    def testUpdateNote(self):

        pass

    def testDeleteNote(self):

        pass

    def testGetMetadata(self):

        diary = d.Diary(diaryFileName)
        with open(diaryFileName) as f:
            diaryData = f.read()

        metadata = diary.getMetadata(diaryData)

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

    def testGetNote(self):

        diary = d.Diary(diaryFileName)
        with open(diaryFileName) as f:
            diaryData = f.read()

        note = diary.getNote(diaryData, 'a3ea0c44-ed00-11e6-a9cf-c48508000000')

        refNote = ("# Short note"
                   "\n\n"
                   "Test"
                   "\n\n")

        self.assertMultiLineEqual(note, refNote)

    def testGetNoteMetadata(self):

        pass


class DiaryAppTest(unittest.TestCase):

    def testLoadTree(self):

        pass

    def testLoadSettings(self):

        pass

    def testMarkdown(self):

        self.maxDiff = None
        app = markdown_diary.DiaryApp()
        with open(noteFileName) as f:
            note = f.read()

        with open(htmlNoteFileName) as f:
            refNoteHtml = f.read().rstrip()

        app.text.setText(note)
        app.markdown()
        noteHtml = app.web.page().mainFrame().toHtml()

        self.assertMultiLineEqual(noteHtml, refNoteHtml)

    def testOpenDiary(self):

        pass


if __name__ == '__main__':
    unittest.main()
