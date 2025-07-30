from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.animation import Animation
from components import RoundedButton
from kivy.uix.image import Image
import os


class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_ui()

    def setup_ui(self):
        # Green background like the VoteLink brand
        with self.canvas.before:
            Color(0.133, 0.706, 0.298, 1)  # VoteLink green color
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(size=self.update_bg, pos=self.update_bg)

        # Main container - full width
        main_layout = BoxLayout(
            orientation='vertical',
            padding=[80, 100, 80, 100],
            spacing=60
        )

        # Logo and title section
        header_layout = BoxLayout(
            orientation='vertical',
            spacing=20,
            size_hint_y=None,
            height=200
        )

        # VoteLink title
        title = Label(
            text='VOTELINK',
            font_size=72,
            color=[1, 1, 1, 1],  # White text
            bold=True,
            size_hint_y=None,
            height=80
        )

        img = Image(
            source='assets/bg.jpg',
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=True
        )
        # Tagline
        tagline = Label(
            text='Secure Digital Voting Made Simple',
            font_size=24,
            color=[1, 1, 1, 0.9],  # Slightly transparent white
            size_hint_y=None,
            height=40
        )

        header_layout.add_widget(tagline)
        header_layout.add_widget(img)

        # Button section
        button_layout = BoxLayout(
            orientation='horizontal',
            spacing=40,
            size_hint_y=None,
            height=80,
            pos_hint={'center_x': 0.5}
        )

        # Register button
        self.register_btn = RoundedButton(
            text='Register',
            font_size=24,
            color=[0.133, 0.706, 0.298, 1],  # Green text on white button
            size_hint_x=0.5,
            size_hint_y=1
        )

        # Override button colors to make it white with green text
        with self.register_btn.canvas.before:
            Color(1, 1, 1, 1)  # White background

        self.register_btn.bind(on_press=self.go_to_register)

        # Verify & Vote button
        self.verify_btn = RoundedButton(
            text='Verify & Vote',
            font_size=24,
            color=[0.133, 0.706, 0.298, 1],  # Green text on white button
            size_hint_x=0.5,
            size_hint_y=1
        )

        # Override button colors to make it white with green text
        with self.verify_btn.canvas.before:
            Color(1, 1, 1, 1)  # White background

        self.verify_btn.bind(on_press=self.go_to_verify)

        button_layout.add_widget(self.register_btn)
        button_layout.add_widget(self.verify_btn)

        # Add spacers to push content to center
        spacer_top = Label(text='')
        spacer_bottom = Label(text='')

        main_layout.add_widget(spacer_top)
        main_layout.add_widget(header_layout)
        main_layout.add_widget(button_layout)
        main_layout.add_widget(spacer_bottom)

        self.add_widget(main_layout)

    def go_to_register(self, instance):
        """Navigate to registration screen"""
        self.add_button_animation(instance)
        Clock.schedule_once(lambda dt: setattr(
            self.manager, 'current', 'register'), 0.2)

    def go_to_verify(self, instance):
        """Navigate to verification screen"""
        self.add_button_animation(instance)
        Clock.schedule_once(lambda dt: setattr(
            self.manager, 'current', 'verify'), 0.2)

    def add_button_animation(self, button):
        """Add press animation to buttons"""
        # Scale down animation
        anim1 = Animation(
            size=(button.size[0] * 0.95, button.size[1] * 0.95), duration=0.1)
        # Scale back up animation
        anim2 = Animation(size=button.size, duration=0.1)
        # Chain animations
        anim1.bind(on_complete=lambda *args: anim2.start(button))
        anim1.start(button)

    def update_bg(self, *args):
        """Update background rectangle"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
