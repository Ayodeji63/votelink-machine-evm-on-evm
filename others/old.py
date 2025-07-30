from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.clock import Clock
from datetime import datetime, timedelta
import json
import os


class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.voter_name = "Olusanya Godwin"  # This would be set from login
        self.setup_ui()

    def setup_ui(self):
        # Light gray background
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(size=self.update_bg, pos=self.update_bg)

        # Main scroll view
        scroll = ScrollView()

        # Main container
        main_layout = BoxLayout(
            orientation='vertical',
            padding=[40, 30, 40, 30],
            spacing=30,
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # Header with navigation
        self.create_header(main_layout)

        # Welcome message
        self.create_welcome_section(main_layout)

        # Main election card
        self.create_election_card(main_layout)

        # Current electoral races
        self.create_electoral_races(main_layout)

        scroll.add_widget(main_layout)
        self.add_widget(scroll)

    def create_header(self, parent):
        """Create header with VoteChain logo and navigation"""
        header_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=80,
            spacing=20
        )

        # Logo and title
        logo_layout = BoxLayout(
            orientation='horizontal',
            size_hint_x=0.3,
            spacing=15
        )

        # VoteChain logo (using checkmark icon)
        logo_container = BoxLayout(
            size_hint=(None, None),
            size=(50, 50),
            pos_hint={'center_y': 0.5}
        )

        with logo_container.canvas.before:
            Color(0.133, 0.706, 0.298, 1)  # Green background
            self.logo_bg = RoundedRectangle(
                pos=logo_container.pos,
                size=logo_container.size,
                radius=[10]
            )

        logo_label = Label(
            text='✓',
            font_size=30,
            color=[1, 1, 1, 1],
            bold=True
        )
        logo_container.add_widget(logo_label)

        title_label = Label(
            text='VoteChain',
            font_size=24,
            color=[0.133, 0.706, 0.298, 1],
            bold=True,
            halign='left',
            text_size=(None, None)
        )

        logo_layout.add_widget(logo_container)
        logo_layout.add_widget(title_label)

        # Navigation tabs
        nav_layout = BoxLayout(
            orientation='horizontal',
            size_hint_x=0.4,
            spacing=20
        )

        nav_items = ['Dashboard', 'Election', 'Statistics']
        for i, item in enumerate(nav_items):
            nav_btn = Button(
                text=item,
                font_size=16,
                color=[0.4, 0.4, 0.4, 1] if i != 0 else [
                    0.133, 0.706, 0.298, 1],
                background_color=[0, 0, 0, 0],  # Transparent background
                size_hint_x=None,
                width=100
            )
            if i == 0:  # Dashboard is active
                nav_btn.bold = True
            nav_layout.add_widget(nav_btn)

        # User profile section
        profile_layout = BoxLayout(
            orientation='horizontal',
            size_hint_x=0.3,
            spacing=15
        )

        # Time remaining (placeholder)
        time_label = Label(
            text='Time Remaining:',
            font_size=14,
            color=[0.6, 0.6, 0.6, 1],
            halign='right'
        )

        # Profile circle
        profile_container = BoxLayout(
            size_hint=(None, None),
            size=(40, 40),
            pos_hint={'center_y': 0.5}
        )

        with profile_container.canvas.before:
            Color(0.8, 0.8, 0.8, 1)  # Gray background
            self.profile_bg = RoundedRectangle(
                pos=profile_container.pos,
                size=profile_container.size,
                radius=[20]
            )

        profile_label = Label(
            text='OG',
            font_size=16,
            color=[0.4, 0.4, 0.4, 1],
            bold=True
        )
        profile_container.add_widget(profile_label)

        profile_layout.add_widget(time_label)
        profile_layout.add_widget(profile_container)

        header_layout.add_widget(logo_layout)
        header_layout.add_widget(nav_layout)
        header_layout.add_widget(profile_layout)

        parent.add_widget(header_layout)

    def create_welcome_section(self, parent):
        """Create welcome message section"""
        welcome_label = Label(
            text=f'Welcome, {self.voter_name}',
            font_size=32,
            color=[0.2, 0.2, 0.2, 1],
            bold=True,
            size_hint_y=None,
            height=60,
            halign='center'
        )
        parent.add_widget(welcome_label)

    def create_election_card(self, parent):
        """Create the main election card"""
        card_container = BoxLayout(
            size_hint_y=None,
            height=200,
            orientation='vertical'
        )

        # Card background
        card_layout = BoxLayout(
            orientation='vertical',
            padding=[40, 30, 40, 30],
            spacing=20
        )

        with card_layout.canvas.before:
            Color(0.15, 0.25, 0.35, 1)  # Dark blue-gray background
            self.card_bg = RoundedRectangle(
                pos=card_layout.pos,
                size=card_layout.size,
                radius=[15]
            )

        # Election title
        election_title = Label(
            text='Presidential, Senate And House of\nRepresentative Election',
            font_size=24,
            color=[1, 1, 1, 1],
            bold=True,
            size_hint_y=None,
            height=80,
            halign='left',
            text_size=(None, None)
        )

        # Input section
        input_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=60,
            spacing=20
        )

        # Input field container
        input_container = BoxLayout(
            orientation='vertical',
            size_hint_x=0.8
        )

        input_label = Label(
            text='Enter your Voters Identification Number (VIN) or National\nIdentification Number (NIN)',
            font_size=14,
            color=[0.6, 0.8, 0.9, 1],
            size_hint_y=None,
            height=35,
            halign='left',
            text_size=(600, None)
        )

        # Input field placeholder (you'll need to implement TextInput)
        input_field = Label(
            text='',
            size_hint_y=None,
            height=40
        )

        with input_field.canvas.before:
            Color(0.9, 0.9, 0.9, 0.1)  # Light transparent background
            self.input_bg = RoundedRectangle(
                pos=input_field.pos,
                size=input_field.size,
                radius=[5]
            )

        input_container.add_widget(input_label)
        input_container.add_widget(input_field)

        # Time remaining section
        time_container = BoxLayout(
            orientation='vertical',
            size_hint_x=0.2
        )

        time_title = Label(
            text='Time Remaining:',
            font_size=14,
            color=[0.6, 0.8, 0.9, 1],
            size_hint_y=None,
            height=35,
            halign='right'
        )

        time_value = Label(
            text='--:--:--',
            font_size=18,
            color=[1, 1, 1, 1],
            bold=True,
            size_hint_y=None,
            height=25,
            halign='right'
        )

        time_container.add_widget(time_title)
        time_container.add_widget(time_value)

        input_layout.add_widget(input_container)
        input_layout.add_widget(time_container)

        card_layout.add_widget(election_title)
        card_layout.add_widget(input_layout)

        card_container.add_widget(card_layout)
        parent.add_widget(card_container)

    def create_electoral_races(self, parent):
        """Create current electoral races section"""
        # Section title
        races_title = Label(
            text='Current Electoral Races',
            font_size=28,
            color=[0.2, 0.2, 0.2, 1],
            bold=True,
            size_hint_y=None,
            height=60,
            halign='left'
        )
        parent.add_widget(races_title)

        # Race cards container
        races_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=200,
            spacing=30
        )

        # Sample race data
        races_data = [
            {
                'title': 'Presidential elections',
                'voters': 18,
                'status': 'Live',
                'color': [0.133, 0.706, 0.298, 1],  # Green
                'bg_color': [0.133, 0.706, 0.298, 1]
            },
            {
                'title': 'Senate elections',
                'voters': 75567,
                'status': 'Not Live',
                'location': 'Anambra Centra',
                'color': [0.4, 0.4, 0.4, 1],  # Gray
                'bg_color': [0.3, 0.3, 0.3, 1]
            },
            {
                'title': 'Gubernational',
                'voters': 65890,
                'status': 'Not Live',
                'location': 'Lagos State',
                'color': [0.8, 0.4, 0.2, 1],  # Orange
                'bg_color': [0.8, 0.4, 0.2, 1]
            }
        ]

        for race in races_data:
            race_card = self.create_race_card(race)
            races_container.add_widget(race_card)

        parent.add_widget(races_container)

    def create_race_card(self, race_data):
        """Create individual race card"""
        card_layout = BoxLayout(
            orientation='vertical',
            padding=[25, 20, 25, 20],
            spacing=15,
            size_hint_x=0.33
        )

        with card_layout.canvas.before:
            Color(*race_data['bg_color'])
            self.race_card_bg = RoundedRectangle(
                pos=card_layout.pos,
                size=card_layout.size,
                radius=[15]
            )

        # Status badge
        status_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=30
        )

        status_badge = Label(
            text=race_data['status'],
            font_size=12,
            color=[1, 1, 1, 1],
            bold=True,
            size_hint=(None, None),
            size=(60, 25),
            halign='center'
        )

        with status_badge.canvas.before:
            if race_data['status'] == 'Live':
                Color(0.2, 0.8, 0.2, 1)  # Bright green for live
            else:
                Color(0.8, 0.2, 0.2, 1)  # Red for not live
            self.status_bg = RoundedRectangle(
                pos=status_badge.pos,
                size=status_badge.size,
                radius=[12]
            )

        status_container.add_widget(status_badge)
        status_container.add_widget(Label())  # Spacer

        # Race title
        race_title = Label(
            text=race_data['title'],
            font_size=20,
            color=[1, 1, 1, 1],
            bold=True,
            size_hint_y=None,
            height=50,
            halign='left',
            text_size=(200, None)
        )

        # Location (if available)
        if 'location' in race_data:
            location_label = Label(
                text=race_data['location'],
                font_size=14,
                color=[1, 1, 1, 0.8],
                size_hint_y=None,
                height=25,
                halign='left'
            )
        else:
            location_label = Label(
                text='',
                size_hint_y=None,
                height=25
            )

        # Voter count
        voter_count = Label(
            text=f'Counted Voters: {race_data["voters"]:,}',
            font_size=16,
            color=[1, 1, 1, 1],
            size_hint_y=None,
            height=30,
            halign='left'
        )

        # Arrow icon
        arrow_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=30
        )

        arrow_label = Label(
            text='→',
            font_size=24,
            color=[1, 1, 1, 1],
            size_hint=(None, None),
            size=(30, 30),
            halign='right'
        )

        arrow_container.add_widget(Label())  # Spacer
        arrow_container.add_widget(arrow_label)

        card_layout.add_widget(status_container)
        card_layout.add_widget(race_title)
        card_layout.add_widget(location_label)
        card_layout.add_widget(voter_count)
        card_layout.add_widget(arrow_container)

        return card_layout

    def update_bg(self, *args):
        """Update background rectangle"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def on_enter(self):
        """Called when screen is entered"""
        # Update any dynamic content when entering the screen
        pass

    def on_leave(self):
        """Called when screen is left"""
        # Clean up any scheduled events
        pass