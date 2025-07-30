from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.uix.popup import Popup
from components import (
    RoundedButton,
    SecondaryButton,
    RoundedBox,
    BorderedTextInput,
    VirtualKeyboard
)
import json
import os
from datetime import datetime
from utils.rfid import RFIDReader
from utils.fingerprint import FingerprintReader
from utils.camera import CameraHandler


class RegistrationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize hardware components
        # Use Arduino-based RFID reader
        self.rfid_reader = RFIDReader(
            use_arduino=True, arduino_port='/dev/ttyUSB0')
        self.fingerprint_reader = FingerprintReader(
            logger=self.update_fingerprint_status)
        self.camera_handler = CameraHandler()

        # Registration data
        self.registration_data = {
            'uid': None,
            'name': '',
            'fingerprint_id': None,
            'face_image': None,
            'has_voted': False,
            'registration_date': None
        }

        # Registration steps
        self.current_step = 0
        self.steps = ['name', 'rfid', 'fingerprint', 'face', 'complete']

        # RFID scanning state
        self.rfid_scanning = False
        self.rfid_scan_event = None

        self.setup_ui()

    def setup_ui(self):
        with self.canvas.before:
            Color(0.956, 0.956, 0.956, 1)  # Light gray background
            self.bg_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[0])

        self.bind(size=self.update_bg, pos=self.update_bg)

        # Create a container that centers everything
        container = FloatLayout()

        self.main_layout = RoundedBox(
            orientation='vertical',
            padding=[30, 20, 30, 30],
            spacing=15,
            size_hint=(None, None),
            size=(700, 600),  # Adjusted size for 7-inch display
            # Center both horizontally and vertically
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        self.content_layout = BoxLayout(
            orientation='vertical',
            spacing=20
        )
        self.main_layout.add_widget(self.content_layout)

        self.button_layout = BoxLayout(
            orientation='horizontal',
            spacing=20,
            size_hint_y=None,
            height=60
        )

        self.back_btn = SecondaryButton(
            text='Back',
            font_size=18,
            color=[0.4, 0.439, 0.522, 1],
            size_hint_x=0.3
        )
        self.back_btn.bind(on_press=self.go_back)

        self.next_btn = RoundedButton(
            text='Next',
            font_size=18,
            color=[1, 1, 1, 1],
            size_hint_x=0.7
        )
        self.next_btn.bind(on_press=self.next_step)

        self.button_layout.add_widget(self.back_btn)
        self.button_layout.add_widget(self.next_btn)
        self.main_layout.add_widget(self.button_layout)

        container.add_widget(self.main_layout)
        self.add_widget(container)
        self.load_step()

    def load_step(self):
        """Load the current registration step"""
        self.content_layout.clear_widgets()
        step = self.steps[self.current_step]

        if step == 'name':
            self.load_name_step()
        elif step == 'rfid':
            self.load_rfid_step()
        elif step == 'fingerprint':
            self.load_fingerprint_step()
        elif step == 'face':
            self.load_face_step()
        elif step == 'complete':
            self.load_complete_step()

    def load_name_step(self):
        """Load name input step"""
        # Title
        title = Label(
            text='Enter Your Full Name',
            font_size=28,  # Reduced for smaller screen
            color=[0, 0.5, 0.2, 1],
            size_hint_y=None,
            height=40
        )
        self.content_layout.add_widget(title)

        # Instruction
        instruction = Label(
            text='Please enter your full name as it appears on your ID card',
            font_size=16,  # Reduced for smaller screen
            color=[0.4, 0.439, 0.522, 1],
            size_hint_y=None,
            height=30,
            text_size=(None, None),
            halign='center'
        )
        self.content_layout.add_widget(instruction)

        # Name input
        input_layout = BoxLayout(
            orientation='vertical',
            spacing=15,
            size_hint_y=None,
            height=180  # Adjusted height
        )

        name_label = Label(
            text="Full Name",
            halign='left',
            color=[0.4, 0.439, 0.522, 1],
            font_size=18,
            size_hint_y=None,
            height=25
        )
        name_label.bind(size=name_label.setter('text_size'))

        self.name_input = BorderedTextInput(
            hint_text='Enter your full name',
            size_hint_y=None,
            height=60
        )

        self.name_input.text_input.bind(focus=self.on_name_focus)

        input_layout.add_widget(name_label)
        input_layout.add_widget(self.name_input)

        self.content_layout.add_widget(input_layout)

        # Update button
        self.next_btn.text = 'Next: Scan RFID Card'

    def on_name_focus(self, instance, value):
        if value:
            self.show_virtual_keyboard(instance)

    def load_rfid_step(self):
        """Load RFID scanning step"""
        # Title
        title = Label(
            text='Scan Your RFID Card',
            font_size=28,
            color=[0, 0.5, 0.2, 1],
            size_hint_y=None,
            height=40
        )
        self.content_layout.add_widget(title)

        # Instruction
        instruction = Label(
            text='Hold your RFID card near the Arduino reader',
            font_size=16,
            color=[0.4, 0.439, 0.522, 1],
            size_hint_y=None,
            height=30,
            text_size=(None, None),
            halign='center'
        )
        self.content_layout.add_widget(instruction)

        # RFID visual with enhanced feedback
        rfid_visual = RoundedBox(
            orientation='vertical',
            padding=30,
            spacing=15,
            size_hint=(None, None),
            size=(350, 280),  # Increased height for more info
            pos_hint={'center_x': 0.5}
        )

        with rfid_visual.canvas.before:
            Color(0.9, 0.95, 1.0, 1)  # Light blue background

        rfid_icon = Label(
            text='📡',
            font_size=60,  # Reduced icon size
            size_hint_y=None,
            height=80
        )

        self.rfid_status = Label(
            text='Initializing RFID reader...',
            font_size=16,
            color=[0.4, 0.439, 0.522, 1],
            size_hint_y=None,
            height=40
        )

        # Connection status
        self.rfid_connection_status = Label(
            text='Checking Arduino connection...',
            font_size=14,
            color=[0.6, 0.6, 0.6, 1],
            size_hint_y=None,
            height=30
        )

        # Scan attempts counter
        self.scan_attempts = Label(
            text='',
            font_size=12,
            color=[0.5, 0.5, 0.5, 1],
            size_hint_y=None,
            height=25
        )

        # Manual retry button
        self.retry_btn = SecondaryButton(
            text='Retry Connection',
            font_size=14,
            size_hint_y=None,
            height=40,
            opacity=0  # Hidden initially
        )
        self.retry_btn.bind(on_press=self.retry_rfid_connection)

        rfid_visual.add_widget(rfid_icon)
        rfid_visual.add_widget(self.rfid_status)
        rfid_visual.add_widget(self.rfid_connection_status)
        rfid_visual.add_widget(self.scan_attempts)
        rfid_visual.add_widget(self.retry_btn)

        self.content_layout.add_widget(rfid_visual)

        # Start RFID scanning
        self.start_rfid_scan()

        # Update button
        self.next_btn.text = 'Next: Fingerprint'
        self.next_btn.disabled = True

    def start_rfid_scan(self):
        """Start RFID scanning process with enhanced feedback"""
        self.rfid_scanning = True
        self.scan_count = 0
        self.rfid_status.text = 'Connecting to Arduino...'

        # Check if Arduino is connected
        if hasattr(self.rfid_reader, 'use_arduino') and self.rfid_reader.use_arduino:
            if hasattr(self.rfid_reader, 'serial_connection') and self.rfid_reader.serial_connection:
                self.rfid_connection_status.text = '✅ Arduino connected successfully'
                self.rfid_connection_status.color = [0, 0.6, 0, 1]  # Green
                self.rfid_status.text = 'Ready! Please scan your RFID card...'
            else:
                self.rfid_connection_status.text = '❌ Arduino not connected'
                self.rfid_connection_status.color = [0.8, 0, 0, 1]  # Red
                self.rfid_status.text = 'Connection failed. Check Arduino connection.'
                self.retry_btn.opacity = 1
                return
        else:
            self.rfid_connection_status.text = '⚠️ Using simulation mode'
            self.rfid_connection_status.color = [0.8, 0.6, 0, 1]  # Orange
            self.rfid_status.text = 'Simulation mode active'

        # Start scanning
        self.rfid_scan_event = Clock.schedule_interval(self.check_rfid, 0.5)

    def check_rfid(self, dt):
        """Check for RFID card with enhanced feedback"""
        if not self.rfid_scanning:
            return False

        self.scan_count += 1
        self.scan_attempts.text = f'Scan attempts: {self.scan_count}'

        try:
            uid = self.rfid_reader.read_card()
            if uid:
                self.registration_data['uid'] = uid
                self.rfid_status.text = f'✅ Card detected!'
                self.rfid_connection_status.text = f'Card UID: {uid}'
                self.rfid_connection_status.color = [0, 0.6, 0, 1]  # Green
                self.scan_attempts.text = f'Success after {self.scan_count} attempts'
                self.next_btn.disabled = False
                self.rfid_scanning = False
                return False  # Stop scheduling
            else:
                # Update status to show it's actively scanning
                dots = '.' * ((self.scan_count % 3) + 1)
                self.rfid_status.text = f'Scanning for RFID card{dots}'

                # Show timeout after many attempts
                if self.scan_count > 60:  # 30 seconds at 0.5s intervals
                    self.rfid_status.text = 'Scan timeout. Please check your card.'
                    self.rfid_connection_status.text = 'Try placing card closer to reader'
                    self.rfid_connection_status.color = [
                        0.8, 0.6, 0, 1]  # Orange
                    self.retry_btn.opacity = 1
                    self.rfid_scanning = False
                    return False

        except Exception as e:
            self.rfid_status.text = f'Error: {str(e)}'
            self.rfid_connection_status.text = 'Please check Arduino connection'
            self.rfid_connection_status.color = [0.8, 0, 0, 1]  # Red
            self.retry_btn.opacity = 1
            self.rfid_scanning = False
            return False

        return True  # Continue checking

    def retry_rfid_connection(self, instance):
        """Retry RFID connection"""
        self.retry_btn.opacity = 0
        self.scan_count = 0
        self.rfid_status.text = 'Retrying connection...'
        self.rfid_connection_status.text = 'Reconnecting to Arduino...'
        self.rfid_connection_status.color = [0.4, 0.439, 0.522, 1]

        # Try to reconnect
        try:
            self.rfid_reader.cleanup()
            self.rfid_reader = RFIDReader(
                use_arduino=True, arduino_port='/dev/ttyUSB0')
            Clock.schedule_once(lambda dt: self.start_rfid_scan(), 1.0)
        except Exception as e:
            self.rfid_status.text = f'Reconnection failed: {str(e)}'
            self.retry_btn.opacity = 1

    def load_fingerprint_step(self):
        """Load fingerprint scanning step"""
        # Title
        title = Label(
            text='Register Your Fingerprint',
            font_size=28,
            color=[0, 0.5, 0.2, 1],
            size_hint_y=None,
            height=40
        )
        self.content_layout.add_widget(title)

        # Instruction
        instruction = Label(
            text='Place your finger on the sensor when prompted',
            font_size=16,
            color=[0.4, 0.439, 0.522, 1],
            size_hint_y=None,
            height=30,
            text_size=(None, None),
            halign='center'
        )
        self.content_layout.add_widget(instruction)

        # Fingerprint visual
        fp_visual = RoundedBox(
            orientation='vertical',
            padding=30,
            spacing=15,
            size_hint=(None, None),
            size=(350, 220),  # Adjusted for smaller screen
            pos_hint={'center_x': 0.5}
        )

        with fp_visual.canvas.before:
            Color(0.95, 0.95, 1.0, 1)  # Light purple background

        fp_icon = Label(
            text='🔒',
            font_size=60,
            size_hint_y=None,
            height=80
        )

        self.fp_status = Label(
            text='Ready to scan fingerprint',
            font_size=16,
            color=[0.4, 0.439, 0.522, 1],
            size_hint_y=None,
            height=40
        )

        # Scan button
        self.fp_scan_btn = RoundedButton(
            text='Start Fingerprint Scan',
            font_size=14,
            color=[1, 1, 1, 1],
            size_hint_y=None,
            height=45
        )
        self.fp_scan_btn.bind(on_press=self.start_fingerprint_scan)

        fp_visual.add_widget(fp_icon)
        fp_visual.add_widget(self.fp_status)
        fp_visual.add_widget(self.fp_scan_btn)

        self.content_layout.add_widget(fp_visual)

        # Update button
        self.next_btn.text = 'Next: Face Photo'
        self.next_btn.disabled = True

    def load_face_step(self):
        """Load face capture step"""
        # Title
        title = Label(
            text='Capture Your Photo',
            font_size=28,
            color=[0, 0.5, 0.2, 1],
            size_hint_y=None,
            height=40
        )
        self.content_layout.add_widget(title)

        # Instruction
        instruction = Label(
            text='Look directly at the camera and press capture',
            font_size=16,
            color=[0.4, 0.439, 0.522, 1],
            size_hint_y=None,
            height=30,
            text_size=(None, None),
            halign='center'
        )
        self.content_layout.add_widget(instruction)

        # Camera layout
        camera_layout = RoundedBox(
            orientation='vertical',
            padding=15,
            spacing=10,
            size_hint=(None, None),
            size=(400, 280),  # Adjusted for smaller screen
            pos_hint={'center_x': 0.5}
        )

        with camera_layout.canvas.before:
            Color(0.1, 0.1, 0.1, 1)  # Dark background

        # Live camera feed
        camera_widget = self.camera_handler.image_widget
        camera_widget.size_hint_y = None
        camera_widget.height = 180  # Reduced camera height
        camera_layout.add_widget(camera_widget)

        self.face_status = Label(
            text='Position your face in the frame',
            font_size=14,
            color=[1, 1, 1, 1],  # White text on dark background
            size_hint_y=None,
            height=25
        )
        camera_layout.add_widget(self.face_status)

        # Capture button
        self.capture_btn = RoundedButton(
            text='Capture Photo',
            font_size=16,
            color=[1, 1, 1, 1],
            size_hint_y=None,
            height=50
        )
        self.capture_btn.bind(on_press=self.capture_face)
        camera_layout.add_widget(self.capture_btn)

        self.content_layout.add_widget(camera_layout)

        # Update button
        self.next_btn.text = 'Complete Registration'
        self.next_btn.disabled = True

    def load_complete_step(self):
        """Load registration complete step"""
        # Title
        title = Label(
            text='Registration Complete!',
            font_size=28,
            color=[0, 0.5, 0.2, 1],
            size_hint_y=None,
            height=40
        )
        self.content_layout.add_widget(title)

        # Success message
        success_msg = Label(
            text='Your voter registration has been completed successfully.',
            font_size=16,
            color=[0.4, 0.439, 0.522, 1],
            size_hint_y=None,
            height=30,
            text_size=(None, None),
            halign='center'
        )
        self.content_layout.add_widget(success_msg)

        # Registration summary
        summary_layout = RoundedBox(
            orientation='vertical',
            padding=20,
            spacing=10,
            size_hint=(None, None),
            size=(500, 220),  # Adjusted for smaller screen
            pos_hint={'center_x': 0.5}
        )

        with summary_layout.canvas.before:
            Color(0.95, 1.0, 0.95, 1)  # Light green background

        summary_title = Label(
            text='Registration Summary',
            font_size=20,
            color=[0, 0.5, 0.2, 1],
            size_hint_y=None,
            height=30
        )

        summary_details = Label(
            text=f'Name: {self.registration_data.get("name", "N/A")}\n'
                 f'RFID UID: {self.registration_data.get("uid", "N/A")}\n'
                 f'Fingerprint ID: {self.registration_data.get("fingerprint_id", "N/A")}\n'
                 f'Face Image: {"Captured" if self.registration_data.get("face_image") else "N/A"}',
            font_size=14,
            color=[0.4, 0.439, 0.522, 1],
            halign='left'
        )
        summary_details.bind(size=summary_details.setter('text_size'))

        summary_layout.add_widget(summary_title)
        summary_layout.add_widget(summary_details)

        self.content_layout.add_widget(summary_layout)

        # Update buttons
        self.next_btn.text = 'Go to Voting'
        self.next_btn.disabled = False

    def show_virtual_keyboard(self, instance):
        """Show virtual keyboard for name input"""
        keyboard_popup = Popup(
            title='Virtual Keyboard',
            size_hint=(0.9, 0.7),
            auto_dismiss=False
        )

        keyboard = VirtualKeyboard(
            target_input=self.name_input,
            popup=keyboard_popup
        )

        keyboard_popup.content = keyboard
        keyboard_popup.open()

    def update_fingerprint_status(self, message):
        self.fp_status.text = message

    def start_fingerprint_scan(self, instance):
        """Start fingerprint scanning process"""
        self.fp_status.text = 'Scanning fingerprint enrollment...'
        self.fp_scan_btn.disabled = True

        def enroll_and_update(dt):
            fingerprint_id = self.fingerprint_reader.enroll_finger()
            if fingerprint_id:
                self.registration_data['fingerprint_id'] = fingerprint_id
                self.next_btn.disabled = False
            else:
                self.fp_scan_btn.disabled = False

        Clock.schedule_once(enroll_and_update, 0.1)  # Run non-blocking

    def fingerprint_scan_complete(self, dt):
        """Handle fingerprint scan completion"""
        fingerprint_id = self.fingerprint_reader.enroll_finger()
        if fingerprint_id:
            self.registration_data['fingerprint_id'] = fingerprint_id
            self.fp_status.text = f'Fingerprint registered successfully! ID: {fingerprint_id}'
            self.next_btn.disabled = False
        else:
            self.fp_status.text = 'Fingerprint scan failed. Please try again.'
            self.fp_scan_btn.disabled = False

    def capture_face(self, instance):
        """Capture face photo"""
        self.face_status.text = 'Capturing photo...'
        self.capture_btn.disabled = True

        # Capture face image
        image_path = self.camera_handler.capture_face(
            self.registration_data['name'])
        if image_path:
            self.registration_data['face_image'] = image_path
            self.face_status.text = 'Photo captured successfully!'
            self.next_btn.disabled = False
        else:
            self.face_status.text = 'Photo capture failed. Please try again.'
            self.capture_btn.disabled = False

    def next_step(self, instance):
        """Move to next registration step"""
        current_step_name = self.steps[self.current_step]

        # Validate current step
        if current_step_name == 'name':
            if not self.name_input.text.strip():
                self.show_error("Please enter your full name")
                return
            self.registration_data['name'] = self.name_input.text.strip()

        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.load_step()
        else:
            # Complete registration
            self.save_registration()
            self.manager.current = 'verify'

    def go_back(self, instance):
        """Go back to previous step or exit"""
        # Stop RFID scanning if active
        if hasattr(self, 'rfid_scan_event') and self.rfid_scan_event:
            self.rfid_scan_event.cancel()
            self.rfid_scanning = False

        if self.current_step > 0:
            self.current_step -= 1
            self.load_step()
        else:
            self.manager.current = 'welcome'

    def save_registration(self):
        """Save registration data to JSON file"""
        self.registration_data['registration_date'] = datetime.now(
        ).isoformat()

        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)

        # Load existing data
        voters_file = 'data/voters.json'
        voters = []
        if os.path.exists(voters_file):
            try:
                with open(voters_file, 'r') as f:
                    voters = json.load(f)
            except:
                voters = []

        # Add new voter
        voters.append(self.registration_data)

        # Save updated data
        with open(voters_file, 'w') as f:
            json.dump(voters, f, indent=2)

        print(f"Registration saved: {self.registration_data}")

    def show_error(self, message):
        """Show error popup"""
        popup = Popup(
            title='Error',
            content=Label(text=message),
            size_hint=(0.6, 0.4)
        )
        popup.open()

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def on_leave(self):
        """Cleanup when leaving screen"""
        # Stop RFID scanning
        if hasattr(self, 'rfid_scan_event') and self.rfid_scan_event:
            self.rfid_scan_event.cancel()
            self.rfid_scanning = False

        # Cleanup RFID reader
        if hasattr(self, 'rfid_reader'):
            self.rfid_reader.cleanup()
