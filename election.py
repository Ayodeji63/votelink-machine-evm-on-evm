import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
import json
import threading
import qrcode
import io
from PIL import Image as PILImage
from kivy.core.image import Image as CoreImage
import time
import hashlib
import os
import datetime
from datetime import datetime
import requests
import json as json_lib
import secrets

# Import the fingerprint reader
try:
    from utils.fingerprint import FingerprintReader
except ImportError:
    print("Warning: Fingerprint reader not available")
    FingerprintReader = None

# Paths - ensure directory exists
VOTES_DIR = 'votes'
COMMIT_FILE = os.path.join(VOTES_DIR, 'commit.json')
SECRETS_FILE = os.path.join(VOTES_DIR, 'secrets.json')

# Create votes directory if it doesn't exist
os.makedirs(VOTES_DIR, exist_ok=True)


class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.bind(size=self.update_graphics, pos=self.update_graphics)

    def update_graphics(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.2, 0.8, 0.4, 1)  # Green color
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])


class CandidateCard(BoxLayout):
    def __init__(self, candidate_name, party_name, candidate_id, vote_callback,
                 candidate_image=None, party_image=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(13)
        self.padding = dp(17)
        self.candidate_id = candidate_id
        self.vote_callback = vote_callback

        # Add shadow effect
        with self.canvas.before:
            Color(0, 0, 0, 0.1)  # Shadow
            RoundedRectangle(pos=(self.x + dp(5), self.y - dp(5)),
                             size=self.size, radius=[dp(15)])
            Color(1, 1, 1, 1)  # White background
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])

        self.bind(size=self.update_shadow, pos=self.update_shadow)

        # Party info section with image
        party_layout = BoxLayout(
            orientation='horizontal', size_hint_y=0.25, spacing=dp(9))

        # Party image
        if party_image and os.path.exists(party_image):
            party_img = Image(source=party_image,
                              size_hint_x=0.3, allow_stretch=True)
        else:
            # Placeholder for party image
            party_img = Widget(size_hint_x=0.3)
            with party_img.canvas:
                Color(0.8, 0.8, 0.8, 1)
                RoundedRectangle(pos=party_img.pos,
                                 size=party_img.size, radius=[dp(5)])

        party_layout.add_widget(party_img)
        party_layout.add_widget(Label(text=party_name, font_size=dp(15),
                                      color=(0.2, 0.2, 0.2, 1), bold=True,
                                      text_size=(None, None), halign='left'))
        self.add_widget(party_layout)

        # Candidate section with large image
        candidate_layout = BoxLayout(
            orientation='vertical', size_hint_y=0.5, spacing=dp(9))

        # Candidate image (large and prominent)
        if candidate_image and os.path.exists(candidate_image):
            candidate_img = Image(source=candidate_image,
                                  size_hint_y=0.8, allow_stretch=True)
        else:
            # Placeholder for candidate image
            candidate_img = Widget(size_hint_y=0.8)
            with candidate_img.canvas:
                Color(0.9, 0.9, 0.9, 1)
                RoundedRectangle(pos=candidate_img.pos,
                                 size=candidate_img.size, radius=[dp(10)])

        candidate_layout.add_widget(candidate_img)
        candidate_layout.add_widget(Label(text=candidate_name, font_size=dp(17),
                                          color=(0.1, 0.1, 0.1, 1), bold=True,
                                          size_hint_y=0.2))
        self.add_widget(candidate_layout)

        # Vote button
        vote_btn = RoundedButton(text='Vote', size_hint_y=0.15,
                                 font_size=dp(15), bold=True)
        vote_btn.bind(on_press=self.on_vote_click)
        self.add_widget(vote_btn)

    def update_shadow(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 0, 0, 0.1)  # Shadow
            RoundedRectangle(pos=(self.x + dp(5), self.y - dp(5)),
                             size=self.size, radius=[dp(15)])
            Color(1, 1, 1, 1)  # White background
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])

    def on_vote_click(self, instance):
        self.vote_callback(self.candidate_id)


