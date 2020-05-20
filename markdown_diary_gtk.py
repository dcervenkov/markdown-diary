import sys
from logzero import logger as log
import markdown_math
import style
import diary
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
gi.require_version('WebKit', '3.0')

from gi.repository import Gio, Gtk, GtkSource, WebKit, GObject  # noqa


class DiaryApp(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self,
                                 application_id='com.github.dcervenkov.markdown-diary',
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):

        builder = Gtk.Builder()
        GObject.type_register(GtkSource.View)
        GObject.type_register(WebKit.WebView)
        builder.add_from_file('resources/markdown_diary.ui')

        window = builder.get_object('main_window')
        window.set_application(self)

        lang_mgr = GtkSource.LanguageManager()
        lang = lang_mgr.get_language('markdownplus')
        if lang is None:
            log.warning('"markdownplus" language spec not found, falling back to "markdown"')
            lang = lang_mgr.get_language('markdown')
        buff = GtkSource.Buffer().new_with_language(lang)
        self.text = builder.get_object('text')
        self.text.set_buffer(buff)
        self.web = builder.get_object('web')
        self.stack = builder.get_object('stack')
        self.stack.set_visible_child_name('web')
        self.liststore = builder.get_object('liststore')
        self.tree = builder.get_object('tree')

        self.edit_button = builder.get_object('edit_button')
        self.edit_button.connect('toggled', self.edit_toggle)

        window.show_all()

        self.diary = diary.Diary('diary.md')
        self.loadTree(self.diary.data)

    def loadTree(self, metadata):
        """Load notes tree from diary metadata.

        Load notes tree from diary metadata and populate the ListStore
        with it.
        """
        self.liststore.clear()

        for note in metadata:
            self.liststore.append([note["note_id"], note["date"], note["title"]])

    def edit_toggle(self, msg):
        if self.stack.get_visible_child_name() == 'text':
            self.stack.set_visible_child_name('web')
        else:
            self.stack.set_visible_child_name('text')


def main():

    app = DiaryApp()
    app.run(sys.argv)


if __name__ == '__main__':
    main()
