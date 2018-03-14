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
            self.data = f.read()
        self.checksum = binascii.crc32(bytes(self.data, encoding="UTF-8"))
        self.metadata = self.getMetadata(self.data)

    def updateDiaryOnDisk(self, newData):
        """Save all changes to the diary to disk.

        If the diary's checksum changed in the meantime, abort the save.

        Args:
            newData (str): The whole diary as a string to be saved to disk.
        """
        with open(self.fname) as f:
            data = f.read()
        checksum = binascii.crc32(bytes(data, encoding="UTF-8"))

        if checksum == self.checksum:
            newChecksum = binascii.crc32(bytes(newData, encoding="UTF-8"))

            with tempfile.NamedTemporaryFile(
                    mode="w", prefix=".diary_", suffix=".tmp",
                    dir=os.path.dirname(self.fname), delete=False) as tmpf:
                tmpf.write(newData)
            os.replace(tmpf.name, self.fname)

            self.data = newData
            self.checksum = newChecksum
            self.metadata = self.getMetadata(self.data)

        else:
            print("ERROR: Diary file was changed! Abort save.")

    def saveNote(self, note, noteId, noteDate):
        """Save a new note to diary or update an existing one.

        Args:
            note (str): The note's contents.
            noteId (str): UUID of the note.
            noteDate (str): Note creation date.
        """
        if any(noteId in metaDict["note_id"] for metaDict in self.metadata):
            self.updateNote(note, noteId, noteDate)
        else:
            newData = self.data
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

        header = reHeader.search(self.data)
        nextHeader = reHeaderNext.search(self.data, header.end())

        newData = self.data[:header.end()]
        newData += "\n"
        newData += noteDate
        newData += "\n\n"
        newData += note
        if nextHeader is not None:
            # We need a newline separating note text from next header
            if newData[-1] is not '\n':
                newData += "\n"
            newData += self.data[nextHeader.start():]

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

        header = reHeader.search(self.data)
        nextHeader = reHeaderNext.search(self.data, header.end())

        newData = self.data[:header.start()]
        if nextHeader is not None:
            newData += "\n"
            newData += self.data[nextHeader.start():]

        self.updateDiaryOnDisk(newData)

    @staticmethod
    def getMetadata(diaryData):
        """Get all notes' metadata from a diary.

        Args:
            diaryData (str): The whole diary as a string.

        Returns:
            A list of metadata dictionaries.

        """
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

    def getNote(self, noteId):
        """Extract note text from diary.

        Args:
            noteId (str): UUID of the requested note.

        Returns:
            A single note's text.

        """
        if not any([noteId in metaDict["note_id"] for metaDict in self.metadata]):
            return None

        reHeader = re.compile(
            r"""^<!---
                (?:\n|\r\n)
                markdown-diary\ note\ metadata
                (?:\n|\r\n)
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

        header = reHeader.search(self.data)
        nextHeader = reHeaderNext.search(self.data, header.end())

        # If this is the last note in the diary, return everything that follows
        if nextHeader is None:
            return self.data[header.end():]

        return self.data[header.end(): nextHeader.start()]

    def getNoteMetadata(self, noteId):
        """Get metadata of a single note.

        Args:
            noteId (str): UUID of the requested note.

        Returns:
            A metadata dictionary. Returns None if noteId not found.

        """
        for metaDict in self.metadata:
            if noteId == metaDict["note_id"]:
                return metaDict

        return None

    def searchNotes(self, pattern):
        """Search for all notes containing 'pattern'.

        Args:
            pattern (string): Text to look for.

        Returns:
            A list of metadata of all matching notes.

        """
        matching = []
        rePattern = re.compile(re.escape(pattern), re.IGNORECASE)
        for metadatum in self.metadata:
            if rePattern.search(self.getNote(metadatum["note_id"])):
                matching.append(metadatum)

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
