from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.popup import Popup
from datetime import datetime, timedelta
import random


class ModernCard(FloatLayout):
    """Modern card component with shadow effect and animations"""

    def __init__(self, bg_color=(1, 1, 1, 1), border_radius=15, elevation=5, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.border_radius = border_radius
        self.elevation = elevation

        # Create shadow and background
        with self.canvas.before:
            # Shadow
            Color(0, 0, 0, 0.1)
            self.shadow = RoundedRectangle(
                pos=(self.x + self.elevation, self.y - self.elevation),
                size=self.size,
                radius=[self.border_radius]
            )

            # Background
            Color(*self.bg_color)
            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.border_radius]
            )

        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, *args):
        self.shadow.pos = (self.x + self.elevation, self.y - self.elevation)
        self.shadow.size = self.size
        self.bg.pos = self.pos
        self.bg.size = self.size

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Create ripple effect
            anim = Animation(elevation=8, duration=0.1)
            anim.bind(on_complete=lambda *args: Animation(elevation=5,
                      duration=0.1).start(self))
            anim.start(self)
        return super().on_touch_down(touch)


class StatusBadge(Label):
    """Status badge with dynamic colors"""

    def __init__(self, status="Live", **kwargs):
        super().__init__(**kwargs)
        self.status = status
        self.text = status
        self.font_size = dp(12)
        self.bold = True
        self.color = (1, 1, 1, 1)
        self.size_hint = (None, None)
        self.size = (dp(70), dp(25))
        self.halign = 'center'
        self.valign = 'middle'

        # Status colors
        status_colors = {
            'Live': (0.2, 0.8, 0.2, 1),      # Green
            'Not Live': (0.8, 0.2, 0.2, 1),  # Red
            'Pending': (0.9, 0.6, 0.1, 1),   # Orange
            'Completed': (0.2, 0.4, 0.8, 1)  # Blue
        }

        bg_color = status_colors.get(status, (0.5, 0.5, 0.5, 1))

        with self.canvas.before:
            Color(*bg_color)
            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(12)]
            )

        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size


class ElectionCard(ModernCard):
    """Enhanced election card with modern design"""

    def __init__(self, title, count, status="Live", location="", **kwargs):
        # Card colors based on status
        card_colors = {
            'Live': (0.133, 0.706, 0.298, 1),      # Green
            'Not Live': (0.3, 0.3, 0.3, 1),        # Dark gray
            'Pending': (0.8, 0.4, 0.2, 1),         # Orange
            'Completed': (0.2, 0.4, 0.8, 1)        # Blue
        }

        bg_color = card_colors.get(status, (0.5, 0.5, 0.5, 1))
        super().__init__(bg_color=bg_color, **kwargs)

        self.title = title
        self.count = count
        self.status = status
        self.location = location

        self.setup_card()

    def setup_card(self):
        # Main content layout
        content = BoxLayout(
            orientation='vertical',
            padding=[dp(20), dp(15)],
            spacing=dp(10),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(0.95, 0.9)
        )

        # Status badge container
        status_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30)
        )

        status_badge = StatusBadge(self.status)
        status_container.add_widget(Widget())  # Spacer
        status_container.add_widget(status_badge)

        # Title
        title_label = Label(
            text=self.title,
            font_size=dp(18),
            bold=True,
            color=(1, 1, 1, 1),
            halign='left',
            valign='top',
            size_hint_y=None,
            height=dp(50)
        )
        title_label.bind(size=title_label.setter('text_size'))

        # Location (if provided)
        location_label = Label(
            text=self.location,
            font_size=dp(14),
            color=(1, 1, 1, 0.8),
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=dp(25)
        )
        location_label.bind(size=location_label.setter('text_size'))

        # Voter count
        count_label = Label(
            text=f"Counted Voters: {self.count:,}",
            font_size=dp(16),
            color=(1, 1, 1, 1),
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=dp(30)
        )
        count_label.bind(size=count_label.setter('text_size'))

        # Arrow indicator
        arrow_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(25)
        )

        arrow_label = Label(
            text='→',
            font_size=dp(20),
            color=(1, 1, 1, 0.8),
            size_hint=(None, None),
            size=(dp(30), dp(25))
        )

        arrow_container.add_widget(Widget())  # Spacer
        arrow_container.add_widget(arrow_label)

        # Add all components
        content.add_widget(status_container)
        content.add_widget(title_label)
        if self.location:
            content.add_widget(location_label)
        content.add_widget(count_label)
        content.add_widget(arrow_container)

        self.add_widget(content)


