import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class IronManUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Iron Man Interface")
        self.setGeometry(100, 100, 800, 600)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.label = QLabel("IRON MAN SYSTEM", self)
        self.label.setFont(QFont("Arial", 24))
        self.label.setStyleSheet("color: cyan;")
        self.label.move(250, 50)

        self.status = QLabel("Gesture: None", self)
        self.status.setFont(QFont("Arial", 18))
        self.status.setStyleSheet("color: red;")
        self.status.move(250, 120)

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(500)

    def animate(self):
        self.status.setText("System Active 🔥")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IronManUI()
    window.show()
    sys.exit(app.exec_())