class VoteConfirmationPopup(Popup):
    def __init__(self, candidate_id, candidate_name, on_confirm, **kwargs):
        super().__init__(**kwargs)
        self.candidate_id = candidate_id
        self.candidate_name = candidate_name
        self.on_confirm = on_confirm
        self.title = 'Confirm Your Vote'
        self.size_hint = (0.8, 0.4)
        self.auto_dismiss = False

        content = BoxLayout(orientation='vertical',
                            spacing=dp(20), padding=dp(20))

        # White background for popup content
        with content.canvas.before:
            Color(1, 1, 1, 1)  # White background
            Rectangle(pos=content.pos, size=content.size)
        content.bind(size=self.update_content_bg, pos=self.update_content_bg)

        content.add_widget(Label(text=f'Are you sure you want to vote for {self.candidate_name}?',
                                 font_size=dp(18), text_size=(dp(350), None), halign='center',
                                 color=(0.2, 0.2, 0.2, 1)))

        button_layout = BoxLayout(
            orientation='horizontal', spacing=dp(20), size_hint_y=0.3)

        confirm_btn = RoundedButton(text='Confirm Vote', size_hint_x=0.5)
        confirm_btn.bind(on_press=self.confirm_vote)

        cancel_btn = Button(text='Cancel', size_hint_x=0.5,
                            background_color=(0.8, 0.2, 0.2, 1))
        cancel_btn.bind(on_press=self.dismiss)

        button_layout.add_widget(confirm_btn)
        button_layout.add_widget(cancel_btn)

        content.add_widget(button_layout)
        self.content = content

    def update_content_bg(self, instance, value):
        """Update popup content background"""
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(1, 1, 1, 1)  # White background
            Rectangle(pos=instance.pos, size=instance.size)

    def confirm_vote(self, instance):
        self.on_confirm(self.candidate_id)
        self.dismiss()


