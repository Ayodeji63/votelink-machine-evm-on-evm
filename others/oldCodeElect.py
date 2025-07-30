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
from web3 import Web3
from eth_account import Account
import json
import threading
import qrcode
import io
from PIL import Image as PILImage
from kivy.core.image import Image as CoreImage
import urllib.request
# import os

# Polygon Amoy RPC URL
POLYGON_AMOY_RPC = "https://polygon-amoy.g.alchemy.com/v2/3avVRcwPpT8B1A_hZW6gBTKZgwI5Sull"

# Contract ABI for VoteLinkContract
CONTRACT_ABI = [{"inputs": [], "stateMutability": "nonpayable", "type": "constructor"}, {"anonymous": False, "inputs": [{"indexed": True, "internalType": "uint256", "name": "candidateId", "type": "uint256"}, {"indexed": False, "internalType": "string", "name": "name", "type": "string"}, {"indexed": False, "internalType": "string", "name": "party", "type": "string"}], "name": "CandidateAdded", "type": "event"}, {"anonymous": False, "inputs": [], "name": "ElectionEnded", "type": "event"}, {"anonymous": False, "inputs": [], "name": "ElectionStarted", "type": "event"}, {"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "voter", "type": "address"}, {"indexed": True, "internalType": "uint256", "name": "candidateId", "type": "uint256"}], "name": "VoteCast", "type": "event"}, {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "name": "candidateIds", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "name": "candidates", "outputs": [{"internalType": "uint256", "name": "id", "type": "uint256"}, {"internalType": "string", "name": "name", "type": "string"}, {"internalType": "string", "name": "party", "type": "string"}, {"internalType": "uint256", "name": "voteCount", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "string", "name": "_voterId", "type": "string"}], "name": "checkIfVoted", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "electionActive", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "endElection", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [], "name": "getAllCandidates", "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "uint256", "name": "_candidateId", "type": "uint256"}], "name": "getCandidate", "outputs": [{"internalType": "uint256", "name": "id", "type": "uint256"}, {"internalType": "string", "name": "name", "type": "string"}, {"internalType": "string", "name": "party", "type": "string"}, {"internalType": "uint256", "name": "voteCount", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "getResults", "outputs": [{"internalType": "string[]", "name": "candidateNames", "type": "string[]"}, {"internalType": "uint256[]", "name": "voteCounts", "type": "uint256[]"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "getWinner", "outputs": [{"internalType": "uint256", "name": "winningCandidateId", "type": "uint256"}, {"internalType": "string", "name": "winningCandidateName", "type": "string"}, {"internalType": "uint256", "name": "winningVoteCount", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "string", "name": "", "type": "string"}], "name": "hasVoted", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "owner", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "resetElection", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [], "name": "startElection", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [], "name": "totalVotes", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "uint256", "name": "_candidateId", "type": "uint256"}, {"internalType": "string", "name": "voterId", "type": "string"}], "name": "vote", "outputs": [], "stateMutability": "nonpayable", "type": "function"}]


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
        self.spacing = dp(13)  # Reduced from 15dp by ~15%
        self.padding = dp(17)  # Reduced from 20dp by ~15%
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
            orientation='horizontal', size_hint_y=0.25, spacing=dp(9))  # Reduced from 10dp

        # Party image
        if party_image:
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
        party_layout.add_widget(Label(text=party_name, font_size=dp(15),  # Reduced from 18dp by ~15%
                                      color=(0.2, 0.2, 0.2, 1), bold=True,
                                      text_size=(None, None), halign='left'))
        self.add_widget(party_layout)

        # Candidate section with large image
        candidate_layout = BoxLayout(
            orientation='vertical', size_hint_y=0.5, spacing=dp(9))  # Reduced from 10dp

        # Candidate image (large and prominent)
        if candidate_image:
            candidate_img = Image(source=candidate_image,
                                  size_hint_y=0.8, allow_stretch=True)
        else:
            # Placeholder for candidate image
            candidate_img = Widget(size_hint_y=0.8)
            with candidate_img.canvas:
                Color(0.9, 0.9, 0.9, 1)
                RoundedRectangle(pos=candidate_img.pos,
                                 size=candidate_img.size, radius=[dp(10)])
                Color(0.6, 0.6, 0.6, 1)
                # Add person icon placeholder

        candidate_layout.add_widget(candidate_img)
        candidate_layout.add_widget(Label(text=candidate_name, font_size=dp(17),  # Reduced from 20dp by ~15%
                                          color=(0.1, 0.1, 0.1, 1), bold=True,
                                          size_hint_y=0.2))
        self.add_widget(candidate_layout)

        # Vote button
        vote_btn = RoundedButton(text='Vote', size_hint_y=0.15,
                                 font_size=dp(15), bold=True)  # Reduced from 18dp by ~15%
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
    def __init__(self, candidate_id, on_confirm, **kwargs):
        super().__init__(**kwargs)
        self.candidate_id = candidate_id
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

        content.add_widget(Label(text=f'Are you sure you want to vote for Candidate {candidate_id}?',
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

        content.add_widget(Label(text='Submitting your vote to the blockchain...',
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
    def __init__(self, tx_hash, **kwargs):
        super().__init__(**kwargs)
        self.tx_hash = tx_hash
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
            text='Your vote has been securely recorded on the Polygon blockchain.',
            font_size=dp(18),
            color=(0.2, 0.2, 0.2, 1),
            size_hint_y=0.1,
            halign='center',
            text_size=(dp(600), None)
        )
        content_layout.add_widget(success_msg)

        # QR Code container
        qr_container = BoxLayout(
            orientation='vertical',
            spacing=dp(20),
            size_hint_y=0.5
        )

        # QR Code
        qr_code_widget = self.generate_qr_code()
        qr_container.add_widget(qr_code_widget)

        # QR Code instruction
        qr_instruction = Label(
            text='Scan this QR code to verify your vote on Polygon scan',
            font_size=dp(16),
            color=(0.4, 0.4, 0.4, 1),
            size_hint_y=0.2,
            halign='center',
            text_size=(dp(400), None)
        )
        qr_container.add_widget(qr_instruction)

        content_layout.add_widget(qr_container)

        # Transaction details
        tx_details = Label(
            text=f'Transaction Hash: {self.tx_hash[:10]}...{self.tx_hash[-10:]}',
            font_size=dp(14),
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=0.1,
            halign='center',
            text_size=(dp(600), None)
        )
        content_layout.add_widget(tx_details)

        # Instructions
        instructions = Label(
            text='Your vote is now immutable and transparent on the blockchain.\nThank you for participating in the democratic process!',
            font_size=dp(16),
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=0.15,
            halign='center',
            text_size=(dp(600), None)
        )
        content_layout.add_widget(instructions)

        main_layout.add_widget(content_layout)
        self.add_widget(main_layout)

    def generate_qr_code(self):
        """Generate QR code for Polygon scan verification"""
        # Polygon Amoy testnet explorer URL
        polygon_scan_url = f"https://amoy.polygonscan.com/tx/{self.tx_hash}"

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(polygon_scan_url)
        qr.make(fit=True)

        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")

        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        qr_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Create Kivy CoreImage from bytes
        core_image = CoreImage(img_byte_arr, ext='png')

        # Create Image widget
        qr_widget = Image(texture=core_image.texture, size_hint=(0.6, 0.8),
                          pos_hint={'center_x': 0.5})

        return qr_widget

    def update_background(self, instance, value):
        """Update background when layout changes"""
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(242/255, 242/255, 247/255, 1)  # #F2F2F7 background color
            Rectangle(pos=instance.pos, size=instance.size)


def is_connected():
    try:
        urllib.request.urlopen("http://www.google.com", timeout=2)
        return True
    except urllib.request.URLError:
        return False


class ElectionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.verified_user = None
        self.web3 = None
        self.contract = None
        self.account = None
        self.offline_mode = is_connected()
        self.setup_web3()
        self.setup_ui()

    def set_verified_user(self, user):
        """Receive user data form VerificationScreen"""
        self.verified_user = user
        print(f"Verified User in ElectionScreen: {user['uid']}")

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
        title = Label(text='VoteLink', font_size=dp(28), bold=True,
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
            candidate_image="assets/can1.jpg",  # Add your candidate image path
            party_image="assets/pdplogo.png"    # Add your party logo path
        )
        candidates_layout.add_widget(candidate1)

        # Candidate 2
        candidate2 = CandidateCard(
            candidate_name="Mohammed Buhari",
            party_name="APC Party",
            candidate_id=2,
            vote_callback=self.show_vote_confirmation,
            candidate_image="assets/can2.jpg",     # Add your candidate image path
            party_image="assets/apclogo.png"   # Add your party logo path
        )
        candidates_layout.add_widget(candidate2)

        main_layout.add_widget(candidates_layout)

        # Footer
        footer = Label(text='Secure Blockchain Voting', font_size=dp(12),
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

    # Inside ElectionScreen class
    def on_enter(self):
        app = App.get_running_app()
        self.verified_user = app.verified_user

        if not self.verified_user:
            print("No verified user found. Please verify your identity first.")
            self.manager.current = 'verify'  # Switch to verification screen
            return
        if self.verified_user:
            uid = self.verified_user.get("uid")
            name = self.verified_user.get("name")
            print(f"User Name in Election Screen: {name}")
            print(f"User UID in Election Screen: {uid}")
            # Use UID to log vote, show profile, check eligibility, etc.

    def setup_web3(self):
        """Initialize Web3 connection to Polygon Amoy"""
        try:
            self.web3 = Web3(Web3.HTTPProvider(POLYGON_AMOY_RPC))
            if self.web3.is_connected():
                print("Connected to Polygon Amoy")

                # For demo purposes, you'll need to set these values
                # Replace with actual contract address
                contract_address = "0xD6Cc5fC8EA585c8f2EB28E891533A62F618e4979"
                # Replace with actual private key
                private_key = "0x5810098e367422376897bb2645c5ada5850a99aeec0505a58d38853ebd7f9f31"

                self.contract = self.web3.eth.contract(
                    address=contract_address,
                    abi=CONTRACT_ABI
                )

                self.account = Account.from_key(private_key)
                print(f"Account address: {self.account.address}")
            else:
                print("Failed to connect to Polygon Amoy")
        except Exception as e:
            print(f"Error setting up Web3: {e}")

    def show_vote_confirmation(self, candidate_id):
        """Show confirmation popup before voting"""
        popup = VoteConfirmationPopup(
            candidate_id=candidate_id,
            on_confirm=self.submit_vote
        )
        popup.open()

    def submit_vote(self, candidate_id):
        """Submit vote to blockchain"""
        if not self.web3 or not self.contract or not self.account:
            self.show_error("Blockchain connection not available")
            return

        # Show loading popup
        loading_popup = LoadingPopup()
        loading_popup.open()

        # Submit vote in background thread
        if self.offline_mode:
            self.save_vote_offline(candidate_id)
            loading_popup.dismiss()
            self.switch_to_qr_screen("offline")
        else:
            threading.Thread(target=self._submit_vote_thread,
                             args=(candidate_id, loading_popup)).start()

    def _submit_vote_thread(self, candidate_id, loading_popup):
        """Submit vote in background thread"""
        try:
            voter_id = str(self.verified_user['uid'])
            print(f"Voter ID: {voter_id}")
        except ValueError:
            Clock.schedule_once(lambda dt: self.vote_error(
                loading_popup, "Invalid UID format."), 0)
            return
        try:
            # Build transaction
            transaction = self.contract.functions.vote(candidate_id, voter_id).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': 100000,
                'gasPrice': self.web3.eth.gas_price,
            })

            # Sign transaction
            signed_txn = self.account.sign_transaction(transaction)

            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(
                signed_txn.rawTransaction)

            # Wait for confirmation
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            # Schedule UI update on main thread
            Clock.schedule_once(lambda dt: self.vote_success(
                loading_popup, tx_hash.hex()), 0)

        except Exception as e:
            Clock.schedule_once(lambda dt, err=str(
                e): self.vote_error(loading_popup, str(err)), 0)

    def vote_success(self, loading_popup, tx_hash):
        """Handle successful vote submission"""
        loading_popup.dismiss()

        # Switch to QR code verification screen
        self.switch_to_qr_screen(tx_hash)

    def switch_to_qr_screen(self, tx_hash):
        """Switch to QR code verification screen"""
        # Get the screen manager
        screen_manager = self.parent

        # Create QR code verification screen
        qr_screen = QRCodeVerificationScreen(
            tx_hash=tx_hash, name='qr_verification')

        # Add screen to manager
        screen_manager.add_widget(qr_screen)

        # Switch to QR screen
        screen_manager.current = 'qr_verification'

    def vote_error(self, loading_popup, error_msg):
        """Handle vote submission error"""
        loading_popup.dismiss()
        self.show_error(f"Vote failed: {error_msg}")

    def show_error(self, message):
        """Show error popup"""
        error_popup = Popup(
            title='Error',
            content=self.create_white_popup_content(message),
            size_hint=(0.8, 0.4)
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
