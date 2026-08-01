# Holographic Gesture HUD (Iron Man Protocol)

A real-time, high-fidelity gesture control system inspired by Iron Man's holographic HUD interfaces. Built with **PyQt5**, **OpenCV**, and **MediaPipe Hands**, this application allows you to control your operating system touchlessly using hand gestures, all rendered inside a glowing cyber-themed dashboard.

---

## 🚀 Key Features

* **Unified Cyberpunk UI**: A dark-mode desktop HUD with neon cyan and magenta accents, glowing active state displays, and interactive telemetry counters.
* **Thread-Safe Architecture**: The gesture tracking runs in a dedicated background worker thread (`QThread`), keeping the PyQt5 UI responsive and preventing resource spikes.
* **Advanced Cursor Control**:
  * **Double Exponential Smoothing**: Drastically reduces hand jitter for precise pointer movements.
  * **Active Interaction Zone**: Maps hand movements within a highlighted central region of the camera to the full extent of the screen, eliminating physical strain.
* **Complex Gestures State Machine**:
  * **Cursor Navigation**: Point your index finger to steer the mouse pointer.
  * **Left Click & Drag**: Pinch your Index finger and Thumb. Hold the pinch to drag and drop windows or files.
  * **Right Click**: Pinch your Middle finger and Thumb.
  * **Vertical Scroll**: Raise Index, Middle, and Ring fingers. Move your hand up or down to scroll.
  * **Zoom Control**: Pinch your Thumb and Pinky. Move your hand horizontally to Zoom In or Zoom Out.
  * **Slide Navigation**: Open all fingers and sweep your hand quickly to the left or right to simulate PageUp/PageDown key actions.
* **Calibration & Toggles**: Dynamically adjust smoothing parameters, click distances, and toggle individual gestures on/off directly from the HUD.

---

## 🖐️ Gesture Reference Guide

| Gesture State | Hand Form | OS Action Simulated | Visual HUD Status |
|---|---|---|---|
| **Cursor Mode** | Index finger UP, others closed | Mouse pointer movement | Cursor Control |
| **Left Click** | Pinch Index Finger + Thumb | Left Click / Drag (Hold) | Left Dragging... / Click |
| **Right Click** | Pinch Middle Finger + Thumb | Right Click | Right Click Simulated |
| **Scroll Mode** | Index, Middle, Ring UP, Pinky closed | Vertical Mouse Scroll | Scrolling... |
| **Zoom Mode** | Pinch Pinky + Thumb | Zoom In/Out (`Ctrl` + `+` / `-`) | Zooming In / Zooming Out |
| **Swipe Mode** | Hand open, swift horizontal sweep | Page Up/Down (`PageUp` / `PageDown`) | Swipe Left / Swipe Right |

---

## 🛠️ Installation & Setup

1. **Clone & Navigate**:
   ```bash
   git clone https://github.com/Kathirvel005/Gesture-Control-Project.git
   cd Gesture-Control-Project
   ```

2. **Initialize Environment & Install Dependencies**:
   ```bash
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Launch the HUD**:
   ```bash
   python main.py
   ```

---

## 📂 Project Architecture

* **`main.py`**: Launches the main application thread and wires the processing worker and UI window together.
* **`gesture_engine.py`**: Captures raw camera feeds, tracks hand landmarks using MediaPipe, maps spatial locations to cursor coordinate outputs, filters noise, and issues PyAutoGUI instructions.
* **`ui.py`**: Implements the futuristic cyber-themed dashboard using PyQt5 widgets, custom stylesheets, sliders, and signal handlers.