class VotingSection(ModernCard):
    """Main voting section with input field"""

    def __init__(self, **kwargs):
        super().__init__(bg_color=(0.15, 0.25, 0.35, 1), **kwargs)
        self.setup_voting_section()

    def setup_voting_section(self):
        content = BoxLayout(
            orientation='vertical',
            padding=[dp(30), dp(25)],
            spacing=dp(20),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(0.95, 0.9)
        )

        # Header section
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60)
        )

        # Title
        title_label = Label(
            text='Presidential, Senate And House of\nRepresentative Election',
            font_size=dp(22),
            bold=True,
            color=(1, 1, 1, 1),
            halign='left',
            valign='middle'
        )
        title_label.bind(size=title_label.setter('text_size'))

        # Time remaining
        time_container = BoxLayout(
            orientation='vertical',
            size_hint_x=None,
            width=dp(150)
        )

        time_label = Label(
            text='Time Remaining:',
            font_size=dp(14),
            color=(0.7, 0.8, 0.9, 1),
            halign='right',
            size_hint_y=None,
            height=dp(20)
        )

        self.time_value = Label(
            text='02:45:30',
            font_size=dp(18),
            bold=True,
            color=(1, 1, 1, 1),
            halign='right',
            size_hint_y=None,
            height=dp(30)
        )

        time_container.add_widget(time_label)
        time_container.add_widget(self.time_value)

        header.add_widget(title_label)
        header.add_widget(time_container)

        # Input section
        input_container = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(70)
        )

        input_label = Label(
            text='Enter your Voters Identification Number (VIN) or National Identification Number (NIN)',
            font_size=dp(14),
            color=(0.7, 0.8, 0.9, 1),
            halign='left',
            size_hint_y=None,
            height=dp(25)
        )
        input_label.bind(size=input_label.setter('text_size'))

        self.vin_input = TextInput(
            hint_text='VIN or NIN',
            font_size=dp(16),
            multiline=False,
            size_hint_y=None,
            height=dp(45),
            background_color=(1, 1, 1, 0.1),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.7, 0.8, 0.9, 1),
            cursor_color=(1, 1, 1, 1),
            selection_color=(0.2, 0.6, 0.8, 0.5)
        )

        input_container.add_widget(input_label)
        input_container.add_widget(self.vin_input)

        # Vote button
        vote_button = Button(
            text='CAST VOTE',
            font_size=dp(16),
            bold=True,
            size_hint_y=None,
            height=dp(50),
            background_color=(0.2, 0.8, 0.2, 1),
            on_press=self.on_vote_pressed
        )

        content.add_widget(header)
        content.add_widget(input_container)
        content.add_widget(vote_button)

        self.add_widget(content)

        # Start timer
        Clock.schedule_interval(self.update_timer, 1)

    def update_timer(self, dt):
        """Update countdown timer"""
        # This would normally calculate actual time remaining
        # For demo purposes, we'll just show a static countdown
        pass

    def on_vote_pressed(self, instance):
        """Handle vote button press"""
        if not self.vin_input.text.strip():
            self.show_popup("Error", "Please enter your VIN or NIN")
            return

        self.show_popup("Success", "Vote recorded successfully!")
        self.vin_input.text = ""

    def show_popup(self, title, message):
        """Show popup message"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(None, None),
            size=(dp(400), dp(200))
        )
        popup.open()


class DashboardScreen(Screen):
    """Main dashboard screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.voter_name = "Olusanya Godwin"
        self.setup_ui()

    def setup_ui(self):
        # Background
        with self.canvas.before:
            Color(0.98, 0.98, 0.98, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_bg, size=self.update_bg)

        # Main scroll view
        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            scroll_type=['content']
        )

        # Main container
        main_layout = BoxLayout(
            orientation='vertical',
            padding=[dp(25), dp(20)],
            spacing=dp(25),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # Create sections
        self.create_header(main_layout)
        self.create_welcome_section(main_layout)
        self.create_voting_section(main_layout)
        self.create_races_section(main_layout)

        scroll.add_widget(main_layout)
        self.add_widget(scroll)

    def create_header(self, parent):
        """Create modern header with navigation"""
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(70),
            spacing=dp(20)
        )

        # Logo section
        logo_section = BoxLayout(
            orientation='horizontal',
            size_hint_x=0.25,
            spacing=dp(15)
        )

        # Logo badge
        logo_badge = Widget(
            size_hint=(None, None),
            size=(dp(45), dp(45))
        )

        with logo_badge.canvas.before:
            Color(0.133, 0.706, 0.298, 1)
            self.logo_bg = RoundedRectangle(
                pos=logo_badge.pos,
                size=logo_badge.size,
                radius=[dp(10)]
            )

        logo_label = Label(
            text='✓',
            font_size=dp(24),
            bold=True,
            color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        logo_badge.add_widget(logo_label)

        brand_label = Label(
            text='VoteChain',
            font_size=dp(24),
            bold=True,
            color=(0.133, 0.706, 0.298, 1),
            halign='left'
        )
        brand_label.bind(size=brand_label.setter('text_size'))

        logo_section.add_widget(logo_badge)
        logo_section.add_widget(brand_label)

        # Navigation
        nav_section = BoxLayout(
            orientation='horizontal',
            size_hint_x=0.5,
            spacing=dp(30)
        )

        nav_items = [
            ('Dashboard', True),
            ('Election', False),
            ('Statistics', False)
        ]

        for item, is_active in nav_items:
            nav_btn = Button(
                text=item,
                font_size=dp(16),
                color=(0.133, 0.706, 0.298, 1) if is_active else (
                    0.5, 0.5, 0.5, 1),
                background_color=(0, 0, 0, 0),
                size_hint_x=None,
                width=dp(100)
            )
            if is_active:
                nav_btn.bold = True
            nav_section.add_widget(nav_btn)

        # Profile section
        profile_section = BoxLayout(
            orientation='horizontal',
            size_hint_x=0.25,
            spacing=dp(15)
        )

        profile_badge = Widget(
            size_hint=(None, None),
            size=(dp(40), dp(40))
        )

        with profile_badge.canvas.before:
            Color(0.9, 0.9, 0.9, 1)
            self.profile_bg = RoundedRectangle(
                pos=profile_badge.pos,
                size=profile_badge.size,
                radius=[dp(20)]
            )

        profile_label = Label(
            text='OG',
            font_size=dp(16),
            bold=True,
            color=(0.4, 0.4, 0.4, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        profile_badge.add_widget(profile_label)
        profile_section.add_widget(Widget())  # Spacer
        profile_section.add_widget(profile_badge)

        header.add_widget(logo_section)
        header.add_widget(nav_section)
        header.add_widget(profile_section)

        parent.add_widget(header)

    def create_welcome_section(self, parent):
        """Create welcome message with animation"""
        welcome_label = Label(
            text=f'Welcome, {self.voter_name}',
            font_size=dp(32),
            bold=True,
            color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None,
            height=dp(60),
            halign='center'
        )

        # Add subtle animation
        anim = Animation(opacity=0, duration=0.1)
        anim += Animation(opacity=1, duration=0.5)
        anim.start(welcome_label)

        parent.add_widget(welcome_label)

    def create_voting_section(self, parent):
        """Create voting section"""
        voting_card = VotingSection(
            size_hint_y=None,
            height=dp(220)
        )
        parent.add_widget(voting_card)

    def create_races_section(self, parent):
        """Create electoral races section"""
        # Section title
        title_label = Label(
            text='Current Electoral Races',
            font_size=dp(28),
            bold=True,
            color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None,
            height=dp(50),
            halign='left'
        )
        title_label.bind(size=title_label.setter('text_size'))

        # Cards container
        cards_container = GridLayout(
            cols=3,
            size_hint_y=None,
            height=dp(200),
            spacing=dp(20)
        )

        # Election data
        elections = [
            {
                'title': 'Presidential\nElections',
                'count': 18,
                'status': 'Live',
                'location': ''
            },
            {
                'title': 'Senate\nElections',
                'count': 75567,
                'status': 'Not Live',
                'location': 'Anambra Central'
            },
            {
                'title': 'Gubernatorial\nElections',
                'count': 65890,
                'status': 'Not Live',
                'location': 'Lagos State'
            }
        ]

        for election in elections:
            card = ElectionCard(
                title=election['title'],
                count=election['count'],
                status=election['status'],
                location=election['location']
            )
            cards_container.add_widget(card)

        parent.add_widget(title_label)
        parent.add_widget(cards_container)

    def update_bg(self, *args):
        """Update background"""
        self.bg.pos = self.pos
        self.bg.size = self.size


class VoteChainApp(App):
    """Main application class"""

    def build(self):
        sm = ScreenManager()
        dashboard = DashboardScreen(name='dashboard')
        sm.add_widget(dashboard)
        return sm


if __name__ == '__main__':
    VoteChainApp().run()
