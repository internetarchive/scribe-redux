import json
import traceback
import urllib
from string import join

from kivy._event import partial
from kivy.adapters.listadapter import ListAdapter
from kivy.app import App
from kivy.network.urlrequest import UrlRequest
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch


from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import BooleanProperty, ObjectProperty, NumericProperty, ListProperty, StringProperty, DictProperty
from kivy.config import Config
from kivy.core.window import Window 
from kivy.cache import Cache

import logging
import os
import sys, subprocess

# import internetarchive as ia
import requests
from dowewantit.DWWI import DWWIWidget
from marc.MARC import MARCWidget

# the kivy file containing the UI templates and actions
Builder.load_file('scribe.kv')

ignore_donation_items = True


# MetadataTextInput
# _________________________________________________________________________________________
class MetadataTextInput(TextInput):
    metadata_key = StringProperty(None)
    key_input = ObjectProperty(None)
    pass


# MetadataSwitch
# _________________________________________________________________________________________
class MetadataSwitch(Switch):
    metadata_key = StringProperty(None)
    pass


# CaptureScreen
# _________________________________________________________________________________________
class CaptureScreen(Screen):
    scribe_widget = ObjectProperty(None)
    screen_manager = ObjectProperty(None)


# CaptureCover
# this class manages the cover capture dialog
# Main thread
# _________________________________________________________________________________________
class CaptureCover(BoxLayout):

    capture_screen = ObjectProperty(None)
    popup = ObjectProperty(None)

    def select_default_collection(self):
        print self

        # self.ids._cset_list.text = self.get_collection_sets()[0]

    def add_marc(self):
        content = MARCDialog(capture_screen=self.capture_screen)
        self.popup = Popup(title="MARC Record", content=content, size_hint=(0.7, 0.5),)
        self.popup.open()


class MARCDialog(FloatLayout):

    def __init__(self, capture_screen, **kwargs):
        super(MARCDialog, self).__init__(**kwargs)

    def save_metadata(self):
        pass


class BarcodeWidget(BoxLayout):
    capture_screen = ObjectProperty(None)

    def load_universal(self):
        self.ids._image.source = self.loading_image
        identifier = self.ids._barcode.text
        archive_ids = []
        if not identifier:
            self.show_error('You must scan an identifier barcode!')
            return

        api_url = 'https://archive.org/book/want/isbn_to_identifier.php?isbn='

        response = json.loads(requests.get(api_url + identifier).text)
        if response['status'] == 'ok':
            archive_ids = [x for x in response['scannable_identifiers']]
            content = UniversalIDDialog(id_list = archive_ids, callback=self.setup_scannable_id)
            self.popup = Popup(title="Select an identifier to scan", content=content,
                                size_hint=(0.7, 0.5),)
            content.popup = self.popup
            self.popup.open()

        else:
            content = Label(text="No items were found")
            self.popup = Popup(title="Select an identifier to scan", content=content,
                                size_hint=(0.3, 0.3), auto_dismiss=True)
            content.popup = self.popup
            self.popup.open()

    def setup_scannable_id(self, identifier, *args):
        self.ids._barcode.text = identifier
        self.ids._button.disabled = True
        self.ids._button_isbn.disabled = True
        self.popup.dismiss()
        try:
            self.load_metadata()
        except:
            print "\n This is really not supposed to happen."

    def print_barcode(self):
        try:
            print "Ok, called barcode."
            l = label.label_create(self.ids._barcode.text)
            print l
            # webbrowser.open(l)
            try:
                import cups
                conn = cups.Connection()
                config = get_metadata(scribe_globals.scancender_metadata)
                if 'printer' in config: 
                    print "Found printer in config", config['printer']
                    printer_name = config['printer']
                else:
                    print "Defaulting to LabelWriter-450-Turbo printer"
                    printer_name = "LabelWriter-450-Turbo"
                conn.printFile(printer_name, l, "", {})
            except Exception as e:
                print "Couldn't print label. Error was", e
        except Exception as e:
            print "There was an error creating the barcode."
            print e
            pass

    # load_metadata()
    # _____________________________________________________________________________________
    def load_metadata(self):
        self.ids._image.source = self.loading_image
        self.ids._button.disabled = True
        identifier = self.ids._barcode.text
        if not identifier:
            self.show_error('You must scan an identifier barcode!')
            return

        self.metadata = None
        self.identifier = identifier
        files_url = 'https://archive.org/metadata/{id}/files'.format(id=self.identifier)
        req = UrlRequest(files_url, self.load_metadata_callback, on_error=self.error_callback, on_failure=self.error_callback)

    # load_metadata_callback()
    # _____________________________________________________________________________________
    def load_metadata_callback(self, req, files):
        
        if files is None:
            self.show_error('Could not fetch metadata from archive.org')
            return

        if 'error' in files:
            self.show_error(files['error'])
            return

        if 'result' not in files:
            self.show_error('archive.org Metadata API returned an empty response')
            return

        # TODO: Add warc et al
        allowed_formats = set(['Metadata', 'MARC', 'MARC Source', 'MARC Binary', 'Dublin Core', 'Archive BitTorrent', 
                            'Web ARChive GZ', 'Web ARChive', 'Log', 'OCLC xISBN JSON', 'Internet Archive ARC', 
                            'Internet Archive ARC GZ', 'CDX Index', 'Item CDX Index', 'Item CDX Meta-Index',
                            'WARC CDX Index', 'Metadata Log' ]);
        for file in files['result']:
            if file['format'] not in allowed_formats:
                self.show_error('This item already contains data files!\n(file={file}, format={format})'.format(file=file['name'], format=file['format']))
                return

        # download meta.xml and put it in the item
        # TODO: make this non-blocking. Since /download/ returns a redirect, using
        # kivy's UrlRequest is not straightforward
        meta_url = 'https://archive.org/download/{id}/{id}_meta.xml'.format(id=self.identifier)
        meta_path = join(self.capture_screen.book_dir, 'metadata.xml')
        try:
            urllib.urlretrieve(meta_url, meta_path)
        except Exception:
            self.show_error('Could not download meta.xml from archive.org!')
        self.capture_screen.load_metadata()
        self.capture_screen.disable_metadata()

        # write out identifier.txt
        id_path = join(self.capture_screen.book_dir, 'identifier.txt')
        f = open(id_path, 'w')
        f.write(self.identifier)
        f.close()

        self.ids._image.source = self.transparent_image

    # error_callback()
    # _____________________________________________________________________________________
    def error_callback(self, request, error):
        print 'error:', error
        self.show_error('You seem to be offline.\nIrregardless, creating id {id}'.format(id=self.identifier))
        # write out identifier.txt
        try:
            id_path = join(self.capture_screen.book_dir, 'identifier.txt')
            f = open(id_path, 'w')
            f.write(self.identifier)
            f.close()
            print "ALL DONE, CREATED OFFLINE ITEM", self.identifier
        except:
            self.show_error('There was an error creating id {id}'.format(id=self.identifier))

    # metadata_thread()
    # _____________________________________________________________________________________
    def metadata_thread(self, url):
        try:
            self.metadata = json.load(urllib.urlopen(url))
        except Exception:
            self.metadata = None

    # show_error()
    # _____________________________________________________________________________________
    def show_error(self, msg):
        self.ids._image.source = self.transparent_image
        self.ids._button.disabled = False
        print traceback.format_exc()
        msg_box = ScribeMessage()
        msg_box.text = msg
        popup = Popup(title='Barcode Error', content=msg_box, auto_dismiss=False, size_hint=(None, None), size=(400, 300))
        msg_box.popup = popup
        msg_box.trigger_func = popup.dismiss
        popup.open()

