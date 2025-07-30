from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.clock import Clock


class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = [0, 0, 0, 0]  # Transparent

        # Draw the button background
        with self.canvas.before:
            Color(0.0, 0.58, 0.267, 1)  # #009444 button color
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[34]
            )

        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class SecondaryButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = [0, 0, 0, 0]  # Transparent

        # Draw the button background
        with self.canvas.before:
            Color(0.816, 0.835, 0.867, 1)  # Light gray background
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[34]
            )

        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class CameraPreview(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scanning = False

        with self.canvas:
            # Dark background for camera preview
            Color(0.1, 0.1, 0.1, 1)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[20]
            )

            # Overlay for ID card outline
            Color(0.0, 0.58, 0.267, 0.8)  # Semi-transparent green
            self.overlay_rect = RoundedRectangle(
                pos=(self.pos[0] + 40, self.pos[1] + 60),
                size=(self.size[0] - 80, self.size[1] - 120),
                radius=[15]
            )

            # Corner indicators
            Color(0.0, 0.58, 0.267, 1)  # Solid green
            corner_size = 30
            line_width = 4

            # Top-left corner
            Line(points=[self.pos[0] + 50, self.pos[1] + self.size[1] - 70,
                         self.pos[0] + 50 + corner_size, self.pos[1] + self.size[1] - 70], width=line_width)
            Line(points=[self.pos[0] + 50, self.pos[1] + self.size[1] - 70,
                         self.pos[0] + 50, self.pos[1] + self.size[1] - 70 - corner_size], width=line_width)

            # Top-right corner
            Line(points=[self.pos[0] + self.size[0] - 50, self.pos[1] + self.size[1] - 70,
                         self.pos[0] + self.size[0] - 50 - corner_size, self.pos[1] + self.size[1] - 70], width=line_width)
            Line(points=[self.pos[0] + self.size[0] - 50, self.pos[1] + self.size[1] - 70,
                         self.pos[0] + self.size[0] - 50, self.pos[1] + self.size[1] - 70 - corner_size], width=line_width)

            # Bottom-left corner
            Line(points=[self.pos[0] + 50, self.pos[1] + 70,
                         self.pos[0] + 50 + corner_size, self.pos[1] + 70], width=line_width)
            Line(points=[self.pos[0] + 50, self.pos[1] + 70,
                         self.pos[0] + 50, self.pos[1] + 70 + corner_size], width=line_width)

            # Bottom-right corner
            Line(points=[self.pos[0] + self.size[0] - 50, self.pos[1] + 70,
                         self.pos[0] + self.size[0] - 50 - corner_size, self.pos[1] + 70], width=line_width)
            Line(points=[self.pos[0] + self.size[0] - 50, self.pos[1] + 70,
                         self.pos[0] + self.size[0] - 50, self.pos[1] + 70 + corner_size], width=line_width)

        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Dark background for camera preview
            Color(0.1, 0.1, 0.1, 1)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[20]
            )

            # Scanning animation overlay
            if self.scanning:
                Color(0.0, 0.58, 0.267, 0.3)
            else:
                Color(0.0, 0.58, 0.267, 0.1)

            self.overlay_rect = RoundedRectangle(
                pos=(self.pos[0] + 40, self.pos[1] + 60),
                size=(self.size[0] - 80, self.size[1] - 120),
                radius=[15]
            )

            # Corner indicators
            Color(0.0, 0.58, 0.267, 1)  # Solid green
            corner_size = 30
            line_width = 4

            # Calculate corner positions
            left = self.pos[0] + 50
            right = self.pos[0] + self.size[0] - 50
            top = self.pos[1] + self.size[1] - 70
            bottom = self.pos[1] + 70

            # Draw corner indicators
            # Top-left
            Line(points=[left, top, left + corner_size, top], width=line_width)
            Line(points=[left, top, left, top - corner_size], width=line_width)

            # Top-right
            Line(points=[right, top, right -
                 corner_size, top], width=line_width)
            Line(points=[right, top, right, top -
                 corner_size], width=line_width)

            # Bottom-left
            Line(points=[left, bottom, left +
                 corner_size, bottom], width=line_width)
            Line(points=[left, bottom, left, bottom +
                 corner_size], width=line_width)

            # Bottom-right
            Line(points=[right, bottom, right -
                 corner_size, bottom], width=line_width)
            Line(points=[right, bottom, right, bottom +
                 corner_size], width=line_width)

    def start_scanning(self):
        self.scanning = True
        self.update_graphics()
        # Stop scanning after 3 seconds (simulate scan completion)
        Clock.schedule_once(self.stop_scanning, 3)

    def stop_scanning(self, dt):
        self.scanning = False
        self.update_graphics()


class BorderedTextInput(BoxLayout):
    def __init__(self, hint_text='', **kwargs):
        # Remove text-specific kwargs to avoid conflicts
        text_kwargs = {}
        for key in ['hint_text']:
            if key in kwargs:
                text_kwargs[key] = kwargs.pop(key)

        super().__init__(**kwargs)
        self.orientation = 'vertical'

        # Store hint_text
        self.hint_text = hint_text

        # Create border background
        with self.canvas.before:
            Color(0.816, 0.835, 0.867, 1)  # #D0D5DD border color
            self.border_bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[34]
            )
            Color(1, 1, 1, 1)  # White inner background
            self.inner_bg = RoundedRectangle(
                pos=(self.pos[0] + 2, self.pos[1] + 2),
                size=(self.size[0] - 4, self.size[1] - 4),
                radius=[32]
            )

        # Create the TextInput with minimal styling
        self.text_input = TextInput(
            hint_text=hint_text,
            background_normal='',
            background_active='',
            background_color=[0, 0, 0, 0],  # Transparent
            foreground_color=[0, 0, 0, 1],  # Black text
            cursor_color=[0, 0, 0, 1],      # Black cursor
            hint_text_color=[0.7, 0.7, 0.7, 1],  # Gray hint
            padding=[15, 15, 15, 15],
            font_size=18,
            multiline=False
        )

        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.add_widget(self.text_input)

    def update_graphics(self, *args):
        self.border_bg.pos = self.pos
        self.border_bg.size = self.size
        self.inner_bg.pos = (self.pos[0] + 2, self.pos[1] + 2)
        self.inner_bg.size = (self.size[0] - 4, self.size[1] - 4)

    # Properties to make it behave like a TextInput
    @property
    def text(self):
        return self.text_input.text

    @text.setter
    def text(self, value):
        self.text_input.text = value

    def bind_text(self, callback):
        self.text_input.bind(text=callback)


class RoundedBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[20])
        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
