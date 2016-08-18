"""

URL: https://archive.org/services/book/v1/do_we_want_it/?isbn=:isbn&debug=:debug

"""
import glob
import json
import os
import requests

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import SlideTransition, Screen
from kivy.uix.textinput import TextInput

Builder.load_file('DWWI.kv')


class MainScreen(Screen):
    fullscreen = BooleanProperty(False)

    def add_widget(self, *args):
        if 'content' in self.ids:
            return self.ids.content.add_widget(*args)
        return super(MainScreen, self).add_widget(*args)


class MetadataTextInput(TextInput):
    metadata_key = StringProperty(None)
    key_input = ObjectProperty(None)
    pass


class CautionPopup(Popup):
    pass


class ResultPopup(Popup):
    pass


class DWWIWidget(BoxLayout):
    current_title = StringProperty()  # Store title of current screen
    screen_names = ListProperty([])
    screens = {}  # Dict of all screens
    hierarchy = ListProperty([])

    capture_screen = ObjectProperty(None)
    caution_popup = ObjectProperty(None)
    result_popup = ObjectProperty(None)
    re_code = NumericProperty(-2)

    def __init__(self, **kwargs):
        super(DWWIWidget, self).__init__(**kwargs)
        self.caution_popup = CautionPopup()
        self.result_popup = ResultPopup()

        self.load_screen()

        self.go_screen('entry', 'left')

    def load_screen(self):
        """
        Load all screens from data/screens to Screen Manager
        :return:
        """
        available_screens = []

        full_path_screens = glob.glob("screens/*.kv")

        for file_path in full_path_screens:
            file_name = os.path.basename(file_path)
            available_screens.append(file_name.split(".")[0])

        self.screen_names = available_screens
        for i in range(len(full_path_screens)):
            screen = Builder.load_file(full_path_screens[i])
            self.screens[available_screens[i]] = screen
        return True

    def go_screen(self, dest_screen, direction):
        """
        Go to given screen
        :param dest_screen:     destination screen name
        :param direction:       "up", "down", "right", "left"
        :return:
        """

        if dest_screen == 'search':
            self.screens['search'].ids['_identifier'].text = ''

        sm = self.ids.sm
        sm.transition = SlideTransition()
        screen = self.screens[dest_screen]
        sm.switch_to(screen, direction=direction)
        self.current_title = screen.name

    def search(self, wid):
        """
        Send request to the server and parse response.
        :param wid: Button widget itself
        :return:
        """
        def check_content(msg):
            """
            * Preprocessing function : Check msg is valid ASIN or ISBN.
            :param msg:
            :return:
            """
            # TODO: Add logic to check whether the value has valid type of ASIN/ISBN or not.
            if len(msg) not in [10, 13]:  # length should be 10 or 13
                return False
            else:
                return True

        _id = self.screens['search'].ids['_identifier'].text

        if not check_content(_id):
            print "Invalid type of ASIN/ISBN number"
            return False

        wid.disabled = True

        api_url = 'https://archive.org/services/book/v1/do_we_want_it/?isbn='

        response = json.loads(requests.get(api_url + _id + '&debug=true').text)

        if response['status'] == 'ok':

            self.re_code = response['response']
            # self.re_code = 2

            if self.re_code == -1:   # invalid asin or isbn
                self.caution_popup.ids['btn_confirm'].text = 'Confirm'
                self.display_popup('Invalid ASIN or ISBN')

            elif self.re_code == 0:   # we don't need this book
                self.caution_popup.ids['btn_confirm'].text = 'Confirm'
                self.display_popup("We do not need to scan this book.")

            elif self.re_code == 1:   # we need to scan this book
                self.caution_popup.ids['btn_confirm'].text = 'Scan this book'
                self.display_popup("We need to scan this book")

            elif self.re_code == 2:   # we have already scanned this book, but need another physical copy for a partner
                self.caution_popup.ids['btn_confirm'].text = 'Send us this book'
                self.display_popup("We need another copy for a partner")

            elif self.re_code == 3:   # we have already scanned this book, but need another physical copy for ourselves
                self.caution_popup.ids['btn_confirm'].text = 'Send us this book'
                self.display_popup("We need another copy for ourselves")

        else:
            self.re_code = -2
            self.display_popup("Error with the input string or the service.")

        # Enable new search
        wid.disabled = False

    def try_again(self):
        """
        Clear DWWI widget and allow new search
        :return:
        """
        self.caution_popup.dismiss()
        self.screens['search'].ids['_identifier'].text = ''

    def confirm(self):
        self.caution_popup.dismiss()
        if self.re_code == -1:
            self.go_screen('entry', 'right')

        elif self.re_code == 0:
            # TODO: user will select boot from books table and optionally add to book locker.
            self.go_screen('entry', 'right')

        elif self.re_code == 1:
            # TODO: Implement logic of scanning this book
            self.go_screen('entry', 'right')

        elif self.re_code == 2:
            # TODO: get link to shipping instructions and display
            self.result_popup.ids['lb_content'].text = 'Link to shipping instructions:'
            self.result_popup.open()
            self.go_screen('book_library', 'up')

        elif self.re_code == 3:
            # TODO: get link to shipping instructions and display
            self.result_popup.ids['lb_content'].text = 'Link to shipping instructions:'
            self.result_popup.open()
            self.go_screen('book_library', 'up')

    def display_popup(self, message):
        """
        Display caution popup
        :param message: Content to display
        :return:
        """
        self.caution_popup.ids['lb_content'].text = message
        self.caution_popup.open()


class DWWI(App):
    """
    Launch app
    """
    def __init__(self, **kwargs):
        super(DWWI, self).__init__(**kwargs)

    def build(self):
        self.title = 'Do We Want it?'
        return DWWIWidget()


if __name__ == '__main__':
    DWWI().run()
