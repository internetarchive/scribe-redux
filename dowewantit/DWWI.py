"""

URL: https://archive.org/services/book/v1/do_we_want_it/?iTESTISBN00016sbn=:isbn&debug=:debug

0: TESTISBN00014
1: TESTISBN00012
2: TESTISBN00018
3: TESTISBN00016

"""
import glob
import json
import os
import requests

from kivy.adapters.args_converters import list_item_args_converter
from kivy.adapters.listadapter import ListAdapter
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty

from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.listview import ListItemButton
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import SlideTransition, Screen, ScreenManager
from kivy.uix.textinput import TextInput

try:
    Builder.load_file('dowewantit/DWWI.kv')
except IOError:
    Builder.load_file('DWWI.kv')


class MetadataTextInput(TextInput):
    metadata_key = StringProperty(None)
    key_input = ObjectProperty(None)
    pass


class CautionPopup(Popup):
    main_widget = ObjectProperty(None)

    def set_main_widget(self, wid):
        self.main_widget = wid

    def on_btn_left(self):
        self.remove_tmp_btn()
        self.main_widget.try_again()

    def on_btn_right(self):
        self.remove_tmp_btn()
        self.main_widget.confirm()

    def remove_tmp_btn(self):
        try:
            wid = self.ids['btn_scan_anyway']
            self.ids['ly_grid'].remove_widget(wid)
        except KeyError:
            pass


class NotificationPopup(Popup):
    pass


class SIPopup(Popup):
    """
    Shipping Instruction Popup
    """
    dropdown = DropDown()
    boxid = StringProperty('')

    def __init__(self):
        super(Popup, self).__init__()
        # self.ids['lb_stat'].bind(focus=self.on_focus_text)
        self.add_dropdown()

    def on_btn_confirm(self):
        """
        :return:
        """
        boxid = self.ids['btn_dropdown'].text
        if self.check_box_id(boxid):
            print "Box ID is valid: ", boxid
            # TODO: Use IA metadata API to set box id value (Davide will do this)

        else:
            print "Invalid Box ID: ", boxid
            self.ids.lb_stat.text = "Invalid Box ID, please try again."
            Clock.schedule_once(self.change_label, 3)

    def check_box_id(self, boxid):
        """
        Check input box_id is valid or not
        :param boxid:
        :return:
        """
        # TODO: implement logic of validating box_id user input.
        return False

    def change_label(self, *args):
        self.ids['lb_stat'].text = 'Input Box ID: '

    def add_dropdown(self):

        # TODO: get valid Boxid values

        for index in range(10):
            btn = Button(text='Value %d' % index, size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.dropdown.select(btn.text))
            self.dropdown.add_widget(btn)

        m_button = self.ids['btn_dropdown']
        m_button.bind(on_release=self.dropdown.open)

        self.dropdown.bind(on_select=lambda instance, x: setattr(m_button, 'text', x))


