"""

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

# Builder.load_file('MARC.kv')


class MetadataTextInput(TextInput):
    metadata_key = StringProperty(None)
    key_input = ObjectProperty(None)
    pass


class NotifyPopup(Popup):
    pass


class MARCWidget(BoxLayout):
    current_title = StringProperty()  # Store title of current screen
    screen_names = ListProperty([])
    screens = {}  # Dict of all screens
    hierarchy = ListProperty([])

    sm = ObjectProperty(None)

    n_popup = ObjectProperty(None)

    dd_type = DropDown()
    dd_cat = DropDown()

    response = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(MARCWidget, self).__init__(**kwargs)

        self.n_popup = NotifyPopup()

        self.load_screen()

        self.go_screen('entry', 'left')

        self.add_dropdowns()

    def load_screen(self):
        """
        Load all screens from data/screens to Screen Manager
        :return:
        """
        available_screens = []

        full_path_screens = glob.glob("marc/screens/*.kv")
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
            if len(App.get_running_app().catalogs) == 0:
                self.show_notification("Error\n\nYou must have configured catalogs t0 use MARC Search.", 24)
                return False
            self.screens['search'].ids['txt_query'].text = ''

        elif dest_screen == 'result':
            self.screens['result'].ids['lb_result'].text = self.response

        self.sm.transition = SlideTransition()
        screen = self.screens[dest_screen]
        self.sm.switch_to(screen, direction=direction)
        self.current_title = screen.name

    def add_dropdowns(self):
        """
        Added child widgets to dropdown widgets
        :return:
        """
        # Added type of MARC
        l_type = ['local', 'isbn', 'standard', 'call', 'keyword', 'title', 'author']
        for t in l_type:
            btn = Button(text=t, size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.dd_type.select(btn.text))
            self.dd_type.add_widget(btn)

        t_button = self.screens['search'].ids['btn_dd_type']
        t_button.bind(on_release=self.dd_type.open)
        self.dd_type.bind(on_select=lambda instance, x: setattr(t_button, 'text', x))
        t_button.text = l_type[0]

        # Added catalog dropdown
        l_cat = App.get_running_app().catalogs
        if len(l_cat) == 0:
            print "There is no configured catalog..."
            return False

        for cat in l_cat:
            btn = Button(text=cat, size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.dd_cat.select(btn.text))
            self.dd_cat.add_widget(btn)

        c_button = self.screens['search'].ids['btn_dd_catalog']
        c_button.bind(on_release=self.dd_cat.open)
        self.dd_cat.bind(on_select=lambda instance, x: setattr(c_button, 'text', x))
        c_button.text = l_cat[0]

    def search(self):
        """
        Send get request
        :return:
        """
        cur_cat = self.screens['search'].ids['btn_dd_catalog'].text
        cur_cat = cur_cat.replace(' ', '+')

        cur_type = self.screens['search'].ids['btn_dd_type'].text
        query = self.screens['search'].ids['txt_query'].text
        if len(query.strip()) == 0:
            self.show_notification('Error\nPlease input query value.')
            return False

        # http://www-judec.archive.org/book/marc/get_marc.php?term=isbn&value=9780750700160&catalog=Independence+Seaport+Museum+-+WorldCat+access
        api_url = 'http://www-judec.archive.org/book/marc/get_marc.php?term='
        try:
            self.response = json.loads(requests.get(api_url + cur_type + '&value=' + query + '&catalog=' + cur_cat).text)
        except requests.exceptions.ConnectionError as e:
            print e
            # TODO: Display Error message
            return False

        # For test
        if self.response['sts'] == 'OK':
            print self.response
            self.go_screen('result', 'left')

        elif self.response['sts'] == 'ERROR':
            print self.response['error']
            self.show_notification('Invalid value of request, pleaes try again.')

    def show_notification(self, msg, font_size=30):
        """
        Open Notification Popup window with given parameters
        :param msg:
        :param font_size:
        :return:
        """
        self.n_popup.ids['lb_content'].font_size = font_size
        self.n_popup.ids['lb_content'].text = msg
        self.n_popup.open()

    def btn_accept(self):
        """
        Callback function of ACCEPT button on the result screen
        :return:
        """
        # TODO: return to CaptureScreen screen with values populated
        print self.response


class MARC(App):
    """
    Launch app
    """

    catalogs = ['calcas', 'olcas', 'notre_dame', ]
    catalogs = []

    def __init__(self, **kwargs):
        super(MARC, self).__init__(**kwargs)

    def build(self):
        self.title = 'Do We Want it?'
        return MARCWidget()


if __name__ == '__main__':
    MARC().run()
