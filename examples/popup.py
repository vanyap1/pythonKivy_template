'''
Example to show a Popup usage with the content from kv lang.
'''
from kivy.uix.popup import Popup
from kivy.uix.button import Button, Label
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty, ListProperty


Builder.load_string('''
<CustomPopup>:
    size_hint: .5, .5
    auto_dismiss: False
    title: 'Hello world'
    BoxLayout:
        orientation: 'vertical' 
        padding: 10
        spacing: 10
        canvas:
            Color:
                rgba: 0, 0, 0, 0
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: 'This is a popup with content defined in kv language.'
            size_hint_y: None
            height: self.texture_size[1]
        Slider:
            min: 0
            max: 100
            value: root.val
            size_hint_y: None
            height: '44dp'
        
        BoxLayout:
            size_hint_y: None
            height: '64dp'
            padding: 10
            spacing: 10
            canvas:
                Color:
                    rgba: 0, 0, 0, 0
                Rectangle:
                    pos: self.pos
                    size: self.size       
            Button:
                text: 'OK'
                on_press: root.dismiss()
            Button:
                text: 'Cancel'
                on_press: root.dismiss()
        
    
''')


class CustomPopup(Popup):
    val = NumericProperty(30)
    pass


class TestApp(App):
    def build(self):
        b = Button(on_press=self.show_popup, text="Show Popup")
        return b

    def show_popup(self, b):
        p = CustomPopup()
        p.open()


TestApp().run()
