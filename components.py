from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
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


class KeyboardButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = [0, 0, 0, 0]  # Transparent

        # Draw the button background
        with self.canvas.before:
            Color(1, 1, 1, 1)  # White background
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[10]
            )
            # Border
            Color(0.816, 0.835, 0.867, 1)  # Gray border
            self.border_rect = Line(
                rounded_rectangle=(
                    self.pos[0], self.pos[1], self.size[0], self.size[1], 10),
                width=2
            )

        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_rect.rounded_rectangle = (
            self.pos[0], self.pos[1], self.size[0], self.size[1], 10)


class VirtualKeyboard(BoxLayout):
    def __init__(self, target_input=None, popup=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 20

        self.target_input = target_input
        self.popup = popup
        self.shift_active = False
        self.caps_lock = False

        # Text display
        self.text_display = BorderedTextInput(
            size_hint_y=None,
            height=60
        )
        if target_input:
            self.text_display.text = target_input.text
        self.add_widget(self.text_display)

        # Keyboard layout
        self.setup_keyboard()

        # Control buttons
        control_layout = BoxLayout(
            orientation='horizontal',
            spacing=10,
            size_hint_y=None,
            height=50
        )

        clear_btn = SecondaryButton(
            text='Clear',
            size_hint_x=0.3
        )
        clear_btn.bind(on_press=self.clear_text)

        space_btn = KeyboardButton(
            text='Space',
            color=[0.4, 0.439, 0.522, 1],
            size_hint_x=0.4
        )
        space_btn.bind(on_press=lambda x: self.add_character(' '))

        done_btn = RoundedButton(
            text='Done',
            color=[1, 1, 1, 1],
            size_hint_x=0.3
        )
        done_btn.bind(on_press=self.done_typing)

        control_layout.add_widget(clear_btn)
        control_layout.add_widget(space_btn)
        control_layout.add_widget(done_btn)

        self.add_widget(control_layout)

    def setup_keyboard(self):
        """Setup the keyboard layout"""
        # Row 1: Numbers
        row1 = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        self.create_key_row(row1)

        # Row 2: QWERTY
        row2 = ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P']
        self.create_key_row(row2)

        # Row 3: ASDF
        row3 = ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L']
        self.create_key_row(row3)

        # Row 4: ZXCV with special keys
        row4_layout = BoxLayout(
            orientation='horizontal',
            spacing=5,
            size_hint_y=None,
            height=50
        )

        # Shift key
        shift_btn = SecondaryButton(
            text='⇧ Shift',
            size_hint_x=1.5,
            color=[0.4, 0.439, 0.522, 1]
        )
        shift_btn.bind(on_press=self.toggle_shift)
        row4_layout.add_widget(shift_btn)

        # Letters
        row4 = ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
        for char in row4:
            btn = KeyboardButton(
                text=char,
                color=[0.4, 0.439, 0.522, 1]
            )
            btn.bind(on_press=lambda x, c=char: self.add_character(c))
            row4_layout.add_widget(btn)

        # Backspace key
        backspace_btn = SecondaryButton(
            text='Backspace',
            size_hint_x=1.5,
            color=[0.4, 0.439, 0.522, 1]
        )
        backspace_btn.bind(on_press=self.backspace)
        row4_layout.add_widget(backspace_btn)

        self.add_widget(row4_layout)

    def create_key_row(self, keys):
        """Create a row of keyboard keys"""
        layout = BoxLayout(
            orientation='horizontal',
            spacing=5,
            size_hint_y=None,
            height=50
        )

        for key in keys:
            btn = KeyboardButton(
                text=key,
                color=[0.4, 0.439, 0.522, 1]
            )
            btn.bind(on_press=lambda x, k=key: self.add_character(k))
            layout.add_widget(btn)

        self.add_widget(layout)

    def add_character(self, char):
        """Add character to text display"""
        current_text = self.text_display.text

        # Apply case logic
        if char.isalpha():
            if self.shift_active or self.caps_lock:
                char = char.upper()
            else:
                char = char.lower()

        self.text_display.text = current_text + char

        # Reset shift after use (but not caps lock)
        if self.shift_active and not self.caps_lock:
            self.shift_active = False

    def toggle_shift(self, instance):
        """Toggle shift/caps lock"""
        if self.shift_active:
            # If shift is active, make it caps lock
            self.caps_lock = True
            self.shift_active = False
            instance.text = 'Caps'
            instance.color = [0.0, 0.58, 0.267, 1]  # Green when active
        elif self.caps_lock:
            # If caps lock is active, turn off
            self.caps_lock = False
            instance.text = 'Shift'
            instance.color = [0.4, 0.439, 0.522, 1]  # Normal color
        else:
            # Activate shift
            self.shift_active = True
            instance.text = 'Shift'
            instance.color = [0.0, 0.58, 0.267, 1]  # Green when active

    def backspace(self, instance):
        """Remove last character"""
        current_text = self.text_display.text
        if current_text:
            self.text_display.text = current_text[:-1]

    def clear_text(self, instance):
        """Clear all text"""
        self.text_display.text = ''

    def done_typing(self, instance):
        """Finish typing and close keyboard"""
        # Update the target input with the text
        if self.target_input:
            self.target_input.text = self.text_display.text

        # Close the popup
        if self.popup:
            self.popup.dismiss()


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

    def bind_focus(self, callback):
        self.text_input.bind(focus=callback)

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
