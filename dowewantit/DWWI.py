from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty, ObjectProperty
Builder.load_file('dowewantit/DWWI.kv')

class DWWIWidget(BoxLayout):
    capture_screen = ObjectProperty(None)
    # __init__()
    #_____________________________________________________________________________________
    def __init__(self, **kwargs):
        super(DWWIWidget, self).__init__(**kwargs)

    def search(self):
        print "called search"