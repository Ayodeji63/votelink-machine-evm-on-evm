from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from register import RegistrationScreen
from verify import VerificationScreen
from welcome import WelcomeScreen
from dashboard import DashboardScreen
from others.oldCodeElect import ElectionScreen  # ✅ Add this


class VoteLinkApp(App):
    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(WelcomeScreen(name='welcome'))
        self.sm.add_widget(VerificationScreen(name='verify'))
        self.sm.add_widget(RegistrationScreen(name='register'))
        self.sm.add_widget(DashboardScreen(name='dashboard'))
        self.sm.add_widget(ElectionScreen(name='election'))  # ✅ Add this

        return self.sm

    def go_to_election_screen(self):
        self.sm.current = 'election'
