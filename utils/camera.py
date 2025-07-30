import os
import cv2
import json
import time
import numpy as np
from datetime import datetime

from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Install `face_recognition` with: pip install face_recognition")


class CameraHandler:
    _instance = None  # Singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CameraHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self, camera_index=0, widget_size=(640, 480)):
        if hasattr(self, 'initialized') and self.initialized:
            return  # Already initialized

        self.camera_index = camera_index
        self.widget_size = widget_size
        self.cap = cv2.VideoCapture(self.camera_index)
        self.frame = None
        self.texture = None
        self.face_encodings_db = self.load_face_database()

        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")

        # Set camera resolution for better quality
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Create image widget with specified size
        self.image_widget = Image(
            size_hint_y=None,
            height=widget_size[1],
            size_hint_x=None,
            width=widget_size[0]
        )
        Clock.schedule_interval(self.update, 1.0 / 30.0)  # 30 FPS

        os.makedirs('data/faces', exist_ok=True)

        self.initialized = True
        print(f"[INFO] CameraHandler initialized with size {widget_size}")

    def update_widget_size(self, width, height):
        """Update the camera widget size"""
        self.widget_size = (width, height)
        self.image_widget.width = width
        self.image_widget.height = height

    def update(self, dt):
        """Read from camera and update Kivy image widget"""
        ret, frame = self.cap.read()
        if not ret:
            return

        self.frame = frame
        # Resize frame to match widget size for better display
        resized_frame = cv2.resize(frame, self.widget_size)

        buf = cv2.flip(resized_frame, 0).tobytes()
        texture = Texture.create(
            size=(resized_frame.shape[1], resized_frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.image_widget.texture = texture

    def capture_face(self, name):
        """Capture current frame, save it, and extract face encoding"""
        if self.frame is None:
            print("[ERROR] No frame to capture")
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name.replace(' ', '_')}_{timestamp}.jpg"
        image_path = os.path.join('data/faces', filename)

        # Save frame
        cv2.imwrite(image_path, self.frame)
        print(f"[INFO] Image saved at {image_path}")

        if FACE_RECOGNITION_AVAILABLE:
            rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(
                rgb_frame, face_locations)

            if face_encodings:
                print("[INFO] Face encoding extracted.")
                self.face_encodings_db[name] = {
                    'encodings': [face_encodings[0].tolist()],
                    'image': image_path
                }
                self.save_face_database()
            else:
                print("[WARNING] No face found in captured image")

        return image_path

    def load_face_database(self):
        """Load face encodings database from file"""
        db_file = 'data/face_encodings.json'
        if os.path.exists(db_file):
            try:
                with open(db_file, 'r') as f:
                    data = json.load(f)
                for person_id, person_data in data.items():
                    if 'encodings' in person_data:
                        person_data['encodings'] = [
                            np.array(enc) for enc in person_data['encodings']]
                return data
            except Exception as e:
                print(f"Error loading face database: {e}")
        return {}

    def save_face_database(self):
        """Save face encodings database to file"""
        db_file = 'data/face_encodings.json'
        serializable_data = {}
        for person_id, person_data in self.face_encodings_db.items():
            serializable_data[person_id] = person_data.copy()
            if 'encodings' in person_data:
                serializable_data[person_id]['encodings'] = [
                    enc.tolist() if isinstance(enc, np.ndarray) else enc
                    for enc in person_data['encodings']
                ]

        with open(db_file, 'w') as f:
            json.dump(serializable_data, f, indent=2)

    def release(self):
        """Release camera and stop update loop"""
        Clock.unschedule(self.update)
        if self.cap and self.cap.isOpened():
            self.cap.release()
        print("[INFO] Camera released.")
