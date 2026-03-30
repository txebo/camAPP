import sys
from dataclasses import dataclass

import cv2

try:
    import pyvirtualcam
except ImportError:
    pyvirtualcam = None

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "camApp"
APP_VERSION = "0.1.0"


@dataclass(frozen=True)
class Resolution:
    name: str
    width: int
    height: int


class CameraWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                color: #333;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
            }
            QLabel {
                color: #333;
            }
            QPushButton {
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton#virtualCamBtn {
                background-color: #e74c3c;
                color: white;
                font-size: 14px;
            }
            QPushButton#virtualCamBtn:hover {
                background-color: #c0392b;
            }
            QPushButton#virtualCamBtnOn {
                background-color: #27ae60;
                color: white;
                font-size: 14px;
            }
            QPushButton#virtualCamBtnOn:hover {
                background-color: #229954;
            }
        """)

        self.cap = None
        self.virtual_cam = None
        self.virtual_cam_enabled = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.current_frame = None

        self.resolutions = [
            Resolution("640 x 480", 640, 480),
            Resolution("1280 x 720 (HD)", 1280, 720),
            Resolution("1920 x 1080 (Full HD)", 1920, 1080),
        ]

        self.init_ui()
        self.populate_camera_options()
        self.update_timer_interval(self.fps_spin.value())
        self.open_camera()
        self.timer.start()

    def init_ui(self):
        """Initialize the UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background-color: #f5f5f5;")

        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        left_layout = QVBoxLayout()

        preview_group = QGroupBox("Live Preview")
        preview_layout = QVBoxLayout()
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.reset_preview_style()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setText("Iniciando cámara...")
        self.video_label.setFont(QFont("Arial", 12))
        self.video_label.setScaledContents(False)
        preview_layout.addWidget(self.video_label)
        preview_group.setLayout(preview_layout)
        left_layout.addWidget(preview_group)

        right_layout = QVBoxLayout()

        camera_group = QGroupBox("Configuración")
        camera_group_layout = QVBoxLayout()

        camera_label = QLabel("📷 Cámara:")
        camera_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        camera_group_layout.addWidget(camera_label)

        self.camera_combo = QComboBox()
        self.camera_combo.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        self.camera_combo.currentIndexChanged.connect(self.open_camera)
        camera_group_layout.addWidget(self.camera_combo)

        resolution_label = QLabel("📐 Resolución:")
        resolution_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        camera_group_layout.addWidget(resolution_label)

        self.resolution_combo = QComboBox()
        for resolution in self.resolutions:
            self.resolution_combo.addItem(resolution.name, resolution)
        self.resolution_combo.setCurrentIndex(1)
        self.resolution_combo.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px;")
        self.resolution_combo.currentIndexChanged.connect(self.apply_camera_settings)
        camera_group_layout.addWidget(self.resolution_combo)

        fps_label = QLabel("⏱️ FPS:")
        fps_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        camera_group_layout.addWidget(fps_label)

        fps_layout = QHBoxLayout()
        self.fps_spin = QSpinBox()
        self.fps_spin.setMinimum(1)
        self.fps_spin.setMaximum(60)
        self.fps_spin.setValue(30)
        self.fps_spin.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 3px; width: 60px;")

        self.fps_label_value = QLabel("30 fps")
        self.fps_label_value.setFont(QFont("Arial", 10))
        self.fps_spin.valueChanged.connect(self.update_timer_interval)

        fps_layout.addWidget(self.fps_spin)
        fps_layout.addWidget(self.fps_label_value)
        fps_layout.addStretch()
        camera_group_layout.addLayout(fps_layout)

        camera_group_layout.addStretch()
        camera_group.setLayout(camera_group_layout)
        right_layout.addWidget(camera_group)

        virtual_group = QGroupBox("Cámara Virtual")
        virtual_layout = QVBoxLayout()

        self.status_label = QLabel("Status: ⚫ Offline")
        self.status_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #c0392b;")
        virtual_layout.addWidget(self.status_label)

        self.virtual_cam_button = QPushButton("🔴 Iniciar Cámara Virtual")
        self.virtual_cam_button.setObjectName("virtualCamBtn")
        self.virtual_cam_button.setMinimumHeight(45)
        self.virtual_cam_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.virtual_cam_button.clicked.connect(self.toggle_virtual_camera)
        virtual_layout.addWidget(self.virtual_cam_button)

        self.info_label = QLabel("Cámara virtual inactiva")
        self.info_label.setFont(QFont("Arial", 9))
        self.info_label.setStyleSheet("color: #666;")
        self.info_label.setWordWrap(True)
        virtual_layout.addWidget(self.info_label)

        virtual_group.setLayout(virtual_layout)
        right_layout.addWidget(virtual_group)
        right_layout.addStretch()

        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
        central_widget.setLayout(main_layout)

    def reset_preview_style(self):
        self.video_label.setStyleSheet("border: 2px solid #bbb; background-color: #000; border-radius: 4px;")

    def selected_resolution(self) -> Resolution:
        resolution = self.resolution_combo.currentData()
        if resolution is None:
            return self.resolutions[1]
        return resolution

    def update_timer_interval(self, fps: int):
        fps = max(1, int(fps))
        self.fps_label_value.setText(f"{fps} fps")
        self.timer.setInterval(max(1, round(1000 / fps)))
        self.apply_camera_settings()

    def populate_camera_options(self):
        current_selection = self.camera_combo.currentData()
        self.camera_combo.blockSignals(True)
        self.camera_combo.clear()

        for camera_index in range(5):
            capture = cv2.VideoCapture(camera_index)
            if capture.isOpened():
                self.camera_combo.addItem(f"Cámara {camera_index}", camera_index)
                capture.release()

        if self.camera_combo.count() == 0:
            self.camera_combo.addItem("Sin cámaras detectadas", None)
        elif current_selection is not None:
            match_index = self.camera_combo.findData(current_selection)
            if match_index >= 0:
                self.camera_combo.setCurrentIndex(match_index)

        self.camera_combo.blockSignals(False)

    def apply_camera_settings(self):
        if self.cap is None or not self.cap.isOpened():
            return

        resolution = self.selected_resolution()
        fps = self.fps_spin.value()
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution.height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)

    def open_camera(self):
        """Open the selected camera and apply current settings."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        camera_index = self.camera_combo.currentData()
        if camera_index is None:
            self.video_label.clear()
            self.video_label.setText("❌ No se detectaron cámaras disponibles")
            self.video_label.setStyleSheet("border: 2px solid #e74c3c; background-color: #ffe6e6; border-radius: 4px;")
            self.info_label.setText("✗ No se encontraron cámaras conectadas.")
            return

        self.cap = cv2.VideoCapture(int(camera_index))
        if not self.cap.isOpened():
            self.video_label.clear()
            self.video_label.setText("❌ No se pudo abrir la cámara seleccionada")
            self.video_label.setStyleSheet("border: 2px solid #e74c3c; background-color: #ffe6e6; border-radius: 4px;")
            self.info_label.setText(f"✗ No se pudo abrir la cámara {camera_index}.")
            return

        self.reset_preview_style()
        self.apply_camera_settings()
        resolution = self.selected_resolution()
        fps = self.fps_spin.value()
        if not self.virtual_cam_enabled:
            self.info_label.setText(
                f"Cámara física lista\nÍndice: {camera_index}\nResolución solicitada: {resolution.width}x{resolution.height} @ {fps}fps"
            )

    def update_frame(self):
        """Update frame from camera and show preview."""
        if self.cap is None or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            self.video_label.setText("⚠️ No se pudo leer un frame de la cámara")
            return

        self.current_frame = frame
        self.display_preview(frame)
        self.send_to_virtual_camera(frame)

    def display_preview(self, frame):
        """Display frame in preview label."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb_frame.shape
        bytes_per_line = channels * width
        qt_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(scaled_pixmap)

    def toggle_virtual_camera(self) -> None:
        if self.virtual_cam_enabled:
            self.stop_virtual_camera()
            return

        if pyvirtualcam is None:
            QMessageBox.warning(
                self,
                "Cámara Virtual",
                "pyvirtualcam no está instalado.\nInstala: pip install pyvirtualcam",
            )
            return

        resolution = self.selected_resolution()
        fps = self.fps_spin.value()

        try:
            self.virtual_cam = pyvirtualcam.Camera(
                width=resolution.width,
                height=resolution.height,
                fps=fps,
                fmt=pyvirtualcam.PixelFormat.BGR,
            )
            self.virtual_cam_enabled = True
            self.virtual_cam_button.setText("🟢 Detener Cámara Virtual")
            self.virtual_cam_button.setObjectName("virtualCamBtnOn")
            self.virtual_cam_button.setStyle(self.virtual_cam_button.style())
            self.status_label.setText("Status: 🟢 Online")
            self.status_label.setStyleSheet("color: #27ae60;")
            self.info_label.setText(
                f"✓ Cámara virtual activa\n{resolution.width}x{resolution.height} @ {fps}fps"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Cámara Virtual", f"Error al iniciar cámara virtual:\n{exc}")
            self.virtual_cam = None
            self.virtual_cam_enabled = False
            self.info_label.setText(f"✗ Error: {str(exc)[:80]}")
            self.status_label.setStyleSheet("color: #c0392b;")

    def stop_virtual_camera(self) -> None:
        if self.virtual_cam is not None:
            try:
                self.virtual_cam.close()
            except Exception:
                pass
        self.virtual_cam = None
        self.virtual_cam_enabled = False
        self.virtual_cam_button.setText("🔴 Iniciar Cámara Virtual")
        self.virtual_cam_button.setObjectName("virtualCamBtn")
        self.virtual_cam_button.setStyle(self.virtual_cam_button.style())
        self.status_label.setText("Status: ⚫ Offline")
        self.status_label.setStyleSheet("color: #c0392b;")
        self.info_label.setText("Cámara virtual inactiva")

    def send_to_virtual_camera(self, frame) -> None:
        if self.virtual_cam is None:
            return

        try:
            if frame.shape[1] != self.virtual_cam.width or frame.shape[0] != self.virtual_cam.height:
                frame = cv2.resize(
                    frame,
                    (self.virtual_cam.width, self.virtual_cam.height),
                    interpolation=cv2.INTER_LINEAR,
                )
            self.virtual_cam.send(frame)
            self.virtual_cam.sleep_until_next_frame()
        except Exception as exc:
            print(f"Error sending to virtual camera: {exc}")
            self.stop_virtual_camera()

    def closeEvent(self, event) -> None:
        self.timer.stop()
        self.stop_virtual_camera()
        if self.cap is not None:
            self.cap.release()
        event.accept()


def main(argv: list[str] | None = None) -> int:
    args = sys.argv if argv is None else argv
    app = QApplication(args)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    window = CameraWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
