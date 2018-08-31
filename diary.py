"""Module containing markdown-diary's actual Diary class."""
import os
import re
import datetime
import binascii
import tempfile


class Diary():
    """Class handling all the diary and note manipulation.

    The Diary is a data container and manipulation class. It can create and
    delete notes and diaries.
    """

    def __init__(self, fname):
        """Init method that reads in a diary from a file.

        Args:
            fname (str): Path to the diary to be loaded.
        """
        self.fname = fname
        with open(fname) as f:
            self.rawData = f.read()
        self.checksum = binascii.crc32(bytes(self.rawData, encoding="UTF-8"))
        self.data = self.extractData(self.rawData)

    def updateDiaryOnDisk(self, newData):
        """Save all changes to the diary to disk.

        If the diary's checksum changed in the meantime, abort the save.

        Args:
            newData (str): The whole diary as a string to be saved to disk.
        """
        with open(self.fname) as f:
            rawData = f.read()
        checksum = binascii.crc32(bytes(rawData, encoding="UTF-8"))

        if checksum == self.checksum:
            newChecksum = binascii.crc32(bytes(newData, encoding="UTF-8"))

            with tempfile.NamedTemporaryFile(
                    mode="w", prefix=".diary_", suffix=".tmp",
                    dir=os.path.dirname(self.fname), delete=False) as tmpf:
                tmpf.write(newData)
            os.replace(tmpf.name, self.fname)

            self.rawData = newData
            self.checksum = newChecksum
            self.data = self.extractData(self.rawData)

        else:
            print("ERROR: Diary file was changed! Abort save.")

    def saveNote(self, note, noteId, noteDate):
        """Save a new note to diary or update an existing one.

        Args:
            note (str): The note's contents.
            noteId (str): UUID of the note.
            noteDate (str): Note creation date.
        """
        if any(noteId in metaDict["note_id"] for metaDict in self.data):
            self.updateNote(note, noteId, noteDate)
        else:
            newData = self.rawData
            newData += self.createNoteHeader(noteId, noteDate)
            newData += note
            self.updateDiaryOnDisk(newData)

    @staticmethod
    def createNoteHeader(noteId, noteDate):
        """Create a note metadata header.

        Args:
            noteId (str): UUID of the note
            noteDate (str): Date of the note's creation

        Returns:
            Note header string.

        """
        header = ("\n<!---\n"
                  "markdown-diary note metadata\n"
                  "note_id = ")
        header += noteId
        header += "\n--->\n"
        header += noteDate
        header += "\n\n"

        return header

    def updateNote(self, note, noteId, noteDate):
        """Update an existing note.

        Args:
            note (str): The note's new contents.
            noteId (str): UUID of the note.
            noteDate (str): Note creation date.
        """
        reHeader = re.compile(
            r"""^<!---
                (?:\n|\r\n)
                markdown-diary\ note\ metadata
                (?:\n|\r\n)
                note_id\ =\                     # Hashtag for PEP8 compiance
                """ + noteId +
            r"""(.*?)
                --->
                """, re.MULTILINE | re.VERBOSE | re.DOTALL)

        reHeaderNext = re.compile(
            r'^<!---(?:\n|\r\n)markdown-diary note metadata(?:\n|\r\n)',
            re.MULTILINE)

        header = reHeader.search(self.rawData)
        nextHeader = reHeaderNext.search(self.rawData, header.end())

        newData = self.rawData[:header.end()]
        newData += "\n"
        newData += noteDate
        newData += "\n\n"
        newData += note
        if nextHeader is not None:
            # We need a newline separating note text from next header
            if newData[-1] is not '\n':
                newData += "\n"
            newData += self.rawData[nextHeader.start():]

        self.updateDiaryOnDisk(newData)

    def deleteNote(self, noteId):
        """Delete a note from a diary.

        Args:
            noteId (str): UUID of the note to be deleted.
        """
        reHeader = re.compile(
            r"""^<!---
                (?:\n|\r\n)
                markdown-diary\ note\ metadata
                (?:\n|\r\n)
                note_id\ =\                     # Hashtag for PEP8 compiance
                """ + noteId +
            r"""(.*?)
                --->
                """, re.MULTILINE | re.VERBOSE | re.DOTALL)

        reHeaderNext = re.compile(
            r'^<!---(?:\n|\r\n)markdown-diary note metadata(?:\n|\r\n)',
            re.MULTILINE)

        header = reHeader.search(self.rawData)
        nextHeader = reHeaderNext.search(self.rawData, header.end())

        newData = self.rawData[:header.start()]
        if nextHeader is not None:
            newData += "\n"
            newData += self.rawData[nextHeader.start():]

        self.updateDiaryOnDisk(newData)

    @staticmethod
    def extractData(rawData):
        """Get all notes' metadata and text from a diary.

        Args:
            diaryData (str): The whole diary as a string.

        Returns:
            A list of data dictionaries.

        """
        reHeader = re.compile(
            r"""^<!---                         # Beggining of Markdown comment
                (?:\n|\r\n)                    # Unix|Windows non-capturing \n
                markdown-diary\ note\ metadata # Mandatory first line
                (.*?)                          # Any characters including \n
                --->                           # End of Markdown comment
                """, re.MULTILINE | re.VERBOSE | re.DOTALL)

        matches = list(reHeader.finditer(rawData))

        data = []
        for i, match in enumerate(matches):
            dataDict = {}
            for line in rawData[
                    match.start():match.end()].splitlines()[2:-1]:
                key, val = line.partition("=")[::2]
                dataDict[key.strip()] = val.strip()

            date = rawData[match.end():].splitlines()[1]
            title = rawData[match.end():].splitlines()[3].strip("# ")

            text = ""
            if i == len(matches) - 1:
                text = rawData[matches[i].end():].split("\n", maxsplit=3)[3]
            else:
                text = rawData[matches[i].end(): matches[i + 1].start()].split("\n", maxsplit=3)[3]

            dataDict["date"] = date
            dataDict["title"] = title
            dataDict["text"] = text

            data.append(dataDict)

        return data

    def getNote(self, noteId):
        """Extract note text from diary.

        Args:
            noteId (str): UUID of the requested note.

        Returns:
            A single note's text.

        """
        for datum in self.data:
            if datum["note_id"] == noteId:
                return datum["text"]

        return None

    def getNoteMetadata(self, noteId):
        """Get metadata of a single note.

        Args:
            noteId (str): UUID of the requested note.

        Returns:
            A metadata dictionary. Returns None if noteId not found.

        """
        for datum in self.data:
            if noteId == datum["note_id"]:
                return datum

        return None

    def searchNotes(self, pattern):
        """Search for all notes containing 'pattern'.

        Args:
            pattern (string): Text to look for.

        Returns:
            A list of metadata of all matching notes.

        """
        matching = []
        for datum in self.data:
            if pattern in datum["text"]:
                matching.append(datum)

        return matching

    def changeNoteDate(self, noteId, newDate):
        """Change date of a note."""
        self.saveNote(self.getNote(noteId), noteId, newDate)

    @staticmethod
    def isValidDate(date):
        """Check whether a date is of a valid format."""
        try:
            datetime.datetime.strptime(date, '%Y-%m-%d')
            if len(date) != 10:
                return False
            return True
        except ValueError:
            return False
