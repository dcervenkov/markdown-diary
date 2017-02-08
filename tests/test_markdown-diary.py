import sys
import unittest

from PyQt5 import QtWidgets

import markdown_diary

app = QtWidgets.QApplication(sys.argv)


class MarkdownDiaryTest(unittest.TestCase):

    def setUp(self):

        pass

    def testGetNoteIds(self):

        diary = markdown_diary.DiaryApp()
        with open('tests/diary.md') as f:
            diaryData = f.read()

        ids = diary.getNoteIds(diaryData)

        refIds = ['a3ea0c44-ed00-11e6-a9cf-c48508000000',
                  'a3ea0c44-ed00-11e6-a9cf-c4850828558c',
                  'a3ea0c44-ed00-11e6-a9cf-c48508000001']

        self.assertListEqual(ids, refIds)

    def testGetNote(self):

        diary = markdown_diary.DiaryApp()
        with open('tests/diary.md') as f:
            diaryData = f.read()

        note = diary.getNote(diaryData, 'a3ea0c44-ed00-11e6-a9cf-c48508000000')

        refNote = ("# Short note"
                   "\n\n"
                   "Test"
                   "\n\n")

        self.assertEqual(note, refNote)

    def testOpenDiary(self):

        pass

    def testNewNote(self):

        pass

    def testSaveNote(self):

        pass

    def testInitTree(self):

        pass

    def testMarkdown(self):

        self.maxDiff = None
        diary = markdown_diary.DiaryApp()
        with open('tests/note.md') as f:
            note = f.read()

        with open('tests/note.html') as f:
            refNoteHtml = f.read()

        diary.text.setText(note)
        diary.markdown()
        noteHtml = diary.web.page().mainFrame().toHtml()

        self.assertEqual(noteHtml, refNoteHtml)


if __name__ == '__main__':
    unittest.main()
