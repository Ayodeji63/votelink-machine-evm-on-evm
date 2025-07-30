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
import logging
from datetime import datetime
from utils.rfid import RFIDReader
from utils.fingerprint import FingerprintReader
from utils.camera import CameraHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rfid_voting.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RegistrationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize hardware components with updated RFIDReader
        self.rfid_reader = RFIDReader(callback=self.on_rfid_card_detected)
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
            size=(700, 520),  # Adjusted size for 7-inch display
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

    def cleanup_current_step(self):
        """Clean up current step before moving to next"""
        current_step_name = self.steps[self.current_step]

        if current_step_name == 'face' and self.camera_handler:
            # Remove camera widget from its parent before switching steps
            camera_widget = self.camera_handler.image_widget
            if camera_widget.parent:
                camera_widget.parent.remove_widget(camera_widget)

    def load_step(self):
        """Load the current registration step"""
        # Clean up previous step
        self.cleanup_current_step()

        # Clear widgets
        self.content_layout.clear_widgets()

        step = self.steps[self.current_step]
        print(f"[INFO   ] [Loading registration step] {step}")

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
            text='Hold your RFID card near the reader',
            font_size=16,
            color=[0.4, 0.439, 0.522, 1],
            size_hint_y=None,
            height=30,
            text_size=(None, None),
            halign='center'
        )
        self.content_layout.add_widget(instruction)

        # RFID visual
        rfid_visual = RoundedBox(
            orientation='vertical',
            padding=30,
            spacing=15,
            size_hint=(None, None),
            size=(350, 250),  # Increased height for button
            pos_hint={'center_x': 0.5}
        )

        with rfid_visual.canvas.before:
            Color(0.9, 0.95, 1.0, 1)  # Light blue background

        rfid_icon = Label(
            text='📡',
            font_size=60,
            size_hint_y=None,
            height=80
        )

        self.rfid_status = Label(
            text='Ready to scan RFID card',
            font_size=16,
            color=[0.4, 0.439, 0.522, 1],
            size_hint_y=None,
            height=40
        )

        # Manual scan button (for testing or backup)
        self.rfid_scan_btn = RoundedButton(
            text='Start Scanning',
            font_size=14,
            color=[1, 1, 1, 1],
            size_hint_y=None,
            height=45
        )
        self.rfid_scan_btn.bind(on_press=self.start_rfid_scan)

        rfid_visual.add_widget(rfid_icon)
        rfid_visual.add_widget(self.rfid_status)
        rfid_visual.add_widget(self.rfid_scan_btn)

        self.content_layout.add_widget(rfid_visual)

        # Update button
        self.next_btn.text = 'Next: Fingerprint'
        self.next_btn.disabled = True

        # Auto-start scanning
        self.start_rfid_scan()

    def on_rfid_card_detected(self, card_id):
        """Callback when RFID card is detected"""
        if self.rfid_scanning and self.steps[self.current_step] == 'rfid':
            # Use Clock.schedule_once to update UI from main thread
            Clock.schedule_once(
                lambda dt: self.handle_rfid_detection(card_id), 0)

    def handle_rfid_detection(self, card_id):
        """Handle RFID card detection (called from main thread)"""
        logger.info(f"RFID card detected: {card_id}")

        # Check if card is already registered
        if self.is_card_registered(card_id):
            self.rfid_status.text = 'This card is already registered!'
            self.rfid_status.color = [1, 0, 0, 1]  # Red color
            logger.warning(f"Card {card_id} is already registered")
            return

        # Card is new, proceed with registration
        self.registration_data['uid'] = card_id
        self.rfid_status.text = f'Card detected: {card_id}'
        self.rfid_status.color = [0, 0.7, 0, 1]  # Green color
        self.next_btn.disabled = False
        self.rfid_scanning = False
        self.rfid_reader.stop_continuous_scan()

        # Update button text
        self.rfid_scan_btn.text = 'Card Detected!'
        self.rfid_scan_btn.disabled = True

    def is_card_registered(self, card_id):
        """Check if card is already registered"""
        try:
            voters_file = 'data/voters.json'
            if os.path.exists(voters_file):
                with open(voters_file, 'r') as f:
                    voters = json.load(f)
                    return any(voter.get('uid') == card_id for voter in voters)
        except Exception as e:
            logger.error(f"Error checking card registration: {e}")
        return False

    def start_rfid_scan(self, instance=None):
        """Start RFID scanning process"""
        if self.rfid_scanning:
            return

        logger.info("Starting RFID scan")
        self.rfid_scanning = True
        self.rfid_status.text = 'Scanning for RFID card...'
        self.rfid_status.color = [0.4, 0.439, 0.522, 1]  # Default color
        self.rfid_scan_btn.text = 'Scanning...'
        self.rfid_scan_btn.disabled = True

        # Start continuous scanning
        self.rfid_reader.start_continuous_scan()

    def stop_rfid_scan(self):
        """Stop RFID scanning"""
        logger.info("Stopping RFID scan")
        self.rfid_scanning = False
        self.rfid_reader.stop_continuous_scan()
        self.rfid_scan_btn.text = 'Start Scanning'
        self.rfid_scan_btn.disabled = False

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
        if self.camera_handler is None:
            self.camera_handler = CameraHandler()

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

        # Camera container with proper centering
        camera_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=360  # Increased height for better layout
        )

        # Camera layout with proper dimensions
        camera_layout = RoundedBox(
            orientation='vertical',
            padding=20,
            spacing=15,
            size_hint=(None, None),
            size=(480, 340),  # Increased width and height for better proportions
            pos_hint={'center_x': 0.5}  # Center horizontally
        )

        with camera_layout.canvas.before:
            Color(0.1, 0.1, 0.1, 1)  # Dark background

        # Camera widget container to ensure proper centering
        camera_widget_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=240  # Fixed height for camera widget
        )

        # FIX: Remove the widget from its current parent before adding it
        camera_widget = self.camera_handler.image_widget
        if camera_widget.parent:
            camera_widget.parent.remove_widget(camera_widget)

        # Set proper camera widget properties
        camera_widget.size_hint = (1, 1)  # Fill the container
        camera_widget.allow_stretch = True
        camera_widget.keep_ratio = True
        camera_widget_container.add_widget(camera_widget)

        camera_layout.add_widget(camera_widget_container)

        # Status label with proper styling
        self.face_status = Label(
            text='Position your face in the frame',
            font_size=14,
            color=[1, 1, 1, 1],  # White text on dark background
            size_hint_y=None,
            height=30
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

        camera_container.add_widget(camera_layout)
        self.content_layout.add_widget(camera_container)

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
        """Update fingerprint status from fingerprint reader"""
        self.fp_status.text = message
        logger.info(f"Fingerprint status: {message}")

    def start_fingerprint_scan(self, instance):
        """Start fingerprint scanning process"""
        logger.info("Starting fingerprint scan")
        self.fp_status.text = 'Scanning fingerprint enrollment...'
        self.fp_scan_btn.disabled = True

        def enroll_and_update(dt):
            fingerprint_id = self.fingerprint_reader.enroll_finger()
            if fingerprint_id:
                self.registration_data['fingerprint_id'] = fingerprint_id
                self.fp_status.text = f'Fingerprint registered! ID: {fingerprint_id}'
                self.next_btn.disabled = False
                logger.info(
                    f"Fingerprint registered with ID: {fingerprint_id}")
            else:
                self.fp_status.text = 'Fingerprint scan failed. Please try again.'
                self.fp_scan_btn.disabled = False
                logger.warning("Fingerprint registration failed")

        Clock.schedule_once(enroll_and_update, 0.1)  # Run non-blocking

    def capture_face(self, instance):
        """Capture face photo"""
        # Update status with better visibility
        self.face_status.text = 'Capturing photo...'
        self.face_status.color = [1, 1, 0, 1]  # Yellow for processing
        self.capture_btn.disabled = True

        def do_capture(dt):
            try:
                # Capture face image
                image_path = self.camera_handler.capture_face(
                    self.registration_data['name'])
                if image_path:
                    self.registration_data['face_image'] = image_path
                    self.face_status.text = 'Photo captured successfully!'
                    self.face_status.color = [0, 1, 0, 1]  # Green for success
                    self.next_btn.disabled = False
                else:
                    self.face_status.text = 'Photo capture failed. Please try again.'
                    self.face_status.color = [1, 0, 0, 1]  # Red for error
                    self.capture_btn.disabled = False
            except Exception as e:
                self.face_status.text = f'Error: {str(e)}'
                self.face_status.color = [1, 0, 0, 1]  # Red for error
                self.capture_btn.disabled = False

        # Schedule the capture to run in the next frame
        Clock.schedule_once(do_capture, 0.1)

    def next_step(self, instance):
        """Move to next registration step"""
        current_step_name = self.steps[self.current_step]
        logger.info(f"Moving to next step from: {current_step_name}")

        # Validate current step
        if current_step_name == 'name':
            if not self.name_input.text.strip():
                self.show_error("Please enter your full name")
                return
            self.registration_data['name'] = self.name_input.text.strip()
            logger.info(f"Name registered: {self.registration_data['name']}")

        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.load_step()
        else:
            # Complete registration
            if self.save_registration():
                logger.info("Registration completed successfully")
                self.manager.current = 'verify'
            else:
                logger.error("Registration failed to save")

    def go_back(self, instance):
        """Go back to previous step or exit"""
        if self.current_step > 0:
            # Stop any ongoing scanning when going back
            if self.current_step == 1:  # RFID step
                self.stop_rfid_scan()

            self.current_step -= 1
            self.load_step()
            logger.info(f"Moved back to step: {self.steps[self.current_step]}")
        else:
            logger.info("Exiting registration, returning to welcome screen")
            self.cleanup()
            self.manager.current = 'welcome'

    def validate_registration_data(self):
        """Validate all registration data before saving"""
        errors = []

        if not self.registration_data.get('name', '').strip():
            errors.append("Name is required")

        if not self.registration_data.get('uid'):
            errors.append("RFID card scan is required")

        if not self.registration_data.get('fingerprint_id'):
            errors.append("Fingerprint registration is required")

        if not self.registration_data.get('face_image'):
            errors.append("Face photo is required")

        return errors

    def save_registration(self):
        """Save registration data to JSON file with validation"""
        logger.info("Saving registration data")

        # Validate data first
        errors = self.validate_registration_data()
        if errors:
            error_msg = "Registration incomplete:\n" + "\n".join(errors)
            self.show_error(error_msg)
            logger.error(f"Registration validation failed: {errors}")
            return False

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
            except Exception as e:
                logger.error(f"Error loading voters file: {e}")
                voters = []

        # Check for duplicate registration
        if any(voter.get('uid') == self.registration_data['uid'] for voter in voters):
            self.show_error("This RFID card is already registered!")
            logger.warning(
                f"Duplicate registration attempt for card: {self.registration_data['uid']}")
            return False

        # Add new voter
        voters.append(self.registration_data)

        # Save updated data
        try:
            with open(voters_file, 'w') as f:
                json.dump(voters, f, indent=2)

            logger.info(
                f"Registration saved successfully: {self.registration_data}")
            return True
        except Exception as e:
            logger.error(f"Error saving registration: {e}")
            self.show_error("Failed to save registration data")
            return False

    def get_registration_stats(self):
        """Get registration statistics"""
        try:
            voters_file = 'data/voters.json'
            if os.path.exists(voters_file):
                with open(voters_file, 'r') as f:
                    voters = json.load(f)
                    return {
                        'total_registered': len(voters),
                        'registered_today': len([
                            v for v in voters
                            if v.get('registration_date', '').startswith(
                                datetime.now().strftime('%Y-%m-%d')
                            )
                        ])
                    }
        except Exception as e:
            logger.error(f"Error getting registration stats: {e}")

        return {'total_registered': 0, 'registered_today': 0}

    def show_error(self, message):
        """Show error popup"""
        popup = Popup(
            title='Error',
            content=Label(text=message),
            size_hint=(0.6, 0.4)
        )
        popup.open()

    def on_leave(self, *args):
        """Called when leaving the screen"""
        logger.info("Leaving registration screen")
        # Clean up RFID scanning
        self.stop_rfid_scan()
        super().on_leave(*args)

    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up registration screen resources")
        try:
            self.stop_rfid_scan()
            self.rfid_reader.cleanup()
            # Clean up other resources as needed
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def update_bg(self, *args):
        """Update background rectangle"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
