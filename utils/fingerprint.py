import time
import serial
import json
import os

import adafruit_fingerprint


class FingerprintReader:
    """Fingerprint Reader for Adafruit-compatible modules like R305"""

    def __init__(self, port='/dev/serial0', baudrate=57600, logger=None):
        self.logger = logger or print
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.enrolled_fingerprints = self.load_fingerprint_database()

        try:
            # Initialize serial connection
            self.serial_connection = serial.Serial(port, baudrate, timeout=1)
            print(f" Fingerprint reader connected on {port}")

            # Initialize Adafruit Fingerprint Sensor
            self.finger = adafruit_fingerprint.Adafruit_Fingerprint(
                self.serial_connection)
            print(" Adafruit Fingerprint initialized")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize fingerprint reader: {e}")

    def load_fingerprint_database(self):
        db_file = 'data/fingerprints.json'
        if os.path.exists(db_file):
            try:
                with open(db_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_fingerprint_database(self):
        os.makedirs('data', exist_ok=True)
        db_file = 'data/fingerprints.json'
        with open(db_file, 'w') as f:
            json.dump(self.enrolled_fingerprints, f, indent=2)

    def enroll_finger(self, location=None):
        if location is None:
            location = self.get_next_available_location()

        if location is None:
            print("No available storage locations")
            return None

        print(f"Starting fingerprint enrollment at location {location}")

        # First scan
        self.logger("Place finger on sensor...")
        if not self._wait_for_finger(timeout=10):
            self.logger("Finger not detected in time.")
            return None

        if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
            self.logger("Failed to convert first fingerprint image.")
            return None

        self.logger("Remove finger...")
        time.sleep(2)

        # Second scan
        self.logger("👉 Place the same finger again...")
        if not self._wait_for_finger(timeout=10):
            self.logger("Second scan failed: Finger not detected in time.")
            return None

        if self.finger.image_2_tz(2) != adafruit_fingerprint.OK:
            self.logger("Failed to convert second fingerprint image.")
            return None

        # Create and store model
        if self.finger.create_model() != adafruit_fingerprint.OK:
            self.logger("Failed to create fingerprint model.")
            return None

        if self.finger.store_model(location) != adafruit_fingerprint.OK:
            self.logger("Failed to store fingerprint.")
            return None

        self.enrolled_fingerprints[str(location)] = {
            'location': location,
            'enrolled_at': time.time()
        }
        self.save_fingerprint_database()

        self.logger(
            f" Fingerprint enrolled successfully at location {location}")
        return location

    def _wait_for_finger(self, timeout=10):
        start = time.time()
        while True:
            result = self.finger.get_image()
            if result == adafruit_fingerprint.OK:
                return True
            elif result == adafruit_fingerprint.NOFINGER:
                pass
            elif result == adafruit_fingerprint.IMAGEFAIL:
                self.logger(" Image capture failed")
                return False

            if time.time() - start > timeout:
                return False
            time.sleep(0.5)

    def search_finger(self):
        self.logger("Place your finger on the sensor...")
        if not self._wait_for_finger(timeout=10):
            self.logger("No finger detected")
            return None, None

        if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
            self.logger("Failed to convert image")
            return None, None

        if self.finger.finger_fast_search() == adafruit_fingerprint.OK:
            self.logger(
                f" Found at ID {self.finger.finger_id} with confidence {self.finger.confidence}")
            return self.finger.finger_id, self.finger.confidence

        self.logger("No match found")
        return None, None

    def delete_finger(self, location):
        if self.finger.delete_model(location) == adafruit_fingerprint.OK:
            self.enrolled_fingerprints.pop(str(location), None)
            self.save_fingerprint_database()
            self.logger(f"🗑️ Fingerprint at location {location} deleted")
            return True
        self.logger("Failed to delete fingerprint")
        return False

    def get_next_available_location(self):
        for i in range(1, 128):
            if str(i) not in self.enrolled_fingerprints:
                return i
        return None

    def get_fingerprint_count(self):
        try:
            return self.finger.count_templates()
        except Exception as e:
            self.logger(f"Error getting fingerprint count: {e}")
            return 0

    def get_system_info(self):
        try:
            return {
                'status': 'OK',
                'system_id': hex(self.finger.system_id),
                'library_size': self.finger.library_size,
                'security_level': self.finger.security_level,
                'device_address': hex(self.finger.device_address),
                'data_packet_size': self.finger.data_packet_size,
                'baudrate': self.finger.baudrate
            }
        except Exception as e:
            self.logger(f"Error getting system info: {e}")
            return {}

    def cleanup(self):
        if self.serial_connection:
            try:
                self.serial_connection.close()
                self.logger("Fingerprint reader connection closed")
            except Exception as e:
                self.logger(f"Error during cleanup: {e}")
