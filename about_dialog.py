from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QTabWidget,
    QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sys
import platform


class AboutDialog(QDialog):
    """
    Professional about dialog with comprehensive application information
    Developed by Tanmay Pandey - gobioeng.com
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Auto-detect version from main module
        self.app_version = self._get_app_version()
        self.setupUI()
    
    def _get_app_version(self):
        """Auto-detect application version"""
        try:
            # Try to import version from main module
            import main
            if hasattr(main, 'APP_VERSION'):
                return main.APP_VERSION
        except ImportError:
            pass
        
        # Fallback to default version
        return "0.0.1"

    def setupUI(self):
        """Setup modern about dialog UI with enhanced styling"""
        self.setWindowTitle("About HALog")
        self.setModal(True)
        self.setFixedSize(600, 500)  # Larger for better content display
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Apply modern CSS styling
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 1px solid #dee2e6;
                border-radius: 12px;
            }
            QLabel {
                color: #212529;
                font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
            }
            QTabWidget::pane {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 16px;
            }
            QTabBar::tab {
                background: #e9ecef;
                border: 1px solid #dee2e6;
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 6px 6px 0 0;
                font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
                font-weight: 500;
                color: #495057;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
                color: #0d6efd;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background: #f8f9fa;
            }
            QPushButton {
                background: #0d6efd;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
                font-weight: 500;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: #0b5ed7;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: #0a58ca;
                transform: translateY(0px);
            }
            QTextBrowser {
                background: white;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
                line-height: 1.4;
            }
        """)

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        self.setLayout(layout)

        # Modern Header section with gradient background
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #0d6efd, stop:1 #6610f2);
                border-radius: 10px;
                padding: 16px;
                margin-bottom: 8px;
            }
            QLabel {
                color: white;
                background: transparent;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 16, 16, 16)

        # Modern logo using text styling
        logo_label = QLabel("HA[Log]")
        logo_label.setFont(QFont("Calibri", 24, QFont.Bold))
        logo_label.setStyleSheet("""
            color: white;
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            padding: 8px 12px;
            font-weight: bold;
        """)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedSize(120, 50)
        header_layout.addWidget(logo_label)

        # Application info with modern styling
        app_info_layout = QVBoxLayout()

        app_name = QLabel("LINAC Log Analysis System")
        app_name.setFont(QFont("Calibri", 18, QFont.Bold))
        app_name.setStyleSheet("color: white; margin-bottom: 4px; font-weight: 600;")
        app_info_layout.addWidget(app_name)

        version_label = QLabel(f"Version {self.app_version} • Professional Edition")
        version_label.setFont(QFont("Calibri", 11))
        version_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); margin-bottom: 2px;")
        app_info_layout.addWidget(version_label)

        developer_label = QLabel("Developed by Tanmay Pandey")
        developer_label.setFont(QFont("Calibri", 10))
        developer_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        app_info_layout.addWidget(developer_label)

        company_label = QLabel("gobioeng.com - Engineering Solutions")
        company_label.setFont(QFont("Calibri", 10))
        company_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        app_info_layout.addWidget(company_label)

        header_layout.addLayout(app_info_layout)
        header_layout.addStretch()

        layout.addWidget(header_widget)

        # Tab widget for different information sections
        tab_widget = QTabWidget()

        # About tab
        about_tab = self.create_about_tab()
        tab_widget.addTab(about_tab, "About")

        # Features tab
        features_tab = self.create_features_tab()
        tab_widget.addTab(features_tab, "Features")

        # System info tab
        system_tab = self.create_system_info_tab()
        tab_widget.addTab(system_tab, "System")

        layout.addWidget(tab_widget)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """
        )
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)

        # Apply professional styling
        self.setStyleSheet(
            """
            QDialog {
                background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #3498db;
            }
        """
        )

    def create_about_tab(self):
        """Create the about tab content with proper developer attribution"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        description = QTextBrowser()
        description.setHtml(
            """
        <h3>LINAC Log Analysis System</h3>
        <p>HALog is a professional desktop application designed for monitoring and analyzing 
        machine log, water system parameters from Linear Accelerator (LINAC) medical devices.</p>
        
        <h4>Key Capabilities:</h4>
        <ul>
            <li><b>Advanced Log Parsing:</b> Intelligent parsing of complex LINAC log files with 
            unified parameter mapping</li>
            <li><b>Real-time Analysis:</b> Comprehensive statistical analysis and anomaly detection</li>
            <li><b>Professional Visualization:</b> Interactive trend charts and data visualization</li>
            <li><b>Data Quality Assessment:</b> Automated quality scoring and validation</li>
        </ul>
        
        <h4>Developer Information:</h4>
        <p><b>Lead Developer:</b> Tanmay Pandey</p>
        <p><b>Company:</b> gobioeng.com</p>
        <p>Tanmay Pandey specializes in biomedical engineering solutions, providing innovative 
        software tools for LINAC and other medical device troubleshooting and monitoring.
        Explore biomedical engineering resources, news, career opportunities, and expert
        insights for students, educators, and job seekers.</p>
        
        <p><b>Website:</b> <a href="https://www.gobioeng.com">gobioeng.com</a></p>
        <p><b>Support:</b> For technical support and inquiries, please visit our website.</p>
        
        <hr>
        <p><i>© 2025 Tanmay Pandey / gobioeng.com. All rights reserved.</i></p>
        """
        )
        description.setOpenExternalLinks(True)
        description.setStyleSheet("border: none; background: transparent;")

        layout.addWidget(description)
        return widget

    def create_features_tab(self):
        """Create the enhanced features tab content with comprehensive app capabilities"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        features = QTextBrowser()
        features.setHtml(
            """
        <div style="font-family: 'Calibri', 'Segoe UI', Arial, sans-serif; line-height: 1.5;">
        
        <h3 style="color: #0d6efd; font-weight: 600; margin-bottom: 16px;">🚀 Core Application Features</h3>
        
        <h4 style="color: #6f42c1; font-weight: 500; margin-top: 20px;">📊 Data Analysis & Visualization</h4>
        <ul style="margin-left: 16px;">
            <li><b>Interactive Dual Graphs:</b> Side-by-side parameter comparison with time synchronization</li>
            <li><b>Real-time Plotting:</b> Live updates with matplotlib integration and Qt5 backend</li>
            <li><b>Water System Monitoring:</b> Flow rates, pressures, and cooling parameters</li>
            <li><b>Voltage Analysis:</b> Multi-channel voltage monitoring with trend detection</li>
            <li><b>Statistical Dashboard:</b> Fault statistics, parameter trends, and quality metrics</li>
        </ul>
        
        <h4 style="color: #6f42c1; font-weight: 500; margin-top: 20px;">🔍 Advanced LINAC Log Processing</h4>
        <ul style="margin-left: 16px;">
            <li><b>Unified Parser:</b> Intelligent log parsing with automatic parameter mapping</li>
            <li><b>Multi-format Support:</b> HALfault.txt, TBFault.txt, and custom log formats</li>
            <li><b>Data Quality Assessment:</b> Automated scoring with confidence intervals</li>
            <li><b>Background Processing:</b> Worker threads for responsive UI during heavy operations</li>
            <li><b>Progress Tracking:</b> Real-time progress with ETA and performance monitoring</li>
        </ul>
        
        <h4 style="color: #6f42c1; font-weight: 500; margin-top: 20px;">💾 Database & Performance</h4>
        <ul style="margin-left: 16px;">
            <li><b>SQLite Integration:</b> Efficient data storage with automatic backup management</li>
            <li><b>Startup Optimization:</b> Smart caching and change detection for faster launches</li>
            <li><b>Memory Management:</b> Optimized for large datasets with chunked processing</li>
            <li><b>Tab Caching:</b> Intelligent UI caching with 5-minute invalidation cycles</li>
        </ul>
        
        <h4 style="color: #6f42c1; font-weight: 500; margin-top: 20px;">🎨 Professional Interface</h4>
        <ul style="margin-left: 16px;">
            <li><b>Modern Design:</b> Windows 11 Fluent-style interface with Calibri fonts</li>
            <li><b>Tabbed Workspace:</b> Dashboard, Water System, Voltages, and Analysis tabs</li>
            <li><b>Interactive Controls:</b> Parameter selection, graph updates, and zoom functionality</li>
            <li><b>Responsive Layout:</b> Adaptive sizing for different screen resolutions</li>
            <li><b>About Dialog:</b> Comprehensive app information with modern CSS styling</li>
        </ul>
        
        <h4 style="color: #6f42c1; font-weight: 500; margin-top: 20px;">⚡ Technical Excellence</h4>
        <ul style="margin-left: 16px;">
            <li><b>PyQt5 Architecture:</b> Professional desktop application with signal/slot patterns</li>
            <li><b>Matplotlib Integration:</b> Advanced plotting with Qt5Agg backend optimization</li>
            <li><b>Pandas/NumPy:</b> High-performance data analysis and statistical processing</li>
            <li><b>Thread Safety:</b> Crash-safe worker threads with health monitoring</li>
            <li><b>Error Handling:</b> Comprehensive exception handling and user feedback</li>
        </ul>
        
        <div style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 16px; margin: 20px 0;">
            <h4 style="color: #198754; margin: 0 0 8px 0;">👨‍💻 Developer Expertise</h4>
            <p style="margin: 0; color: #495057;">
                This application demonstrates <b>Tanmay Pandey's</b> proficiency in biomedical engineering software development, 
                advanced data visualization, and user-centric design. Built for medical professionals working with 
                Linear Accelerator (LINAC) systems, showcasing expertise in Python, Qt, and scientific computing.
            </p>
        </div>
        
        </div>
        """
        )
        features.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(features)
        return widget

    def create_system_info_tab(self):
        """Create the system information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        system_info = QTextBrowser()
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        try:
            import PyQt5.QtCore

            qt_version = PyQt5.QtCore.QT_VERSION_STR
            pyqt_version = PyQt5.QtCore.PYQT_VERSION_STR
        except:
            qt_version = "Unknown"
            pyqt_version = "Unknown"
        try:
            import pandas as pd

            pandas_version = pd.__version__
        except:
            pandas_version = "Not available"
        try:
            import numpy as np

            numpy_version = np.__version__
        except:
            numpy_version = "Not available"
        try:
            import matplotlib

            matplotlib_version = matplotlib.__version__
        except:
            matplotlib_version = "Not available"

        system_info.setHtml(
            f"""
        <h3>System Information</h3>
        <h4>Application Details</h4>
        <table>
            <tr><td><b>Application:</b></td><td>Gobioeng HALog</td></tr>
            <tr><td><b>Version:</b></td><td>0.0.1 beta</td></tr>
            <tr><td><b>Developer:</b></td><td>Tanmay Pandey</td></tr>
            <tr><td><b>Company:</b></td><td>gobioeng.com</td></tr>
            <tr><td><b>Build Date:</b></td><td>2025-08-22</td></tr>
            <tr><td><b>Architecture:</b></td><td>{platform.machine()}</td></tr>
        </table>
        <h4>System Environment</h4>
        <table>
            <tr><td><b>Operating System:</b></td><td>{platform.system()} {platform.release()}</td></tr>
            <tr><td><b>Platform:</b></td><td>{platform.platform()}</td></tr>
            <tr><td><b>Processor:</b></td><td>{platform.processor()}</td></tr>
        </table>
        <h4>Python Environment</h4>
        <table>
            <tr><td><b>Python Version:</b></td><td>{python_version}</td></tr>
            <tr><td><b>Qt Version:</b></td><td>{qt_version}</td></tr>
            <tr><td><b>PyQt5 Version:</b></td><td>{pyqt_version}</td></tr>
        </table>
        <h4>Dependencies</h4>
        <table>
            <tr><td><b>Pandas:</b></td><td>{pandas_version}</td></tr>
            <tr><td><b>NumPy:</b></td><td>{numpy_version}</td></tr>
            <tr><td><b>Matplotlib:</b></td><td>{matplotlib_version}</td></tr>
        </table>
        <h4>Technical Credits</h4>
        <table>
            <tr><td><b>Lead Developer:</b></td><td>Tanmay Pandey</td></tr>
            <tr><td><b>UI Framework:</b></td><td>PyQt5</td></tr>
            <tr><td><b>Data Processing:</b></td><td>Pandas, NumPy</td></tr>
            <tr><td><b>Visualization:</b></td><td>Matplotlib</td></tr>
        </table>
        """
        )
        system_info.setStyleSheet(
            """
            border: none; 
            background: transparent;
            QTextBrowser table { border-collapse: collapse; width: 100%; }
            QTextBrowser td { padding: 4px 8px; border-bottom: 1px solid #eee; }
            QTextBrowser tr:nth-child(even) { background-color: #f9f9f9; }
        """
        )
        layout.addWidget(system_info)
        return widget
