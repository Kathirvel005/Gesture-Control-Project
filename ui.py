import cv2
import sys
import numpy as np
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                             QFrame, QCheckBox, QSlider, QListWidget, 
                             QPushButton, QGroupBox, QGridLayout)
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import Qt, pyqtSlot

class IronManHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.engine_thread = None
        self.init_ui()

    def init_ui(self):
        # Configure Window
        self.setWindowTitle("F.R.I.D.A.Y. Holographic Gesture HUD")
        self.setGeometry(100, 100, 1100, 680)
        self.setMinimumSize(1000, 620)
        
        # Stylesheet: Sleek dark cyberpunk theme
        self.setStyleSheet("""
            QWidget {
                background-color: #050811;
                color: #A5C0F3;
                font-family: 'Consolas', 'Segoe UI', monospace;
            }
            QFrame#panel {
                background-color: rgba(10, 17, 34, 0.85);
                border: 2px solid #00F0FF;
                border-radius: 12px;
            }
            QFrame#panel:hover {
                border-color: #FF00A0;
            }
            QLabel {
                color: #A5C0F3;
            }
            QLabel#hud_title {
                color: #00F0FF;
                font-size: 20px;
                font-weight: bold;
                letter-spacing: 2px;
                border-bottom: 2px solid rgba(0, 240, 255, 0.3);
                padding-bottom: 5px;
            }
            QLabel#hud_subtitle {
                color: #FF00A0;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QLabel#gesture_display {
                color: #00F0FF;
                font-size: 26px;
                font-weight: bold;
                border: 1px solid rgba(0, 240, 255, 0.2);
                border-radius: 6px;
                padding: 10px;
                background-color: rgba(0, 240, 255, 0.05);
            }
            QGroupBox {
                border: 1px solid rgba(0, 240, 255, 0.3);
                border-radius: 8px;
                margin-top: 15px;
                font-weight: bold;
                color: #00F0FF;
                padding-top: 10px;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #00F0FF;
                border-radius: 3px;
                background: #050811;
            }
            QCheckBox::indicator:checked {
                background: #00F0FF;
                border-color: #00F0FF;
            }
            QSlider::groove:horizontal {
                border: 1px solid rgba(0, 240, 255, 0.3);
                height: 6px;
                background: #091122;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #FF00A0;
                border: 1px solid #FF00A0;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #00F0FF;
                border-color: #00F0FF;
            }
            QListWidget {
                background-color: rgba(9, 17, 34, 0.9);
                border: 1px solid rgba(0, 240, 255, 0.2);
                border-radius: 6px;
                color: #00F0FF;
                font-size: 11px;
            }
            QPushButton {
                background-color: rgba(0, 240, 255, 0.15);
                border: 1px solid #00F0FF;
                border-radius: 6px;
                color: #00F0FF;
                font-weight: bold;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #FF00A0;
                border-color: #FF00A0;
                color: #FFFFFF;
            }
        """)

        # Main Layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ----------------- LEFT SIDE PANEL -----------------
        left_panel = QFrame()
        left_panel.setObjectName("panel")
        left_panel_layout = QVBoxLayout(left_panel)
        left_panel_layout.setSpacing(12)
        left_panel_layout.setContentsMargins(15, 15, 15, 15)

        # Titles
        title_label = QLabel("F.R.I.D.A.Y. GESTURE HUD")
        title_label.setObjectName("hud_title")
        subtitle_label = QLabel("TACTICAL HAND INTERACTION PROTOCOL v2.0")
        subtitle_label.setObjectName("hud_subtitle")
        left_panel_layout.addWidget(title_label)
        left_panel_layout.addWidget(subtitle_label)

        # Gesture Status Box
        left_panel_layout.addWidget(QLabel("CURRENT DETECTED GESTURE:"))
        self.gesture_lbl = QLabel("No Hand Detected")
        self.gesture_lbl.setObjectName("gesture_display")
        self.gesture_lbl.setAlignment(Qt.AlignCenter)
        left_panel_layout.addWidget(self.gesture_lbl)

        # Stats Grid Box
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: rgba(0, 240, 255, 0.02); border-radius: 6px; padding: 5px;")
        stats_grid = QGridLayout(stats_frame)
        stats_grid.setSpacing(6)
        
        stats_grid.addWidget(QLabel("Target Status:"), 0, 0)
        self.target_status_lbl = QLabel("Standby 💤")
        self.target_status_lbl.setStyleSheet("color: #FF00A0; font-weight: bold;")
        stats_grid.addWidget(self.target_status_lbl, 0, 1)

        stats_grid.addWidget(QLabel("Frame FPS:"), 1, 0)
        self.fps_lbl = QLabel("0.0")
        self.fps_lbl.setStyleSheet("color: #00F0FF;")
        stats_grid.addWidget(self.fps_lbl, 1, 1)

        stats_grid.addWidget(QLabel("Cursor Coord:"), 2, 0)
        self.coord_lbl = QLabel("X: 0, Y: 0")
        self.coord_lbl.setStyleSheet("color: #A5C0F3;")
        stats_grid.addWidget(self.coord_lbl, 2, 1)
        
        left_panel_layout.addWidget(stats_frame)

        # Control Options Group
        control_group = QGroupBox("TACTICAL TOGGLES")
        control_group_layout = QVBoxLayout(control_group)
        
        self.mouse_cb = QCheckBox("Mouse Movement")
        self.mouse_cb.setChecked(True)
        self.mouse_cb.stateChanged.connect(self.toggle_mouse)
        control_group_layout.addWidget(self.mouse_cb)

        self.scroll_cb = QCheckBox("Scroll Simulation")
        self.scroll_cb.setChecked(True)
        self.scroll_cb.stateChanged.connect(self.toggle_scroll)
        control_group_layout.addWidget(self.scroll_cb)

        self.zoom_cb = QCheckBox("Zoom Control")
        self.zoom_cb.setChecked(True)
        self.zoom_cb.stateChanged.connect(self.toggle_zoom)
        control_group_layout.addWidget(self.zoom_cb)

        self.swipe_cb = QCheckBox("Swipe Actions")
        self.swipe_cb.setChecked(True)
        self.swipe_cb.stateChanged.connect(self.toggle_swipe)
        control_group_layout.addWidget(self.swipe_cb)
        
        left_panel_layout.addWidget(control_group)

        # Slider Box (Sensitivity & Smoothing)
        sliders_group = QGroupBox("HUD CALIBRATION")
        sliders_layout = QVBoxLayout(sliders_group)
        
        # Smoothing Slider
        sliders_layout.addWidget(QLabel("Smoothing (Cursor Jitter):"))
        self.smooth_slider = QSlider(Qt.Horizontal)
        self.smooth_slider.setMinimum(5)   # 0.05
        self.smooth_slider.setMaximum(95)  # 0.95
        self.smooth_slider.setValue(25)  # Default 0.25
        self.smooth_slider.valueChanged.connect(self.smooth_changed)
        sliders_layout.addWidget(self.smooth_slider)

        # Pinch Click Distance Slider
        sliders_layout.addWidget(QLabel("Pinch Trigger Threshold (px):"))
        self.click_slider = QSlider(Qt.Horizontal)
        self.click_slider.setMinimum(15)
        self.click_slider.setMaximum(60)
        self.click_slider.setValue(28)
        self.click_slider.valueChanged.connect(self.click_threshold_changed)
        sliders_layout.addWidget(self.click_slider)

        left_panel_layout.addWidget(sliders_group)

        # Action Log Window
        left_panel_layout.addWidget(QLabel("SYSTEM EVENT LOGGER:"))
        self.log_list = QListWidget()
        left_panel_layout.addWidget(self.log_list)

        clear_btn = QPushButton("CLEAR LOGGER LOGS")
        clear_btn.clicked.connect(self.log_list.clear)
        left_panel_layout.addWidget(clear_btn)

        # Adjust panel width ratio
        left_panel.setFixedWidth(380)
        main_layout.addWidget(left_panel)

        # ----------------- RIGHT SIDE VIDEO VIEW -----------------
        right_panel = QFrame()
        right_panel.setObjectName("panel")
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.setContentsMargins(10, 10, 10, 10)

        # Camera Display Label
        self.camera_lbl = QLabel("INITIALIZING CAMERA SYSTEM...")
        self.camera_lbl.setAlignment(Qt.AlignCenter)
        self.camera_lbl.setStyleSheet("""
            border: 2px solid rgba(0, 240, 255, 0.4);
            border-radius: 8px;
            background-color: #030409;
        """)
        self.camera_lbl.setMinimumSize(640, 480)
        right_panel_layout.addWidget(self.camera_lbl)

        # System Bar Status
        self.status_bar_lbl = QLabel("SYSTEM: SECURE // ONLINE // LISTENING")
        self.status_bar_lbl.setStyleSheet("""
            color: #00F0FF;
            font-size: 11px;
            padding: 5px;
            background-color: rgba(0, 240, 255, 0.05);
            border-radius: 4px;
            border: 1px solid rgba(0, 240, 255, 0.1);
        """)
        self.status_bar_lbl.setAlignment(Qt.AlignCenter)
        right_panel_layout.addWidget(self.status_bar_lbl)

        main_layout.addWidget(right_panel)
        self.setLayout(main_layout)

    def set_engine_thread(self, thread):
        self.engine_thread = thread
        
        # Connect signals
        self.engine_thread.frame_ready.connect(self.update_camera_frame)
        self.engine_thread.status_changed.connect(self.update_gesture_status)
        self.engine_thread.stats_updated.connect(self.update_hud_stats)

    @pyqtSlot(np.ndarray)
    def update_camera_frame(self, cv_img):
        # Convert OpenCV BGR to QImage RGB
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale image to fit the label widget
        scaled_pixmap = QPixmap.fromImage(qt_img).scaled(
            self.camera_lbl.width(), 
            self.camera_lbl.height(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.camera_lbl.setPixmap(scaled_pixmap)

    @pyqtSlot(str)
    def update_gesture_status(self, status):
        self.gesture_lbl.setText(status)
        
        # Dynamically change text colors based on gesture state
        if status in ["Scanning...", "No Hand Detected"]:
            self.gesture_lbl.setStyleSheet("color: #A5C0F3; background-color: rgba(165, 192, 243, 0.05); border-color: rgba(165, 192, 243, 0.2);")
        elif "Click" in status or "Dragging" in status:
            self.gesture_lbl.setStyleSheet("color: #FF00A0; background-color: rgba(255, 0, 160, 0.08); border-color: rgba(255, 0, 160, 0.3);")
            self.add_log_entry(f"Action: {status}")
        elif "Swipe" in status:
            self.gesture_lbl.setStyleSheet("color: #E2FF00; background-color: rgba(226, 255, 0, 0.08); border-color: rgba(226, 255, 0, 0.3);")
            self.add_log_entry(f"Action: {status}")
        else:
            self.gesture_lbl.setStyleSheet("color: #00F0FF; background-color: rgba(0, 240, 255, 0.08); border-color: rgba(0, 240, 255, 0.3);")

    @pyqtSlot(dict)
    def update_hud_stats(self, stats):
        # Update labels
        self.fps_lbl.setText(str(stats["fps"]))
        
        if stats["hand_detected"]:
            self.target_status_lbl.setText("TRACKING DETECTED 🎯")
            self.target_status_lbl.setStyleSheet("color: #00F0FF; font-weight: bold;")
        else:
            self.target_status_lbl.setText("Scanning... 💤")
            self.target_status_lbl.setStyleSheet("color: #FF00A0; font-weight: bold;")
            
        self.coord_lbl.setText(f"X: {stats['cursor_x']}, Y: {stats['cursor_y']}")

    def add_log_entry(self, message):
        # Get current time stamp
        timestamp = time.strftime("[%H:%M:%S] ")
        item_text = timestamp + message
        
        # Add to list widget (only if it's new/different from the last log entry)
        if self.log_list.count() > 0:
            last_item = self.log_list.item(self.log_list.count() - 1)
            if last_item.text().split("] ")[-1] == message:
                return
                
        self.log_list.addItem(item_text)
        self.log_list.scrollToBottom()
        
        # Keep logs list size capped to 15 entries
        while self.log_list.count() > 15:
            self.log_list.takeItem(0)

    # ------------ UI Controls & Slots Connections ------------
    def toggle_mouse(self, state):
        enabled = state == Qt.Checked
        if self.engine_thread:
            self.engine_thread.mouse_control_enabled = enabled
        self.add_log_entry(f"Mouse Control: {'ENABLED' if enabled else 'DISABLED'}")

    def toggle_scroll(self, state):
        enabled = state == Qt.Checked
        if self.engine_thread:
            self.engine_thread.scroll_control_enabled = enabled
        self.add_log_entry(f"Scroll Support: {'ENABLED' if enabled else 'DISABLED'}")

    def toggle_zoom(self, state):
        enabled = state == Qt.Checked
        if self.engine_thread:
            self.engine_thread.zoom_control_enabled = enabled
        self.add_log_entry(f"Zoom Gesture: {'ENABLED' if enabled else 'DISABLED'}")

    def toggle_swipe(self, state):
        enabled = state == Qt.Checked
        if self.engine_thread:
            self.engine_thread.swipe_control_enabled = enabled
        self.add_log_entry(f"Swipe Support: {'ENABLED' if enabled else 'DISABLED'}")

    def smooth_changed(self):
        val = self.smooth_slider.value() / 100.0
        if self.engine_thread:
            self.engine_thread.smoothing = val
        self.add_log_entry(f"Smoothing set to {val}")

    def click_threshold_changed(self):
        val = self.click_slider.value()
        if self.engine_thread:
            self.engine_thread.click_threshold = val
        self.add_log_entry(f"Pinch Threshold set to {val}px")

    def closeEvent(self, event):
        # Graceful cleanup of thread when UI closes
        if self.engine_thread:
            self.engine_thread.stop()
        event.accept()
        sys.exit(0)

if __name__ == "__main__":
    import time
    app = QApplication(sys.argv)
    window = IronManHUD()
    window.show()
    sys.exit(app.exec_())