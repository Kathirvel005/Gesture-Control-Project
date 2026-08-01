import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import math
import time
import os
from PyQt5.QtCore import QThread, pyqtSignal

# Set fail-safe to True to allow user to abort by moving mouse to corner
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01

class GestureEngine(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    status_changed = pyqtSignal(str)
    stats_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.is_running = True
        
        # UI Configurable variables
        self.mouse_control_enabled = True
        self.scroll_control_enabled = True
        self.zoom_control_enabled = True
        self.swipe_control_enabled = True
        
        self.smoothing = 0.25
        self.click_threshold = 28
        self.scroll_speed = 30
        
        # Screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Mouse smoothing state
        self.prev_screen_x = None
        self.prev_screen_y = None
        
        # Click state machine
        self.is_left_clicked = False
        self.is_right_clicked = False
        
        # Gesture tracking state
        self.last_scroll_y = None
        self.last_zoom_x = None
        self.last_swipe_time = 0
        self.hand_x_history = []
        self.hand_history_limit = 10
        
        # Active Zone in camera frame (640x480)
        self.x_min, self.x_max = 120, 520
        self.y_min, self.y_max = 96, 384

    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Import MediaPipe Tasks API
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        # Resolve absolute path for hand_landmarker.task
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, 'hand_landmarker.task')

        # Configure Hand Landmarker Options
        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        detector = vision.HandLandmarker.create_from_options(options)
        prev_time = time.time()

        while self.is_running:
            success, frame = cap.read()
            if not success:
                self.msleep(10)
                continue

            # Mirror the frame horizontally for intuitive self-tracking
            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape

            # Convert to RGB for MediaPipe Tasks
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Wrap numpy RGB array as MediaPipe Image
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.array(rgb_frame))
            
            # Calculate timestamp in milliseconds
            timestamp_ms = int(time.time() * 1000)
            
            # Process frame using the Tasks API
            result = detector.detect_for_video(mp_image, timestamp_ms)

            gesture_status = "Scanning..."
            hand_detected = False
            fps = 0.0

            # Calculate FPS
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time) if curr_time - prev_time > 0 else 0
            prev_time = curr_time

            # Draw HUD boundaries (futuristic corners)
            self.draw_hud_overlay(frame)

            if result.hand_landmarks and result.handedness:
                hand_detected = True
                hand_landmarks = result.hand_landmarks[0] # List of NormalizedLandmark
                # Handedness category name is 'Left' or 'Right'
                handedness = result.handedness[0][0].category_name

                # Convert landmarks to pixel values
                landmarks_px = []
                for lm in hand_landmarks:
                    landmarks_px.append((int(lm.x * w), int(lm.y * h)))

                # Detect fingers state [Thumb, Index, Middle, Ring, Pinky] (1 = up, 0 = down)
                fingers = self.get_fingers_state(hand_landmarks, handedness)
                
                # Extract key joint positions
                thumb_tip = landmarks_px[4]
                index_tip = landmarks_px[8]
                middle_tip = landmarks_px[12]
                pinky_tip = landmarks_px[20]
                index_mcp = landmarks_px[5] # Used for swipe velocity tracking

                # 1. Left Click & Right Click distance calculations
                left_click_dist = math.hypot(thumb_tip[0] - index_tip[0], thumb_tip[1] - index_tip[1])
                right_click_dist = math.hypot(thumb_tip[0] - middle_tip[0], thumb_tip[1] - middle_tip[1])
                zoom_dist = math.hypot(thumb_tip[0] - pinky_tip[0], thumb_tip[1] - pinky_tip[1])

                # 2. Gesture Mode Classification
                # Cursor Mode: Index finger is up, middle/ring/pinky are down
                is_cursor_mode = fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0
                
                # Scroll Mode: Index, Middle, Ring fingers up, Pinky down
                is_scroll_mode = fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0

                # Zoom Mode: Thumb & Pinky pinching
                is_zoom_mode = zoom_dist < self.click_threshold

                # Swipe detection (Hand wide open: all 5 fingers up)
                is_swipe_candidate = fingers == [1, 1, 1, 1, 1]

                # 3. Action Executions
                if is_cursor_mode and self.mouse_control_enabled:
                    gesture_status = "Cursor Control"
                    # Map index tip coordinates relative to Active Zone
                    ix, iy = index_tip
                    
                    # Clamp index tip inside active zone
                    ix_clamped = max(self.x_min, min(ix, self.x_max))
                    iy_clamped = max(self.y_min, min(iy, self.y_max))
                    
                    # Convert to normalized coordinates relative to active zone
                    norm_x = (ix_clamped - self.x_min) / (self.x_max - self.x_min)
                    norm_y = (iy_clamped - self.y_min) / (self.y_max - self.y_min)
                    
                    # Map to screen dimensions
                    target_x = int(norm_x * self.screen_width)
                    target_y = int(norm_y * self.screen_height)
                    
                    # Smooth cursor movement
                    if self.prev_screen_x is None:
                        self.prev_screen_x, self.prev_screen_y = target_x, target_y
                    else:
                        self.prev_screen_x = self.prev_screen_x + (target_x - self.prev_screen_x) * self.smoothing
                        self.prev_screen_y = self.prev_screen_y + (target_y - self.prev_screen_y) * self.smoothing
                    
                    try:
                        pyautogui.moveTo(int(self.prev_screen_x), int(self.prev_screen_y))
                    except pyautogui.FailSafeException:
                        gesture_status = "Failsafe Triggered"
                    
                    # Left Click Pinch checking in Cursor Mode
                    if left_click_dist < self.click_threshold:
                        if not self.is_left_clicked:
                            try:
                                pyautogui.mouseDown()
                                self.is_left_clicked = True
                            except Exception:
                                pass
                        gesture_status = "Left Dragging..."
                        cv2.circle(frame, index_tip, 12, (0, 255, 0), -1) # Glowing green circle for clicking
                    else:
                        if self.is_left_clicked:
                            try:
                                pyautogui.mouseUp()
                                self.is_left_clicked = False
                            except Exception:
                                pass
                        cv2.circle(frame, index_tip, 8, (255, 255, 0), 2) # Normal cursor indicator
                        
                elif is_scroll_mode and self.scroll_control_enabled:
                    gesture_status = "Scroll Mode"
                    # Track vertical movement using index finger tip
                    iy = index_tip[1]
                    if self.last_scroll_y is None:
                        self.last_scroll_y = iy
                    else:
                        dy = iy - self.last_scroll_y
                        if abs(dy) > 15:
                            # If moving down (dy > 0), scroll down (negative in PyAutoGUI)
                            scroll_amount = -int(dy * 1.5)
                            try:
                                pyautogui.scroll(scroll_amount)
                            except Exception:
                                pass
                            self.last_scroll_y = iy
                            gesture_status = "Scrolling..."
                            
                elif is_zoom_mode and self.zoom_control_enabled:
                    gesture_status = "Zoom Mode"
                    ix = index_tip[0]
                    if self.last_zoom_x is None:
                        self.last_zoom_x = ix
                    else:
                        dx = ix - self.last_zoom_x
                        if abs(dx) > 30:
                            if dx > 0:
                                try:
                                    pyautogui.hotkey('ctrl', '+')
                                except Exception:
                                    pass
                                gesture_status = "Zooming In 🔎"
                            else:
                                try:
                                    pyautogui.hotkey('ctrl', '-')
                                except Exception:
                                    pass
                                gesture_status = "Zooming Out 🔍"
                            self.last_zoom_x = ix
                            
                elif is_swipe_candidate and self.swipe_control_enabled:
                    gesture_status = "System Standby"
                    # Track horizontal hand speed for swipe gesture
                    self.hand_x_history.append((time.time(), index_mcp[0]))
                    if len(self.hand_x_history) > self.hand_history_limit:
                        self.hand_x_history.pop(0)
                        
                    # Calculate velocity if we have enough points
                    if len(self.hand_x_history) >= 4 and (time.time() - self.last_swipe_time) > 1.5:
                        dt = self.hand_x_history[-1][0] - self.hand_x_history[0][0]
                        dx = self.hand_x_history[-1][1] - self.hand_x_history[0][1]
                        if dt > 0:
                            velocity = dx / dt
                            if abs(velocity) > 600: # Threshold for swift swipe
                                if velocity > 0:
                                    gesture_status = "Swipe Right 👉"
                                    try:
                                        pyautogui.press('pagedown')
                                    except Exception:
                                        pass
                                else:
                                    gesture_status = "Swipe Left 👈"
                                    try:
                                        pyautogui.press('pageup')
                                    except Exception:
                                        pass
                                self.last_swipe_time = time.time()
                                self.hand_x_history.clear()
                else:
                    # Reset tracker states when not in gesture modes
                    self.prev_screen_x, self.prev_screen_y = None, None
                    self.last_scroll_y = None
                    self.last_zoom_x = None
                    if self.is_left_clicked:
                        try:
                            pyautogui.mouseUp()
                        except Exception:
                            pass
                        self.is_left_clicked = False
                    gesture_status = "Neutral"

                # Check Right Click (Index & middle open, thumb pinched with middle)
                if fingers[2] == 1 and right_click_dist < self.click_threshold:
                    if not self.is_right_clicked:
                        try:
                            pyautogui.rightClick()
                            self.is_right_clicked = True
                        except Exception:
                            pass
                        gesture_status = "Right Click Simulated"
                else:
                    self.is_right_clicked = False

                # Draw High-Tech Neon Landmarks
                self.draw_hologram_hand(frame, landmarks_px, fingers)

            else:
                # Reset states when hand goes out of frame
                self.prev_screen_x, self.prev_screen_y = None, None
                self.last_scroll_y = None
                self.last_zoom_x = None
                if self.is_left_clicked:
                    try:
                        pyautogui.mouseUp()
                    except Exception:
                        pass
                    self.is_left_clicked = False
                gesture_status = "No Hand Detected"

            # Emit final frame and signals
            self.frame_ready.emit(frame)
            self.status_changed.emit(gesture_status)
            self.stats_updated.emit({
                "fps": round(fps, 1),
                "hand_detected": hand_detected,
                "cursor_x": int(self.prev_screen_x) if self.prev_screen_x else 0,
                "cursor_y": int(self.prev_screen_y) if self.prev_screen_y else 0,
                "left_click": self.is_left_clicked,
                "right_click": self.is_right_clicked
            })

            self.msleep(15) # Avoid CPU usage spikes (approx 60 fps limit)

        cap.release()
        detector.close()

    def get_fingers_state(self, hand_landmarks, handedness):
        tips = [4, 8, 12, 16, 20]
        joints = [3, 6, 10, 14, 18]
        fingers = []

        # Thumb logic (dependent on Left/Right classification)
        is_right = handedness == "Right"
        thumb_tip_x = hand_landmarks[4].x
        thumb_ip_x = hand_landmarks[3].x

        if is_right:
            thumb_up = thumb_tip_x > thumb_ip_x
        else:
            thumb_up = thumb_tip_x < thumb_ip_x
        fingers.append(1 if thumb_up else 0)

        # Other 4 fingers
        for tip, joint in zip(tips[1:], joints[1:]):
            if hand_landmarks[tip].y < hand_landmarks[joint].y:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def draw_hud_overlay(self, frame):
        # Draw target corners of the Active Zone (holographic cyan style)
        color = (255, 255, 0) # Cyan (BGR: Blue=255, Green=255, Red=0)
        thickness = 2
        length = 20

        # Draw full bounding box with a dotted/semi-transparent feel
        cv2.rectangle(frame, (self.x_min, self.y_min), (self.x_max, self.y_max), (50, 50, 0), 1)

        # Top-Left Corner
        cv2.line(frame, (self.x_min, self.y_min), (self.x_min + length, self.y_min), color, thickness)
        cv2.line(frame, (self.x_min, self.y_min), (self.x_min, self.y_min + length), color, thickness)
        # Top-Right Corner
        cv2.line(frame, (self.x_max, self.y_min), (self.x_max - length, self.y_min), color, thickness)
        cv2.line(frame, (self.x_max, self.y_min), (self.x_max, self.y_min + length), color, thickness)
        # Bottom-Left Corner
        cv2.line(frame, (self.x_min, self.y_max), (self.x_min + length, self.y_max), color, thickness)
        cv2.line(frame, (self.x_min, self.y_max), (self.x_min, self.y_max - length), color, thickness)
        # Bottom-Right Corner
        cv2.line(frame, (self.x_max, self.y_max), (self.x_max - length, self.y_max), color, thickness)
        cv2.line(frame, (self.x_max, self.y_max), (self.x_max, self.y_max - length), color, thickness)

        # Draw HUD text labels
        cv2.putText(frame, "ACTIVE INTERACTION ZONE", (self.x_min + 5, self.y_min - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)

    def draw_hologram_hand(self, frame, landmarks_px, fingers):
        # Connections array mapping start to end index of joints
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4), # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8), # Index
            (5, 9), (9, 10), (10, 11), (11, 12), # Middle
            (9, 13), (13, 14), (14, 15), (15, 16), # Ring
            (13, 17), (17, 18), (18, 19), (19, 20), # Pinky
            (0, 17) # Wrist to Pinky
        ]

        # Draw glowing neon connecting lines
        glow_color = (255, 100, 0) # Electric neon blue (BGR: Blue=255, Green=100, Red=0)
        core_color = (255, 255, 255) # Pure white core

        for start, end in connections:
            cv2.line(frame, landmarks_px[start], landmarks_px[end], glow_color, 3, cv2.LINE_AA)
            cv2.line(frame, landmarks_px[start], landmarks_px[end], core_color, 1, cv2.LINE_AA)

        # Draw joints
        for idx, pt in enumerate(landmarks_px):
            # Make tip nodes slightly bigger and highlighted if finger is up
            is_tip = idx in [4, 8, 12, 16, 20]
            finger_idx = [4, 8, 12, 16, 20].index(idx) if is_tip else -1
            
            if is_tip and fingers[finger_idx] == 1:
                cv2.circle(frame, pt, 7, (0, 180, 255), -1, cv2.LINE_AA) # Bright orange tip
                cv2.circle(frame, pt, 9, (0, 100, 255), 2, cv2.LINE_AA) # Double ring
            else:
                cv2.circle(frame, pt, 4, glow_color, -1, cv2.LINE_AA)
                cv2.circle(frame, pt, 6, core_color, 1, cv2.LINE_AA)

    def stop(self):
        self.is_running = False
        self.wait()