class DWWIWidget(BoxLayout):
    current_title = StringProperty()  # Store title of current screen
    screen_names = ListProperty([])
    screens = {}  # Dict of all screens
    hierarchy = ListProperty([])

    caution_popup = ObjectProperty(None)
    si_popup = ObjectProperty(None)
    n_popup = ObjectProperty(None)

    re_code = NumericProperty(-2)
    sm = ObjectProperty(None)
    response = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(DWWIWidget, self).__init__(**kwargs)
        self.caution_popup = CautionPopup()
        self.caution_popup.set_main_widget(self)
        self.si_popup = SIPopup()
        self.n_popup = NotificationPopup()

        self.load_screen()

        self.go_screen('entry', 'left')

    def load_screen(self):
        """
        Load all screens from data/screens to Screen Manager
        :return:
        """
        available_screens = []

        full_path_screens = glob.glob("dowewantit/screens/*.kv")
        if len(full_path_screens) == 0:
            full_path_screens = glob.glob("screens/*.kv")

        for file_path in full_path_screens:
            file_name = os.path.basename(file_path)
            available_screens.append(file_name.split(".")[0])

        self.screen_names = available_screens
        for i in range(len(full_path_screens)):
            screen = Builder.load_file(full_path_screens[i])
            self.screens[available_screens[i]] = screen

        self.sm = ScreenManager(id='sm')
        self.add_widget(self.sm)
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
        elif dest_screen == 'book_library':
            self.update_books()
            # self.caution_popup.open()

        self.sm.transition = SlideTransition()
        screen = self.screens[dest_screen]
        self.sm.switch_to(screen, direction=direction)
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
            if len(msg) == 0:
                self.n_popup.ids['lb_content'].text = 'Error, please input ASIN/ISBN.'
                self.n_popup.open()
                return False
            elif len(msg) not in [10, 13]:  # length should be 10 or 13
                self.n_popup.ids['lb_content'].text = 'Error, invalid ASIN/ISBN.'
                self.n_popup.open()
                self.screens['search'].ids['_identifier'].text = ''
                return False
            else:
                return True

        _id = self.screens['search'].ids['_identifier'].text

        if not check_content(_id):
            print "Invalid type of ASIN/ISBN number"
            return False

        wid.disabled = True

        api_url = 'https://archive.org/services/book/v1/do_we_want_it/?isbn='

        try:
            self.response = json.loads(requests.get(api_url + _id + '&debug=true').text)
        except requests.exceptions.ConnectionError as e:
            print e
            # TODO: Display Error message
            return False

        if self.response['status'] == 'ok':

            self.re_code = self.response['response']
            # self.re_code = 2

            if self.re_code == -1:   # invalid asin or isbn
                self.caution_popup.ids['btn_confirm'].text = 'Confirm'
                self.display_popup('Invalid ASIN or ISBN')

            elif self.re_code == 0:   # we don't need this book
                self.caution_popup.ids['btn_confirm'].text = 'Confirm'
                new_btn = Button(text='Scan anyway', id='btn_scan_anyway')
                new_btn.bind(on_release=self.scan_anyway)
                self.caution_popup.ids['ly_grid'].add_widget(new_btn)
                self.display_popup("We do not need to scan this book.")

            elif self.re_code == 1:   # we need to scan this book
                # TODO: We will fetch metadata from an API called MARC API
                self.caution_popup.ids['btn_confirm'].text = 'Scan this book'
                self.display_popup("We need to scan this book")

            elif self.re_code == 2:   # we have already scanned this book, but need another physical copy for a partner
                self.screens['book_library'].ids['lb_content'].text = "We need another copy for a partner"
                self.go_screen('book_library', 'left')

            elif self.re_code == 3:   # we have already scanned this book, but need another physical copy for ourselves
                self.screens['book_library'].ids['lb_content'].text = "We need another copy for ourselves"
                self.go_screen('book_library', 'left')

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

    def update_books(self):
        """
        Update list view on book library screen
        :return:
        """
        book_list_adapter = ListAdapter(data=self.response['books'], args_converter=list_item_args_converter,
                                        selection_mode='single', propagate_selection_to_data=False,
                                        allow_empty_selection=False, cls=ListItemButton)
        self.screens['book_library'].ids['l_book'].adapter = book_list_adapter

    def show_si_popup(self):
        """
        This function is called when user presses "Send us this book" button after getting response 2 or 3
        :return:
        """
        if App.get_running_app().ignore_donation_items:
            self.n_popup.ids['lb_content'].text = 'We have already scanned this book.\n' \
                                                  'Please send it to the boxing station'
            self.n_popup.open()
            self.go_screen('entry', 'left')
        else:
            adapter = self.screens['book_library'].ids['l_book'].adapter
            self.si_popup.ids['lb_stat'].text = "Input Box ID: "
            self.si_popup.ids['lb_book_id'].text = "Book ID: " + adapter.selection[0].text
            self.si_popup.open()

    def scan_anyway(self, *args):
        """
        Return {'DWWI': False} dict to the main widget
        :return:
        """
        self.caution_popup.remove_tmp_btn()
        self.caution_popup.dismiss()
        ret_val = {'DWWI': False}
        # TODO: Implement logic of returning this value to the main widget. (Not sure which widget should receive this)
        print ret_val


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
