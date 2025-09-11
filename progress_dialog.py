"""
Enhanced Progress Dialog for HALog
Native Windows styling with responsive design
"""

from PyQt5.QtWidgets import QProgressDialog, QProgressBar, QLabel, QVBoxLayout, QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class ProgressDialog(QProgressDialog):
    """Enhanced progress dialog with native Windows styling"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Processing...")
        self.setWindowModality(Qt.WindowModal)
        self.setMinimumWidth(400)
        self.setMinimumHeight(150)

        # Use native Windows styling
        self.setStyleSheet("""
            QProgressDialog {
                background-color: white;
                border: 1px solid #c0c0c0;
                font-family: 'Segoe UI';
                font-size: 9pt;
            }
            QProgressBar {
                border: 1px solid #c0c0c0;
                border-radius: 2px;
                text-align: center;
                background-color: #f0f0f0;
                color: #000000;
                font-size: 8pt;
                min-height: 16px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 1px;
            }
            QLabel {
                color: #000000;
                font-size: 9pt;
                padding: 4px;
            }
            QPushButton {
                background-color: #e1e1e1;
                border: 1px solid #adadad;
                padding: 6px 12px;
                border-radius: 2px;
                font-size: 9pt;
                min-width: 75px;
            }
            QPushButton:hover {
                background-color: #e5f1fb;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #cce4f7;
            }
        """)

        self.current_phase = "processing"
        self.current_phase_progress = 0

        # Setup initial state
        self.setRange(0, 100)
        self.setValue(0)
        self.setLabelText("Initializing...")
        
        # Ensure dialog stays visible and responsive
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
    
    def ensure_visible(self):
        """Ensure the dialog is visible and responsive"""
        if not self.isVisible():
            self.show()
        self.raise_()
        self.activateWindow()
        QApplication.processEvents()

    def set_phase(self, phase_name, initial_progress=0):
        """Set current processing phase"""
        phase_names = {
            "uploading": "Reading and uploading file...",
            "processing": "Processing data...",
            "finalizing": "Finalizing...",
            "saving": "Saving results...",
            "analyzing": "Analyzing data..."
        }

        self.current_phase = phase_name
        self.current_phase_progress = initial_progress

        label_text = phase_names.get(phase_name, f"{phase_name.title()}...")
        self.setLabelText(label_text)
        self.setValue(int(initial_progress))  # Ensure integer value
        
        # Ensure dialog is visible when setting phase
        self.ensure_visible()

    def update_progress(self, percentage, status_message="", lines_processed=0, 
                       total_lines=0, bytes_processed=0, total_bytes=0):
        """Update progress with detailed information"""
        self.setValue(min(100, max(0, int(percentage))))

        if status_message:
            self.setLabelText(status_message)
        
        # Ensure dialog is visible and on top
        if not self.isVisible():
            self.show()
        self.raise_()
        self.activateWindow()

        # Process events to keep UI responsive
        QApplication.processEvents()

    def mark_complete(self):
        """Mark processing as complete"""
        self.setValue(100)
        self.setLabelText("Complete!")
        self.ensure_visible()