class FingerprintVerificationPopup(Popup):
    """Popup for fingerprint verification before vote submission"""

    def __init__(self, candidate_id, on_verify_success, on_verify_fail, **kwargs):
        super().__init__(**kwargs)
        self.candidate_id = candidate_id
        self.on_verify_success = on_verify_success
        self.on_verify_fail = on_verify_fail
        self.title = 'Fingerprint Verification Required'
        self.size_hint = (0.8, 0.6)
        self.auto_dismiss = False

        # Initialize fingerprint reader
        self.fingerprint_reader = None
        self.verification_in_progress = False

        self.setup_ui()
        if FingerprintReader:
            self.start_fingerprint_verification()
        else:
            self.update_status(
                "Fingerprint reader not available - skipping verification")
            Clock.schedule_once(lambda dt: self.proceed_with_vote(), 2.0)

    def setup_ui(self):
        content = BoxLayout(orientation='vertical',
                            spacing=dp(20), padding=dp(20))

        # White background for popup content
        with content.canvas.before:
            Color(1, 1, 1, 1)  # White background
            Rectangle(pos=content.pos, size=content.size)
        content.bind(size=self.update_content_bg, pos=self.update_content_bg)

        # Title
        title_label = Label(
            text='Identity Verification',
            font_size=dp(22),
            bold=True,
            color=(0.2, 0.8, 0.4, 1),
            size_hint_y=0.2
        )
        content.add_widget(title_label)

        # Instruction
        instruction_label = Label(
            text='Please place your finger on the sensor to verify your identity before submitting your vote.',
            font_size=dp(16),
            text_size=(dp(400), None),
            halign='center',
            color=(0.2, 0.2, 0.2, 1),
            size_hint_y=0.25
        )
        content.add_widget(instruction_label)

        # Status label
        self.status_label = Label(
            text='Initializing fingerprint reader...',
            font_size=dp(14),
            color=(0.4, 0.4, 0.4, 1),
            size_hint_y=0.2
        )
        content.add_widget(self.status_label)

        # Fingerprint icon
        fingerprint_icon = Label(
            text='🖐️',
            font_size=dp(48),
            size_hint_y=0.2
        )
        content.add_widget(fingerprint_icon)

        # Button layout
        button_layout = BoxLayout(
            orientation='horizontal', spacing=dp(20), size_hint_y=0.15
        )

        # Retry button
        self.retry_btn = Button(
            text='Retry Verification',
            size_hint_x=0.5,
            background_color=(0.2, 0.6, 0.8, 1),
            disabled=True
        )
        self.retry_btn.bind(on_press=self.retry_verification)

        # Cancel button
        cancel_btn = Button(
            text='Cancel',
            size_hint_x=0.5,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        cancel_btn.bind(on_press=self.cancel_verification)

        button_layout.add_widget(self.retry_btn)
        button_layout.add_widget(cancel_btn)

        content.add_widget(button_layout)
        self.content = content

    def update_content_bg(self, instance, value):
        """Update popup content background"""
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(1, 1, 1, 1)  # White background
            Rectangle(pos=instance.pos, size=instance.size)

    def start_fingerprint_verification(self):
        """Start fingerprint verification in background thread"""
        if self.verification_in_progress or not FingerprintReader:
            return

        self.verification_in_progress = True
        self.retry_btn.disabled = True

        # Start verification in background thread
        threading.Thread(
            target=self._verify_fingerprint_thread, daemon=True).start()

    def _verify_fingerprint_thread(self):
        """Verify fingerprint in background thread"""
        try:
            # Initialize fingerprint reader
            Clock.schedule_once(lambda dt: self.update_status(
                "Connecting to fingerprint sensor..."), 0)

            self.fingerprint_reader = FingerprintReader(
                port='/dev/serial0',  # Adjust port as needed
                baudrate=57600,
                logger=lambda msg: Clock.schedule_once(
                    lambda dt: self.update_status(msg), 0)
            )

            Clock.schedule_once(lambda dt: self.update_status(
                "Place your finger on the sensor..."), 0)

            # Attempt fingerprint verification
            finger_id, confidence = self.fingerprint_reader.search_finger()

            if finger_id is not None:
                Clock.schedule_once(
                    lambda dt: self.verification_success(finger_id, confidence), 0)
            else:
                Clock.schedule_once(lambda dt: self.verification_failed(
                    "No matching fingerprint found"), 0)

        except Exception as e:
            Clock.schedule_once(lambda dt: self.verification_failed(
                f"Fingerprint reader error: {str(e)}"), 0)
        finally:
            self.verification_in_progress = False
            if self.fingerprint_reader:
                self.fingerprint_reader.cleanup()

    def update_status(self, message):
        """Update status label on main thread"""
        self.status_label.text = message

    def verification_success(self, finger_id, confidence):
        """Handle successful fingerprint verification"""
        self.status_label.text = f" Fingerprint verified! (ID: {finger_id}, Confidence: {confidence})"
        self.status_label.color = (0.2, 0.8, 0.2, 1)  # Green color

        # Auto-dismiss after 1 second and proceed with vote
        Clock.schedule_once(lambda dt: self.proceed_with_vote(), 1.0)

    def verification_failed(self, error_message):
        """Handle failed fingerprint verification"""
        self.status_label.text = f"❌ Verification failed: {error_message}"
        self.status_label.color = (0.8, 0.2, 0.2, 1)  # Red color
        self.retry_btn.disabled = False

    def proceed_with_vote(self):
        """Proceed with vote submission after successful verification"""
        self.dismiss()
        self.on_verify_success(self.candidate_id)

    def retry_verification(self, instance):
        """Retry fingerprint verification"""
        self.status_label.color = (0.4, 0.4, 0.4, 1)  # Reset to default color
        self.start_fingerprint_verification()

    def cancel_verification(self, instance):
        """Cancel fingerprint verification"""
        self.verification_in_progress = False
        if self.fingerprint_reader:
            self.fingerprint_reader.cleanup()
        self.dismiss()
        self.on_verify_fail("Verification cancelled by user")


class LoadingPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Processing Vote'
        self.size_hint = (0.6, 0.3)
        self.auto_dismiss = False

        content = BoxLayout(orientation='vertical',
                            spacing=dp(20), padding=dp(20))

        # White background for popup content
        with content.canvas.before:
            Color(1, 1, 1, 1)  # White background
            Rectangle(pos=content.pos, size=content.size)
        content.bind(size=self.update_loading_bg, pos=self.update_loading_bg)

        content.add_widget(Label(text='Processing your vote and uploading to IPFS...',
                                 font_size=dp(16), text_size=(dp(280), None), halign='center',
                                 color=(0.2, 0.2, 0.2, 1)))
        self.content = content

    def update_loading_bg(self, instance, value):
        """Update loading popup background"""
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(1, 1, 1, 1)  # White background
            Rectangle(pos=instance.pos, size=instance.size)


class QRCodeVerificationScreen(Screen):
    def __init__(self, user_id, secret, vote_hash, candidate_name, ipfs_cid=None, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.secret = secret
        self.vote_hash = vote_hash
        self.candidate_name = candidate_name
        self.ipfs_cid = ipfs_cid
        self.setup_ui()

    def setup_ui(self):
        # Main layout
        main_layout = FloatLayout()

        # Background
        with main_layout.canvas.before:
            Color(242/255, 242/255, 247/255, 1)  # #F2F2F7 background color
            Rectangle(pos=main_layout.pos, size=main_layout.size)

        main_layout.bind(size=self.update_background,
                         pos=self.update_background)

        # Content container
        content_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(30),
            padding=dp(40),
            size_hint=(0.9, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        # Title
        title = Label(
            text='Vote Successfully Recorded!',
            font_size=dp(28),
            bold=True,
            color=(0.2, 0.8, 0.4, 1),
            size_hint_y=0.15,
            halign='center'
        )
        content_layout.add_widget(title)

        # Success message
        success_msg = Label(
            text=f'Your vote has been securely uploaded to IPFS and recorded.',
            font_size=dp(16),
            color=(0.2, 0.2, 0.2, 1),
            size_hint_y=0.08,
            halign='center',
            text_size=(dp(600), None)
        )
        content_layout.add_widget(success_msg)

        # QR Code container
        qr_container = BoxLayout(
            orientation='vertical',
            spacing=dp(15),
            size_hint_y=0.45
        )

        # QR Code
        qr_code_widget = self.generate_qr_code()
        qr_container.add_widget(qr_code_widget)

        # QR Code instruction
        qr_instruction = Label(
            text='Scan QR code to verify your vote',
            font_size=dp(14),
            color=(0.4, 0.4, 0.4, 1),
            size_hint_y=0.15,
            halign='center',
            text_size=(dp(400), None)
        )
        qr_container.add_widget(qr_instruction)

        content_layout.add_widget(qr_container)

        # IPFS CID section (now mandatory)
        if self.ipfs_cid:
            ipfs_section = BoxLayout(
                orientation='vertical',
                spacing=dp(8),
                size_hint_y=0.12
            )

            ipfs_title = Label(
                text='IPFS Storage Confirmed',
                font_size=dp(14),
                bold=True,
                color=(0.2, 0.8, 0.2, 1),  # Green color for success
                size_hint_y=0.4,
                halign='center'
            )
            ipfs_section.add_widget(ipfs_title)

            ipfs_cid_label = Label(
                text=f'CID: {self.ipfs_cid}',
                font_size=dp(12),
                color=(0.3, 0.3, 0.3, 1),
                size_hint_y=0.6,
                halign='center',
                text_size=(dp(580), None)
            )
            ipfs_section.add_widget(ipfs_cid_label)

            content_layout.add_widget(ipfs_section)
        else:
            # This should never happen now, but just in case
            error_section = Label(
                text='IPFS Upload Failed - Vote Not Recorded',
                font_size=dp(16),
                bold=True,
                color=(0.8, 0.2, 0.2, 1),
                size_hint_y=0.12,
                halign='center'
            )
            content_layout.add_widget(error_section)

        # Vote details section
        details_section = BoxLayout(
            orientation='vertical',
            spacing=dp(5),
            size_hint_y=0.15
        )

        # User ID
        user_id_label = Label(
            text=f'Voter ID: {self.user_id}',
            font_size=dp(12),
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=0.33,
            halign='center'
        )
        details_section.add_widget(user_id_label)

        # Vote hash
        vote_hash_label = Label(
            text=f'Vote Hash: {self.vote_hash[:20]}...',
            font_size=dp(12),
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=0.33,
            halign='center'
        )
        details_section.add_widget(vote_hash_label)

        # Timestamp
        timestamp_label = Label(
            text=f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            font_size=dp(12),
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=0.33,
            halign='center'
        )
        details_section.add_widget(timestamp_label)

        content_layout.add_widget(details_section)

        # Instructions
        instructions = Label(
            text='Vote successfully uploaded to IPFS! Keep this receipt for verification.\nThank you for participating in the democratic process!',
            font_size=dp(14),
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=0.1,
            halign='center',
            text_size=(dp(580), None)
        )
        content_layout.add_widget(instructions)

        # Print button for thermal printer
        print_btn = RoundedButton(
            text='Print Receipt',
            size_hint_y=0.08,
            font_size=dp(14),
            bold=True
        )
        print_btn.bind(on_press=self.print_receipt)
        content_layout.add_widget(print_btn)

        main_layout.add_widget(content_layout)
        self.add_widget(main_layout)

    def generate_qr_code(self):
        """Generate QR code with URL for online vote verification"""
        # Create the verification URL using vote_hash as voterHash
        verification_url = f"https://vote-peek.vercel.app/vote/{self.vote_hash}"

        # Create QR code with the URL
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=30,
            border=6,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)

        # Create QR code image
        qr_image = qr.make_image(fill_color="green", back_color="white")

        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        qr_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Create Kivy CoreImage from bytes
        core_image = CoreImage(img_byte_arr, ext='png')

        # Create Image widget (smaller for thermal printer)
        qr_widget = Image(texture=core_image.texture, size_hint=(0.5, 0.85),
                          pos_hint={'center_x': 0.5})

        return qr_widget

    def generate_thermal_qr_code(self):
        """Generate smaller QR code for thermal printer"""
        verification_url = f"https://vote-peek.vercel.app/vote/{self.vote_hash}"

        # Create smaller QR code for thermal printer
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3,  # Smaller box size for thermal printer
            border=2,    # Smaller border
        )
        qr.add_data(verification_url)
        qr.make(fit=True)

        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")

        return qr_image

    def update_background(self, instance, value):
        """Update background when layout changes"""
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(242/255, 242/255, 247/255, 1)  # #F2F2F7 background color
            Rectangle(pos=instance.pos, size=instance.size)

    def print_receipt(self, instance):
        """Print thermal receipt - optimized for 58mm thermal printer"""
        try:
            # This function would interface with your thermal printer
            # For now, it creates a text receipt that can be sent to printer
            self.generate_thermal_receipt()
            self.show_print_success()
        except Exception as e:
            self.show_print_error(str(e))

    def generate_thermal_receipt(self):
        """Generate thermal printer compatible receipt with QR code"""
        # Generate QR code for thermal printer
        qr_image = self.generate_thermal_qr_code()

        # Save QR code as image file for thermal printer
        qr_file = os.path.join(VOTES_DIR, f"qr_{self.user_id}.png")
        qr_image.save(qr_file)

        verification_url = f"https://vote-peek.vercel.app/vote/{self.vote_hash}"

        receipt_content = f"""
{'='*32}
       VOTELINK RECEIPT
{'='*32}

VOTE CONFIRMED ON IPFS
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Voter ID: {self.user_id}
Candidate: {self.candidate_name}

Vote Hash: 
{self.vote_hash[:32]}
{self.vote_hash[32:]}

IPFS CID (MANDATORY):
{self.ipfs_cid[:32] if self.ipfs_cid else 'ERROR: NO CID'}
{self.ipfs_cid[32:] if self.ipfs_cid and len(self.ipfs_cid) > 32 else ''}

Secret Key (Keep Safe):
{self.secret[:16]}
{self.secret[16:]}

Verification URL:
{verification_url}

{'='*32}
[QR CODE WILL BE PRINTED HERE]

Scan QR code to verify online
or visit the URL above

{'='*32}
Your vote has been uploaded
to IPFS and is permanently
recorded on the distributed
network.

Keep this receipt safe for
verification purposes.

Thank you for voting!
{'='*32}
"""

        # Save receipt to file (can be sent to printer)
        receipt_file = os.path.join(VOTES_DIR, f"receipt_{self.user_id}.txt")
        with open(receipt_file, 'w') as f:
            f.write(receipt_content)

        print(f"Receipt saved to: {receipt_file}")
        print(f"QR code saved to: {qr_file}")

        # Send to thermal printer with QR code
        self.send_to_thermal_printer(receipt_content, qr_file)

        return receipt_file

    def send_to_thermal_printer(self, content, qr_file):
        """Send content and QR code to 58mm thermal printer (ESC/POS commands)"""
        try:
            import serial
            from PIL import Image

            # Configure for your thermal printer
            printer_port = '/dev/serial0'  # or '/dev/ttyUSB0', 'COM3', etc.
            baud_rate = 9600

            with serial.Serial(printer_port, baud_rate, timeout=1) as printer:
                # ESC/POS commands for formatting
                printer.write(b'\x1B\x40')  # Initialize printer
                printer.write(b'\x1B\x61\x01')  # Center align

                # Print text content (before QR code section)
                content_before_qr = content.split(
                    '[QR CODE WILL BE PRINTED HERE]')[0]
                printer.write(content_before_qr.encode('utf-8'))

                # Print QR code image
                self.print_qr_image(printer, qr_file)

                # Print text content (after QR code section)
                content_after_qr = content.split(
                    '[QR CODE WILL BE PRINTED HERE]')[1]
                printer.write(content_after_qr.encode('utf-8'))

                # Cut paper (if supported)
                printer.write(b'\x1D\x56\x00')

                print("Receipt with QR code sent to thermal printer successfully")

        except Exception as e:
            print(f"Thermal printer error: {e}")
            # Fallback: just save to file
            pass

    def print_qr_image(self, printer, qr_file):
        """Print QR code image on thermal printer using ESC/POS commands"""
        try:
            from PIL import Image

            # Load and process QR code image
            img = Image.open(qr_file)

            # Convert to black and white
            img = img.convert('1')  # Convert to 1-bit per pixel

            # Get image dimensions
            width, height = img.size

            # ESC/POS command to print raster bitmap
            # This is a simplified version - actual implementation may vary by printer model

            # Set line spacing to 0
            printer.write(b'\x1B\x33\x00')

            # Print image data line by line
            for y in range(height):
                # Start raster bitmap line
                printer.write(b'\x1D\x76\x30\x00')

                # Calculate bytes per line (width / 8, rounded up)
                bytes_per_line = (width + 7) // 8
                printer.write(
                    bytes([bytes_per_line & 0xFF, (bytes_per_line >> 8) & 0xFF]))
                printer.write(bytes([1, 0]))  # Height = 1 line

                # Convert pixels to bytes
                line_data = []
                for x in range(0, width, 8):
                    byte_val = 0
                    for bit in range(8):
                        if x + bit < width:
                            pixel = img.getpixel((x + bit, y))
                            if pixel == 0:  # Black pixel
                                byte_val |= (1 << (7 - bit))
                    line_data.append(byte_val)

                printer.write(bytes(line_data))

            # Reset line spacing
            printer.write(b'\x1B\x32')

        except Exception as e:
            print(f"QR code printing error: {e}")
            # Fallback: print placeholder text
            printer.write(b'\n[QR CODE]\n\n')

    def show_print_success(self):
        """Show print success message"""
        success_popup = Popup(
            title='Print Successful',
            content=Label(text='Receipt with QR code has been printed successfully!',
                          font_size=dp(16), color=(0.2, 0.8, 0.2, 1)),
            size_hint=(0.6, 0.3)
        )
        success_popup.open()
        Clock.schedule_once(lambda dt: success_popup.dismiss(), 2)

    def show_print_error(self, error_msg):
        """Show print error message"""
        error_popup = Popup(
            title='Print Error',
            content=Label(text=f'Print failed: {error_msg}',
                          font_size=dp(14), color=(0.8, 0.2, 0.2, 1)),
            size_hint=(0.7, 0.4)
        )
        error_popup.open()


def hash_vote(uid, candidate_id, secret):
    """Create a hash of the vote for commit-reveal scheme"""
    vote_data = f"{candidate_id}:{secret}"
    return hashlib.sha256(vote_data.encode()).hexdigest()


def load_json(path):
    """Load JSON data from file"""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {path}: {e}")
        return {}


def save_json(path, data):
    """Save JSON data to file"""
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except IOError as e:
        print(f"Error saving {path}: {e}")
        return False


def get_ipfs_version():
    """Get IPFS version information"""
    try:
        response = requests.get(
            'http://127.0.0.1:5001/api/v0/version', timeout=5)
        if response.status_code == 200:
            version_info = response.json()
            return version_info.get('Version', 'Unknown')
    except:
        pass
    return None


def check_ipfs_connection():
    """Check if IPFS node is running and accessible using HTTP API"""
    try:
        # Test IPFS connection using HTTP API
        response = requests.post('http://127.0.0.1:5001/api/v0/id', timeout=5)
        if response.status_code == 200:
            node_info = response.json()
            version = get_ipfs_version()
            print(f" IPFS connected successfully. Node ID: {node_info['ID']}")
            print(f" IPFS Version: {version}")
            return True, None
        else:
            error_msg = f"IPFS HTTP API returned status {response.status_code}"
            print(f"❌ {error_msg}")
            return False, error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"IPFS connection failed: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected IPFS error: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg


def upload_to_ipfs(file_path):
    """Upload file to IPFS using HTTP API directly"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                'http://127.0.0.1:5001/api/v0/add',
                files=files,
                timeout=30
            )

        if response.status_code == 200:
            response_text = response.text.strip()
            last_line = response_text.split('\n')[-1]
            result = json.loads(last_line)

            cid = result['Hash']
            print(f" File uploaded to IPFS successfully. CID: {cid}")
            return cid
        else:
            raise Exception(
                f"IPFS upload failed with status {response.status_code}: {response.text}")

    except Exception as e:
        print(f"❌ IPFS upload error: {str(e)}")
        raise e


class ElectionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.verified_user = None
        self.candidates = {
            1: "Goodluck Jonathan",
            2: "Mohammed Buhari"
        }
        self.setup_ui()

    def set_verified_user(self, user):
        """Receive user data from VerificationScreen"""
        self.verified_user = user
        print(f"Verified User in ElectionScreen: {user.get('uid', 'Unknown')}")

    def setup_ui(self):
        # Main layout
        main_layout = FloatLayout()

        # Background
        with main_layout.canvas.before:
            Color(242/255, 242/255, 247/255, 1)  # #F2F2F7 background color
            Rectangle(pos=main_layout.pos, size=main_layout.size)

        main_layout.bind(size=self.update_background,
                         pos=self.update_background)

        # Title
        title = Label(text='VoteLink - Offline Edition', font_size=dp(28), bold=True,
                      color=(0.2, 0.8, 0.4, 1), size_hint=(1, 0.1),
                      pos_hint={'top': 1})
        main_layout.add_widget(title)

        # Candidates container
        candidates_layout = GridLayout(cols=2, spacing=dp(20), padding=dp(20),
                                       size_hint=(0.85, 0.68), pos_hint={'center_x': 0.5, 'top': 0.9})

        # Candidate 1
        candidate1 = CandidateCard(
            candidate_name="Goodluck Jonathan",
            party_name="PDP Party",
            candidate_id=1,
            vote_callback=self.show_vote_confirmation,
            candidate_image="assets/can1.jpg",  # Will check if exists
            party_image="assets/pdplogo.png"    # Will check if exists
        )
        candidates_layout.add_widget(candidate1)

        # Candidate 2
        candidate2 = CandidateCard(
            candidate_name="Mohammed Buhari",
            party_name="APC Party",
            candidate_id=2,
            vote_callback=self.show_vote_confirmation,
            candidate_image="assets/can2.jpg",     # Will check if exists
            party_image="assets/apclogo.png"   # Will check if exists
        )
        candidates_layout.add_widget(candidate2)

        main_layout.add_widget(candidates_layout)

        # Footer
        footer = Label(text='Secure Offline Voting System', font_size=dp(12),
                       color=(0.5, 0.5, 0.5, 1), size_hint=(1, 0.1),
                       pos_hint={'bottom': 1})
        main_layout.add_widget(footer)

        self.add_widget(main_layout)

    def update_background(self, instance, value):
        """Update background when layout changes"""
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(242/255, 242/255, 247/255, 1)  # #F2F2F7 background color
            Rectangle(pos=instance.pos, size=instance.size)

    def on_enter(self):
        """Called when screen is entered"""
        app = App.get_running_app()
        if hasattr(app, 'verified_user'):
            self.verified_user = app.verified_user

        if not self.verified_user:
            print("No verified user found. Please verify your identity first.")
            # You might want to redirect to verification screen here
            return

        if self.verified_user:
            uid = self.verified_user.get("uid")
            name = self.verified_user.get("name")
            print(f"User Name in Election Screen: {name}")
            print(f"User UID in Election Screen: {uid}")

    def show_vote_confirmation(self, candidate_id):
        """Show confirmation popup before voting"""
        # First check IPFS connection
        ipfs_connected, error_msg = check_ipfs_connection()
        if not ipfs_connected:
            self.show_error(
                f"Cannot vote: IPFS is not available.\n\n{error_msg}\n\nPlease ensure IPFS daemon is running:\n• Start IPFS: ipfs daemon\n• Check status: ipfs id")
            return

        candidate_name = self.candidates.get(
            candidate_id, f"Candidate {candidate_id}")

        popup = VoteConfirmationPopup(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            on_confirm=self.show_fingerprint_verification
        )
        popup.open()

    def show_fingerprint_verification(self, candidate_id):
        """Show fingerprint verification popup"""
        fingerprint_popup = FingerprintVerificationPopup(
            candidate_id=candidate_id,
            on_verify_success=self.submit_vote,
            on_verify_fail=self.verification_failed
        )
        fingerprint_popup.open()

    def verification_failed(self, error_message):
        """Handle failed fingerprint verification"""
        self.show_error(f"Verification failed: {error_message}")

    def submit_vote(self, candidate_id):
        """Submit vote using offline commit-reveal scheme"""
        # Show loading popup
        loading_popup = LoadingPopup()
        loading_popup.open()

        def process_vote():
            try:
                # Get user data
                if self.verified_user:
                    uid = self.verified_user.get("uid")
                    name = self.verified_user.get("name")
                else:
                    # Fallback for testing
                    uid = "333445577"
                    name = "Test User"

                print(
                    f"Submitting vote for {name} (UID: {uid}) for candidate {candidate_id}")

                # Check if user has already voted
                commits = load_json(COMMIT_FILE)
                if uid in commits:
                    Clock.schedule_once(lambda dt: self.vote_error(
                        loading_popup, "You have already voted!"), 0)
                    return

                # Generate secret and hash
                salt = secrets.token_hex(16)
                vote_hash = hash_vote(uid, candidate_id, salt)

                print(f"Generated vote hash: {vote_hash} with salt: {salt}")

                # PRIORITY: Upload to IPFS FIRST - vote fails if this fails
                ipfs_cid = None
                try:
                    # Create a vote record for IPFS
                    vote_record = {
                        "user_id": uid,
                        "vote_hash": vote_hash,
                        "salt": salt,
                        "candidate_id": candidate_id,
                        "timestamp": datetime.now().isoformat(),
                        "election_id": "ELECTION_2025"  # You can customize this
                    }

                    # Save temporary file for IPFS upload
                    temp_vote_file = os.path.join(
                        VOTES_DIR, f"vote_{uid}.json")
                    with open(temp_vote_file, 'w') as f:
                        json.dump(vote_record, f, indent=2)

                    # Upload to IPFS using HTTP API - THIS MUST SUCCEED
                    print("Uploading vote to IPFS...")
                    ipfs_cid = upload_to_ipfs(temp_vote_file)

                    # Clean up temporary file
                    os.remove(temp_vote_file)

                    print(
                        f" Vote successfully uploaded to IPFS with CID: {ipfs_cid}")

                except Exception as e:
                    print(f"❌ CRITICAL: IPFS upload failed: {str(e)}")
                    # Clean up temp file if it exists
                    temp_vote_file = os.path.join(
                        VOTES_DIR, f"vote_{uid}.json")
                    if os.path.exists(temp_vote_file):
                        os.remove(temp_vote_file)

                    # IPFS upload failed - abort the vote process
                    error_msg = f"IPFS upload failed: {str(e)}\n\nPlease ensure IPFS daemon is running:\nipfs daemon."
                    Clock.schedule_once(lambda dt: self.vote_error(
                        loading_popup, error_msg), 0)
                    return

                # Only proceed with local storage if IPFS upload succeeded
                print("IPFS upload successful, proceeding with local storage...")

                # Save commit locally (only after IPFS success)
                commits[uid] = {
                    "vote_hash": vote_hash,
                    "timestamp": datetime.now().isoformat(),
                    "candidate_id": candidate_id,
                    "ipfs_cid": ipfs_cid  # Store the CID with the commit
                }

                if not save_json(COMMIT_FILE, commits):
                    Clock.schedule_once(lambda dt: self.vote_error(
                        loading_popup, "Failed to save vote commit locally"), 0)
                    return

                # Save secret separately for reveal phase (only after IPFS success)
                secrets_data = load_json(SECRETS_FILE)
                secrets_data[uid] = {
                    "secret": salt,
                    "candidate_id": candidate_id,
                    "timestamp": datetime.now().isoformat(),
                    "ipfs_cid": ipfs_cid  # Store the CID with the secret too
                }

                if not save_json(SECRETS_FILE, secrets_data):
                    Clock.schedule_once(lambda dt: self.vote_error(
                        loading_popup, "Failed to save vote secret locally"), 0)
                    return

                # Vote is only successful if IPFS upload succeeded
                candidate_name = self.candidates.get(
                    candidate_id, f"Candidate {candidate_id}")
                print(
                    f" Vote process completed successfully with IPFS CID: {ipfs_cid}")
                Clock.schedule_once(lambda dt: self.vote_success(
                    loading_popup, uid, salt, vote_hash, candidate_name, ipfs_cid), 0)

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                Clock.schedule_once(lambda dt, msg=error_msg: self.vote_error(
                    loading_popup, msg), 0)

        # Process vote in background thread
        threading.Thread(target=process_vote, daemon=True).start()

    def vote_success(self, loading_popup, user_id, secret, vote_hash, candidate_name, ipfs_cid=None):
        """Handle successful vote submission"""
        loading_popup.dismiss()
        self.switch_to_qr_screen(
            user_id, secret, vote_hash, candidate_name, ipfs_cid)

    def vote_error(self, loading_popup, error_msg):
        """Handle vote submission error"""
        loading_popup.dismiss()
        self.show_error(f"Vote failed: {error_msg}")

    def switch_to_qr_screen(self, user_id, secret, vote_hash, candidate_name, ipfs_cid=None):
        """Switch to QR code verification screen"""
        # Get the screen manager
        screen_manager = self.parent

        # Create QR code verification screen
        qr_screen = QRCodeVerificationScreen(
            user_id=user_id,
            secret=secret,
            vote_hash=vote_hash,
            candidate_name=candidate_name,
            ipfs_cid=ipfs_cid,
            name='qr_verification'
        )

        # Add screen to manager if it doesn't exist
        if not screen_manager.has_screen('qr_verification'):
            screen_manager.add_widget(qr_screen)
        else:
            # Remove old screen and add new one
            screen_manager.remove_widget(
                screen_manager.get_screen('qr_verification'))
            screen_manager.add_widget(qr_screen)

        # Switch to QR screen
        screen_manager.current = 'qr_verification'

    def show_error(self, message):
        """Show error popup"""
        error_popup = Popup(
            title='Voting Error',
            content=self.create_white_popup_content(message),
            # Made bigger for detailed IPFS error messages
            size_hint=(0.9, 0.6)
        )
        error_popup.open()

    def create_white_popup_content(self, text):
        """Create popup content with white background"""
        content = BoxLayout(orientation='vertical',
                            spacing=dp(20), padding=dp(20))

        # White background
        with content.canvas.before:
            Color(1, 1, 1, 1)
            Rectangle(pos=content.pos, size=content.size)

        def update_bg(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(1, 1, 1, 1)
                Rectangle(pos=instance.pos, size=instance.size)

        content.bind(size=update_bg, pos=update_bg)

        content.add_widget(Label(text=text, font_size=dp(16),
                                 text_size=(dp(350), None), halign='center',
                                 color=(0.2, 0.2, 0.2, 1)))
        return content


# Additional utility functions for vote verification
def verify_vote(uid, candidate_id, secret, stored_hash):
    """Verify that a vote matches the stored hash"""
    calculated_hash = hash_vote(uid, candidate_id, secret)
    return calculated_hash == stored_hash


def get_vote_statistics():
    """Get voting statistics from stored commits"""
    commits = load_json(COMMIT_FILE)
    secrets = load_json(SECRETS_FILE)

    stats = {
        "total_votes": len(commits),
        "candidate_votes": {},
        "verified_votes": 0
    }

    # Count votes per candidate (from secrets file for actual counts)
    for uid, secret_data in secrets.items():
        candidate_id = secret_data.get("candidate_id")
        if candidate_id:
            stats["candidate_votes"][candidate_id] = stats["candidate_votes"].get(
                candidate_id, 0) + 1

    # Verify vote integrity
    for uid in commits:
        if uid in secrets:
            secret_data = secrets[uid]
            if verify_vote(uid, secret_data["candidate_id"], secret_data["secret"], commits[uid]["vote_hash"]):
                stats["verified_votes"] += 1

    return stats


# Example usage function for testing
def print_vote_statistics():
    """Print current voting statistics"""
    stats = get_vote_statistics()
    print(f"Total votes: {stats['total_votes']}")
    print(f"Verified votes: {stats['verified_votes']}")
    print("Votes per candidate:")
    for candidate_id, count in stats['candidate_votes'].items():
        print(f"  Candidate {candidate_id}: {count} votes")
