import sys
from PyQt5.QtWidgets import QApplication
from ui import IronManHUD
from gesture_engine import GestureEngine

def main():
    # Initialize the GUI Application
    app = QApplication(sys.argv)
    
    # Initialize the HUD view
    hud_window = IronManHUD()
    
    # Initialize the Gesture Recognition Engine Thread
    engine = GestureEngine()
    
    # Attach engine to HUD so they can exchange frame and telemetry signals
    hud_window.set_engine_thread(engine)
    
    # Start capturing and processing gestures
    engine.start()
    
    # Display the holographic interface
    hud_window.show()
    
    # Execute application main loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()