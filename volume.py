import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QSlider, QPushButton, QGraphicsDropShadowEffect, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PyQt5.QtGui import QColor, QFont
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from comtypes import CLSCTX_ALL


def get_sessions():
    return AudioUtilities.GetAllSessions()


def set_master_volume(level):
    for session in get_sessions():
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        volume.SetMasterVolume(level, None)


def get_master_volume():
    vols = []
    for session in get_sessions():
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        vols.append(volume.GetMasterVolume())
    return sum(vols) / len(vols) if vols else 0


def mute_all(state):
    for session in get_sessions():
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        volume.SetMute(state, None)


class VolumeControl(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.init_ui()
        self.animate_in()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Glass-like card
        self.card = QWidget()
        self.card.setStyleSheet("""
            background-color: rgba(25, 25, 25, 150);
            border-radius: 20px;
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 0)
        self.card.setGraphicsEffect(shadow)

        # Header with close button
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 10)
        header.setSpacing(0)

        spacer = QLabel("")  # to push close button to right
        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: transparent;
                font-size: 18px;
                border: none;
            }
            QPushButton:hover {
                color: #ff5555;
            }
        """)
        close_btn.clicked.connect(self.close)

        header.addWidget(spacer)
        header.addWidget(close_btn)

        # Inner layout
        inner = QVBoxLayout()
        inner.setSpacing(15)
        inner.setContentsMargins(40, 30, 40, 40)

        self.label = QLabel("Volume")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; font-size: 22px;")
        self.label.setFont(QFont("SF Pro Display", 18))

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(int(get_master_volume() * 100))
        self.slider.valueChanged.connect(self.on_volume_change)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255,255,255,0.15);
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: rgba(255,255,255,0.7);
                border-radius: 4px;
            }
        """)

        self.percent = QLabel(f"{self.slider.value()}%")
        self.percent.setAlignment(Qt.AlignCenter)
        self.percent.setStyleSheet("color: #CCCCCC; font-size: 16px;")

        self.mute_btn = QPushButton("Mute")
        self.mute_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 10px;
                color: white;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.2);
            }
        """)
        self.mute_btn.clicked.connect(self.toggle_mute)

        inner.addLayout(header)
        inner.addWidget(self.label)
        inner.addWidget(self.slider)
        inner.addWidget(self.percent)
        inner.addWidget(self.mute_btn)
        self.card.setLayout(inner)
        layout.addWidget(self.card)
        self.setLayout(layout)

        self.resize(350, 230)
        self.muted = False

    def on_volume_change(self):
        val = self.slider.value()
        self.percent.setText(f"{val}%")
        set_master_volume(val / 100)

    def toggle_mute(self):
        self.muted = not self.muted
        mute_all(self.muted)
        self.mute_btn.setText("Unmute" if self.muted else "Mute")
        self.card.setStyleSheet(
            f"background-color: rgba(25,25,25,{80 if self.muted else 150}); border-radius: 20px;"
        )

    def animate_in(self):
        screen = QApplication.desktop().availableGeometry()
        start_y = 0
        end_y = screen.height() - 1000  # slightly higher than before
        self.setGeometry(screen.width() - 400, start_y, 350, 230)

        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(500)
        self.anim.setStartValue(QRect(screen.width() - 400, start_y, 350, 230))
        self.anim.setEndValue(QRect(screen.width() - 400, end_y, 350, 230))
        self.anim.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = VolumeControl()
    win.show()
    sys.exit(app.exec_())
