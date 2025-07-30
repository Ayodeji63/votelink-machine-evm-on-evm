import serial
import time
import threading
import random
import string
import glob
from datetime import datetime


class RFIDReader:
    """RFID Reader class for USB-connected RFID module"""

    def __init__(self, callback=None):
        self.ser = None
        self.simulation_mode = False  # Set to False for actual hardware
        self.callback = callback  # Optional callback for real-time updates
        self.last_card_id = None
        self.last_scan_time = 0
        self.scan_cooldown = 2.0  # Seconds between scans of same card
        self.is_scanning = False
        self.scan_thread = None
        self.current_card_data = {}

        # Known cards database (for testing)
        self.known_cards = {
            "93F34DC5E8": {"name": "John Doe", "access_level": "admin"},
            "AABBCCDDEE": {"name": "Jane Smith", "access_level": "user"}
        }

        if not self.simulation_mode:
            self.initialize_serial()
        else:
            print("RFID Reader in simulation mode")

    def initialize_serial(self):
        """Initialize serial connection to USB RFID reader"""
        try:
            # Try to find the correct port automatically
            port = self.find_serial_port()
            if port:
                self.ser = serial.Serial(port, 9600, timeout=1)
                time.sleep(2)  # Give device time to initialize
                print(f"RFID Reader connected to {port}")
                self.simulation_mode = False
            else:
                print("No RFID reader found, using simulation mode")
                self.simulation_mode = True
        except Exception as e:
            print(f"Failed to initialize RFID reader: {e}")
            self.simulation_mode = True

    def find_serial_port(self):
        """Automatically find the correct serial port"""
        possible_ports = ['/dev/ttyUSB0', '/dev/ttyACM0', '/dev/ttyUSB1']

        # Add all available USB/ACM ports
        possible_ports.extend(glob.glob('/dev/ttyUSB*'))
        possible_ports.extend(glob.glob('/dev/ttyACM*'))

        for port in possible_ports:
            try:
                test_ser = serial.Serial(port, 9600, timeout=1)
                test_ser.close()
                return port
            except serial.SerialException:
                continue

        return None

    def start_continuous_scan(self):
        """Start continuous scanning in a separate thread"""
        if self.is_scanning:
            return

        self.is_scanning = True
        self.scan_thread = threading.Thread(
            target=self._scan_loop, daemon=True)
        self.scan_thread.start()

    def stop_continuous_scan(self):
        """Stop continuous scanning"""
        self.is_scanning = False
        if self.scan_thread:
            self.scan_thread.join(timeout=1)

    def _scan_loop(self):
        """Internal scanning loop"""
        while self.is_scanning:
            try:
                card_id = self.read_card()
                if card_id and self.callback:
                    self.callback(card_id)
                time.sleep(0.1)  # Small delay to prevent overwhelming
            except Exception as e:
                print(f"Error in scan loop: {e}")
                time.sleep(1)

    def read_card(self):
        """
        Read RFID card and return UID
        Returns: str - UID of the card or None if no card detected
        """
        if self.simulation_mode:
            return self._simulate_card_read()

        if not self.ser:
            return None

        try:
            # Check if data is available
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8').strip()

                # Skip empty lines and dots
                if not line or line == ".":
                    return None

                # Look for card detection
                if "Card found" in line:
                    self.current_card_data = {}
                    return None

                # Extract decimal values
                elif line.startswith("Dec: "):
                    dec_str = line.replace("Dec: ", "").strip()
                    dec_values = [int(x.strip()) for x in dec_str.split(",")]
                    self.current_card_data['decimal'] = dec_values
                    return None

                # Extract hex values and create card ID
                elif line.startswith("Hex: "):
                    hex_str = line.replace("Hex: ", "").strip()
                    hex_values = [x.strip().upper()
                                  for x in hex_str.split(",")]
                    self.current_card_data['hex'] = hex_values

                    # Create a unique card ID from hex values
                    card_id = "".join([val.zfill(2) for val in hex_values])

                    # Check cooldown to prevent duplicate reads
                    current_time = time.time()
                    if (card_id != self.last_card_id or
                            current_time - self.last_scan_time > self.scan_cooldown):

                        self.last_card_id = card_id
                        self.last_scan_time = current_time

                        # Log the card read
                        self.log_card_read(card_id, self.current_card_data)

                        return card_id

                return None

        except Exception as e:
            print(f"Error reading RFID card: {e}")
            return None

    def _simulate_card_read(self):
        """Simulate card reading for testing"""
        if random.random() < 0.1:  # 10% chance of detecting card
            # Generate a random UID or use a known one
            if random.random() < 0.3:  # 30% chance of known card
                uid = random.choice(list(self.known_cards.keys()))
            else:
                uid = ''.join(random.choices(
                    string.ascii_uppercase + string.digits, k=10))

            # Check cooldown
            current_time = time.time()
            if (uid != self.last_card_id or
                    current_time - self.last_scan_time > self.scan_cooldown):

                self.last_card_id = uid
                self.last_scan_time = current_time
                return uid

        return None

    def read_card_blocking(self, timeout=10):
        """
        Read RFID card with timeout (blocking)
        Args:
            timeout (int): Timeout in seconds
        Returns:
            str: UID of the card or None if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            card_id = self.read_card()
            if card_id:
                return card_id
            time.sleep(0.1)

        return None

    def write_card(self, data):
        """
        Write data to RFID card (if supported by reader)
        Args:
            data (str): Data to write to the card
        Returns:
            bool: True if successful, False otherwise
        """
        if self.simulation_mode:
            print(f"Simulating write to RFID card: {data}")
            return True

        # Most USB RFID readers are read-only
        # This would need to be implemented based on your specific reader's capabilities
        print("Write operation not supported by USB RFID reader")
        return False

    def is_card_present(self):
        """
        Check if a card is present without reading
        Returns:
            bool: True if card is present, False otherwise
        """
        if self.simulation_mode:
            return random.random() < 0.3  # 30% chance

        # For USB readers, we can't easily detect presence without reading
        # This would depend on your specific reader's capabilities
        return self.read_card() is not None

    def get_card_info(self, uid):
        """
        Get additional information about the card
        Args:
            uid (str): UID of the card
        Returns:
            dict: Card information
        """
        info = {
            'uid': uid,
            'type': 'Unknown',
            'size': 'Unknown',
            'readable': True,
            'writable': False,  # Most USB readers are read-only
            'scan_time': datetime.now().isoformat()
        }

        # Add known card information if available
        if uid in self.known_cards:
            info.update(self.known_cards[uid])
            info['known_card'] = True
        else:
            info['known_card'] = False

        return info

    def log_card_read(self, card_id, card_data):
        """Log card read event"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] Card Read: {card_id}")

        if 'decimal' in card_data:
            print(f"  Decimal: {card_data['decimal']}")
        if 'hex' in card_data:
            print(f"  Hex: {card_data['hex']}")

    def add_known_card(self, uid, name, access_level="user"):
        """Add a card to the known cards database"""
        self.known_cards[uid] = {
            "name": name,
            "access_level": access_level
        }

    def remove_known_card(self, uid):
        """Remove a card from the known cards database"""
        if uid in self.known_cards:
            del self.known_cards[uid]

    def cleanup(self):
        """Clean up resources"""
        self.stop_continuous_scan()

        if self.ser:
            try:
                self.ser.close()
                print("RFID Reader serial connection closed")
            except:
                pass


# Example usage and testing
if __name__ == "__main__":
    def card_detected_callback(card_id):
        print(f"Card detected via callback: {card_id}")

    # Initialize reader
    reader = RFIDReader(callback=card_detected_callback)

    try:
        print("Starting RFID reader test...")
        print("Press Ctrl+C to exit")

        # Start continuous scanning
        reader.start_continuous_scan()

        # Keep the main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping RFID reader...")
        reader.cleanup()
        print("Done!")