# UniversalIDDialog
# this is the widget to that shows a list of possible identifiers
# obtained by querying the ISBN-to-id API on archive.org
# _________________________________________________________________________________________


class UniversalIDDialog(FloatLayout):
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    book_path = StringProperty()
    popup = ObjectProperty(None)
    id_list = ListProperty(None)
    callback = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(UniversalIDDialog, self).__init__(**kwargs)
        adapter = ListAdapter(
                data=self.id_list,
                selection_mode='single',
                allow_empty_selection=False,
                cls=ListItemButton)
        # adapter.bind(on_selection_change = self.selected_callback)
        self.listview = ListView(adapter=adapter)
        rootbox = self.ids._list_box
        rootbox.add_widget(self.listview)

    def button_callback(self):
        print "SELECTED ITEM", self.listview.adapter.selection[0].text
        print self.callback
        Clock.schedule_once(partial(self.callback, self.listview.adapter.selection[0].text))

    # show_error()
    # _____________________________________________________________________________________
    def show_error(self, msg):
        msg_box = ScribeMessage()
        msg_box.text = msg
        popup = Popup(title=' Error', content=msg_box, auto_dismiss=False, size_hint=(None, None), size=(400, 300))
        msg_box.popup = popup
        msg_box.trigger_func = self.popup_dismiss
        popup.open()

    # popup_dismiss()
    # _____________________________________________________________________________________
    def popup_dismiss(self, popup):
        popup.dismiss()


class ScribeWidget(BoxLayout):
    # _____________________________________________________________________________________
    def __init__(self, **kwargs):
        super(ScribeWidget, self).__init__(**kwargs)


# this class tarts the UI and the app
# _________________________________________________________________________________________
class Scribe3(App):

    ignore_donation_items = BooleanProperty(False)

    catalogs = ['calcas', 'olcas', 'notre_dame', ]

    def __init__(self, **kwargs):
        super(Scribe3, self).__init__(**kwargs)

        self.ignore_donation_items = False

    def build(self):
        self.title = 'ttscribe redux'
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
        return ScribeWidget()


if __name__ == '__main__':
    Scribe3().run()



