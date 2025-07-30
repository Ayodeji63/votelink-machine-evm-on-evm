from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.app import App

from components import RoundedButton, SecondaryButton, RoundedBox

import json
import os
import cv2
from datetime import datetime
from utils.rfid import RFIDReader
from utils.fingerprint import FingerprintReader
from utils.camera import CameraHandler

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Install `face_recognition` with: pip install face_recognition")


class VerificationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize hardware components
        self.rfid_reader = RFIDReader(callback=self.on_rfid_card_detected)
        self.fingerprint_reader = FingerprintReader(
            logger=self.update_status)
        self.camera_handler = None

        # Verification data
        self.verified_user = None
        self.verification_steps = ['rfid', 'fingerprint', 'face', 'complete']
        self.current_step = 0
        self.verification_start_time = None

        self.setup_ui()

    def setup_ui(self):
        with self.canvas.before:
            Color(0.956, 0.956, 0.956, 1)  # Light gray background
            self.bg_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[0])

        self.bind(size=self.update_bg, pos=self.update_bg)

        # Create main container
        container = FloatLayout()

        self.main_layout = RoundedBox(
            orientation='vertical',
            padding=[40, 30, 40, 40],
            spacing=30,
            size_hint=(None, None),
            size=(850, 750),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        # Header section
        self.create_header()

        # Content area
        self.content_layout = BoxLayout(
            orientation='vertical',
            spacing=30
        )
        self.main_layout.add_widget(self.content_layout)

        # Button section
        self.create_buttons()

        container.add_widget(self.main_layout)
        self.add_widget(container)

        # Load initial step
        self.load_step()

    def create_header(self):
        """Create header with title and progress indicator"""
        header_layout = BoxLayout(
            orientation='vertical',
            spacing=10,
            size_hint_y=None,
            height=80
        )

        # Title
        title = Label(
            text='Voter Verification',
            font_size=32,
            color=[0, 0.5, 0.2, 1],
            size_hint_y=None,
            height=40
        )

        header_layout.add_widget(title)
        self.main_layout.add_widget(header_layout)

    def create_buttons(self):
        """Create navigation buttons"""
        self.button_layout = BoxLayout(
            orientation='horizontal',
            spacing=30,
            size_hint_y=None,
            height=80
        )

        self.back_btn = SecondaryButton(
            text='Back to Welcome',
            font_size=22,
            color=[0.4, 0.439, 0.522, 1],
            size_hint_x=0.4
        )
        self.back_btn.bind(on_press=self.go_back)

        self.action_btn = RoundedButton(
            text='Start Verification',
            font_size=24,
            color=[1, 1, 1, 1],
            size_hint_x=0.6
        )
        self.action_btn.bind(on_press=self.handle_action)

        self.button_layout.add_widget(self.back_btn)
        self.button_layout.add_widget(self.action_btn)
        self.main_layout.add_widget(self.button_layout)

    def load_step(self):
        """Load the current verification step"""
        self.content_layout.clear_widgets()

        step = self.verification_steps[self.current_step]

        if step == 'rfid':
            self.load_rfid_step()
        elif step == 'fingerprint':
            self.load_fingerprint_step()
        elif step == 'face':
            self.load_face_step()
        elif step == 'complete':
            self.load_complete_step()

    def load_rfid_step(self):
        """Load RFID verification step"""
        # Instruction
        instruction = Label(
            text='Please scan your RFID card to begin verification',
            font_size=24,
            color=[0.4, 0.439, 0.522, 1],
            size_hint_y=None,
            height=50,
            text_size=(None, None),
            halign='center'
        )
        self.content_layout.add_widget(instruction)

        # RFID visual container
        rfid_container = RoundedBox(
            orientation='vertical',
            padding=40,
            spacing=30,
            size_hint=(None, None),
            size=(400, 280),
            pos_hint={'center_x': 0.5}
        )

        with rfid_container.canvas.before:
            Color(0.95, 0.98, 1.0, 1)  # Very light blue background

        # Status label
        self.status_label = Label(
            text='Ready to scan RFID card',
            font_size=22,
            color=[0.2, 0.4, 0.8, 1],
            size_hint_y=None,
            height=30
        )

        # Card visual representation
        card_visual = RoundedBox(
            size_hint=(None, None),
            size=(320, 230),
            pos_hint={'center_x': 0.5}
        )

        with card_visual.canvas.before:
            Color(0.8, 0.8, 0.9, 1)  # Card color

        img = Image(
            source='assets/votersCard.jpg',
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=True
        )
        card_visual.add_widget(img)

        rfid_container.add_widget(self.status_label)
        rfid_container.add_widget(card_visual)

        self.content_layout.add_widget(rfid_container)

        # Update button
        self.action_btn.text = 'Start RFID Scan'
        self.action_btn.disabled = False

    def load_fingerprint_step(self):
        """Load fingerprint verification step"""
        # Show user info
        user_info = Label(
            text=f'Welcome back, {self.verified_user["name"]}!\nPlease verify your fingerprint',
            font_size=22,
            color=[0, 0.5, 0.2, 1],
            size_hint_y=None,
            height=80,
            halign='center'
        )
        user_info.bind(size=user_info.setter('text_size'))
        self.content_layout.add_widget(user_info)

        # Fingerprint visual container
        fp_container = RoundedBox(
            orientation='vertical',
            padding=40,
            spacing=30,
            size_hint=(None, None),
            size=(400, 260),
            pos_hint={'center_x': 0.5}
        )

        with fp_container.canvas.before:
            Color(0.98, 0.95, 1.0, 1)  # Very light purple background

        # Fingerprint icon
        fp_icon = Label(
            text='👆',
            font_size=80,
            size_hint_y=None,
            height=100
        )

        # Status label
        self.fp_status_label = Label(
            text='Ready to scan fingerprint',
            font_size=22,
            color=[0.5, 0.2, 0.8, 1],
            size_hint_y=None,
            height=40
        )

        # Fingerprint sensor visual
        sensor_visual = RoundedBox(
            size_hint=(None, None),
            size=(80, 80),
            pos_hint={'center_x': 0.5}
        )

        with sensor_visual.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # Dark sensor color

        sensor_label = Label(
            text='SENSOR',
            font_size=30,
            color=[1, 1, 1, 1]
        )
        sensor_visual.add_widget(sensor_label)

        fp_container.add_widget(fp_icon)
        fp_container.add_widget(self.fp_status_label)
        fp_container.add_widget(sensor_visual)

        self.content_layout.add_widget(fp_container)

        # Update button
        self.action_btn.text = 'Scan Fingerprint'
        self.action_btn.disabled = False

    def load_face_step(self):
        """Load face verification step with enlarged camera"""
        if self.camera_handler is None:
            self.camera_handler = CameraHandler()

        # Instruction
        instruction = Label(
            text='Please look directly at the camera for face verification',
            font_size=26,
            color=[0.4, 0.439, 0.522, 1],
            size_hint_y=None,
            height=40,
            halign='center'
        )
        self.content_layout.add_widget(instruction)

        # Camera container - increased size
        camera_container = RoundedBox(
            orientation='vertical',
            padding=20,
            spacing=25,
            size_hint=(None, None),
            size=(700, 520),  # Increased from (550, 420)
            pos_hint={'center_x': 0.5}
        )

        with camera_container.canvas.before:
            Color(0.1, 0.1, 0.1, 1)

        # Camera widget - handle parent properly and increase size
        camera_widget = self.camera_handler.image_widget

        # Remove from previous parent if it exists
        if camera_widget.parent:
            camera_widget.parent.remove_widget(camera_widget)

        camera_widget.size_hint_y = None
        camera_widget.height = 350  # Increased from 200
        camera_container.add_widget(camera_widget)

        # Status label for face verification
        self.face_status_label = Label(
            text='Ready for face verification',
            font_size=22,
            color=[0.2, 0.4, 0.8, 1],
            size_hint_y=None,
            height=50
        )
        camera_container.add_widget(self.face_status_label)

        self.content_layout.add_widget(camera_container)

        # Update button
        self.action_btn.text = 'Scan Face'
        self.action_btn.disabled = False

    def load_complete_step(self):
        """Load verification complete step"""
        # Success message
        success_title = Label(
            text=' Verification Successful!',
            font_size=36,
            color=[0, 0.7, 0.2, 1],
            size_hint_y=None,
            height=50
        )
        self.content_layout.add_widget(success_title)

        # Verification summary
        summary_container = RoundedBox(
            orientation='vertical',
            padding=25,
            spacing=25,
            size_hint=(None, None),
            size=(600, 280),
            pos_hint={'center_x': 0.5}
        )

        with summary_container.canvas.before:
            Color(0.95, 1.0, 0.95, 1)  # Light green background

        # User details
        user_name = Label(
            text=f'Voter: {self.verified_user["name"]}',
            font_size=36,
            color=[0, 0.5, 0.2, 1],
            size_hint_y=None,
            height=35
        )

        verification_time = Label(
            text=f'Verified at: {datetime.now().strftime("%H:%M:%S")}',
            font_size=22,
            color=[0.4, 0.439, 0.522, 1],
            size_hint_y=None,
            height=30
        )

        # Verification methods
        methods_verified = Label(
            text=' RFID Card Verified\n Fingerprint Verified\n Face Recognition Verified',
            font_size=14,
            color=[0, 0.5, 0, 1],
            size_hint_y=None,
            height=80,
            halign='left'
        )
        methods_verified.bind(size=methods_verified.setter('text_size'))

        # Voting status
        voting_status = Label(
            text=f'Voting Status: {"Already Voted" if self.verified_user.get("has_voted", False) else "Ready to Vote"}',
            font_size=22,
            color=[0.8, 0.4, 0, 1] if self.verified_user.get(
                "has_voted", False) else [0, 0.5, 0.2, 1],
            size_hint_y=None,
            height=35
        )

        summary_container.add_widget(user_name)
        summary_container.add_widget(verification_time)
        summary_container.add_widget(methods_verified)
        summary_container.add_widget(voting_status)

        self.content_layout.add_widget(summary_container)

        # Update button based on voting status
        if self.verified_user.get("has_voted", False):
            self.action_btn.text = 'Already Voted - Return'
            self.action_btn.disabled = False
        else:
            self.action_btn.text = 'Proceed to Voting'
            self.action_btn.disabled = False

    def handle_action(self, instance):
        """Handle action button press based on current step"""
        step = self.verification_steps[self.current_step]

        if step == 'rfid':
            self.start_rfid_verification()
        elif step == 'fingerprint':
            self.start_fingerprint_verification()
        elif step == 'face':
            self.start_face_verification()
        elif step == 'complete':
            if self.verified_user.get("has_voted", False):
                self.go_back(instance)
            else:
                self.go_to_voting()

    def start_rfid_verification(self):
        """Start RFID verification process"""
        self.verification_start_time = datetime.now()
        self.status_label.text = 'Scanning for RFID card...'
        self.action_btn.disabled = True
        Clock.schedule_interval(self.check_rfid, 0.5)

    def check_rfid(self, dt):
        """Check for RFID card"""
        uid = self.rfid_reader.read_card()
        # uid = "46OCMOC7"
        if uid:
            self.status_label.text = f'Card detected: {uid}'
            self.verified_user = self.find_user_by_uid(uid)

            if not self.verified_user:
                self.show_error_popup(
                    "User not found", "This RFID card is not registered. Please register first.")
                self.status_label.text = 'Card not registered'
                self.action_btn.disabled = False
                return False

            # Move to next step
            self.current_step += 1
            Clock.schedule_once(lambda dt: self.load_step(), 1.0)
            return False  # Stop scheduling
        return True  # Continue checking

    def start_fingerprint_verification(self):
        """Start fingerprint verification"""
        self.fp_status_label.text = 'Place your finger on the sensor...'
        self.action_btn.disabled = True

        def verify_fingerprint(dt):
            fid, confidence = self.fingerprint_reader.search_finger()
            expected_id = self.verified_user.get('fingerprint_id')

            if fid is not None and str(fid) == str(expected_id):
                self.fp_status_label.text = f'Fingerprint verified! (Confidence: {confidence})'
                # Move to next step
                self.current_step += 1
                Clock.schedule_once(lambda dt: self.load_step(), 1.5)
            else:
                self.show_error_popup(
                    "Fingerprint Mismatch", "Fingerprint verification failed. Please try again.")
                self.fp_status_label.text = 'Fingerprint mismatch - try again'
                self.action_btn.disabled = False

        Clock.schedule_once(verify_fingerprint, 0.1)

    def start_face_verification(self):
        """Start face verification"""
        if not FACE_RECOGNITION_AVAILABLE:
            self.show_error_popup(
                "Face Recognition Unavailable", "Face recognition library not installed.")
            return

        self.face_status_label.text = 'Analyzing face... Please look at camera'
        self.action_btn.disabled = True

        def verify_face(dt):
            frame = self.camera_handler.frame
            if frame is None:
                self.show_error_popup(
                    "Camera Error", "Unable to access camera. Please try again.")
                self.face_status_label.text = 'Camera error - try again'
                self.action_btn.disabled = False
                return

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(
                rgb_frame, face_locations)

            if not face_encodings:
                self.show_error_popup(
                    "No Face Detected", "No face detected in camera. Please position yourself properly.")
                self.face_status_label.text = 'No face detected - try again'
                self.action_btn.disabled = False
                return

            known_encoding = self.camera_handler.face_encodings_db.get(
                self.verified_user['name'], {}).get('encodings')

            if known_encoding:
                results = face_recognition.compare_faces(
                    known_encoding, face_encodings[0])
                if results[0]:
                    self.face_status_label.text = 'Face verified successfully!'
                    # Move to final step
                    self.current_step += 1
                    Clock.schedule_once(lambda dt: self.load_step(), 1.5)
                else:
                    self.show_error_popup(
                        "Face Mismatch", "Face verification failed. This doesn't match your registered face.")
                    self.face_status_label.text = 'Face mismatch - try again'
                    self.action_btn.disabled = False
            else:
                self.show_error_popup(
                    "No Face Data", "No face data found for this user. Please re-register.")
                self.face_status_label.text = 'No face data found'
                self.action_btn.disabled = False

        Clock.schedule_once(verify_face, 1.0)

    def on_rfid_card_detected(self, card_id):
        """Callback when RFID card is detected"""
        if self.rfid_scanning and self.steps[self.current_step] == 'rfid':
            # Use Clock.schedule_once to update UI from main thread
            Clock.schedule_once(
                lambda dt: self.handle_rfid_detection(card_id), 0)

    def find_user_by_uid(self, uid):
        """Find user by RFID UID - Enhanced with better debugging"""
        if not os.path.exists('data/voters.json'):
            print("voters.json file not found!")
            return None

        try:
            with open('data/voters.json', 'r') as f:
                voters = json.load(f)

            print(f"Looking for UID: {uid}")
            print(f"Total voters in database: {len(voters)}")

            for voter in voters:
                stored_uid = voter.get('uid')
                print(
                    f"Checking voter: {voter.get('name', 'Unknown')} with UID: {stored_uid}")

                if stored_uid == uid:
                    print(f"Match found! Voter: {voter.get('name')}")
                    return voter

            print(f"No match found for UID: {uid}")

        except Exception as e:
            print(f"Error loading voter data: {e}")

        return None

    def go_to_voting(self):
        """Navigate to voting screen"""
        if hasattr(self.manager, 'get_screen'):
            try:
                # 'voting' must match the name you used in ScreenManager
                voting_screen = self.manager.get_screen('voting')
                voting_screen.set_verified_user(
                    self.verified_user)  # Pass verified user
            except Exception as e:
                print(f"Error passing user to voting screen: {e}")

        # or 'voting' if that's the correct screen name
        app = App.get_running_app()
        app.verified_user = self.verified_user  # Store globally if needed

        self.manager.current = 'dashboard'

    def go_back(self, instance):
        """Go back to welcome screen"""
        self.reset_verification()
        self.manager.current = 'welcome'

    def reset_verification(self):
        """Reset verification state"""
        self.current_step = 0
        self.verified_user = None
        self.verification_start_time = None

        # Clean up camera if initialized
        if self.camera_handler:
            try:
                self.camera_handler.release()
                self.camera_handler = None
            except:
                pass

    def show_error_popup(self, title, message):
        """Show error popup with custom title"""
        popup_content = BoxLayout(
            orientation='vertical', spacing=25, padding=20)

        message_label = Label(
            text=message,
            font_size=22,
            color=[0.2, 0.2, 0.2, 1],
            text_size=(300, None),
            halign='center'
        )

        ok_button = RoundedButton(
            text='OK',
            size_hint=(None, None),
            size=(100, 40),
            pos_hint={'center_x': 0.5}
        )

        popup_content.add_widget(message_label)
        popup_content.add_widget(ok_button)

        popup = Popup(
            title=title,
            content=popup_content,
            size_hint=(0.7, 0.5),
            auto_dismiss=False
        )

        ok_button.bind(on_press=popup.dismiss)
        popup.open()

    def update_status(self, message):
        """Update status message - called by hardware components"""
        if hasattr(self, 'status_label'):
            self.status_label.text = message
        elif hasattr(self, 'fp_status_label'):
            self.fp_status_label.text = message
        elif hasattr(self, 'face_status_label'):
            self.face_status_label.text = message

    def update_bg(self, *args):
        """Update background rectangle"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def on_enter(self):
        """Called when screen is entered"""
        self.reset_verification()
        self.load_step()

    def on_leave(self):
        """Called when screen is left"""
        # Stop any running clocks
        Clock.unschedule(self.check_rfid)

        # Clean up resources
        if self.camera_handler:
            try:
                self.camera_handler.release()
                self.camera_handler = None
            except:
                pass
