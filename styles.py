"""
Modern Native Styling for Gobioeng HALog
Windows 11 inspired design with native OS integration
Developer: gobioeng.com
Date: 2025-01-21
"""


def get_modern_native_stylesheet():
    """Get modern native Windows-style stylesheet with Calibri font"""
    return """
    /* Modern Native Windows Theme with Calibri Font */
    QMainWindow {
        background-color: #f0f0f0;
        color: #333333;
        font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
        font-size: 10pt;
    }

    /* Native-style buttons */
    QPushButton {
        background-color: #e1e1e1;
        border: 1px solid #adadad;
        padding: 6px 12px;
        border-radius: 3px;
        color: #333333;
        font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
        font-weight: normal;
        min-height: 18px;
    }
    QPushButton:hover {
        background-color: #e5f1fb;
        border: 1px solid #0078d4;
    }
    QPushButton:pressed {
        background-color: #005a9e;
        color: white;
    }
    QPushButton:disabled {
        background-color: #f5f5f5;
        color: #a0a0a0;
        border: 1px solid #d0d0d0;
    }

    /* Native-style tabs */
    QTabWidget::pane {
        border: 1px solid #adadad;
        background-color: white;
        border-radius: 0px;
    }
    QTabBar::tab {
        background-color: #e1e1e1;
        border: 1px solid #adadad;
        padding: 6px 12px;
        margin-right: 2px;
        color: #333333;
    }
    QTabBar::tab:selected {
        background-color: white;
        border-bottom: 1px solid white;
    }
    QTabBar::tab:hover:!selected {
        background-color: #f0f0f0;
    }

    /* Native-style group boxes */
    QGroupBox {
        font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
        font-weight: bold;
        border: 1px solid #adadad;
        border-radius: 3px;
        margin-top: 1ex;
        padding-top: 10px;
        background-color: white;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
        background-color: #f0f0f0;
        font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
    }

    /* Native-style tables */
    QTableWidget {
        background-color: white;
        border: 1px solid #adadad;
        gridline-color: #d0d0d0;
        selection-background-color: #0078d4;
        selection-color: white;
        font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
    }
    QHeaderView::section {
        background-color: #f0f0f0;
        border: 1px solid #adadad;
        padding: 4px;
        font-weight: bold;
        color: #333333;
        font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
    }

    /* Native-style combo boxes */
    QComboBox {
        border: 1px solid #adadad;
        padding: 4px;
        background-color: white;
        color: #333333;
        font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
    }
    QComboBox:focus {
        border: 2px solid #0078d4;
    }
    QComboBox::drop-down {
        border: none;
        width: 20px;
    }

    /* Native-style text inputs */
    QLineEdit, QTextEdit, QPlainTextEdit {
        border: 1px solid #adadad;
        padding: 4px;
        background-color: white;
        color: #333333;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 2px solid #0078d4;
    }

    /* Native-style labels */
    QLabel {
        color: #333333;
        background-color: transparent;
    }

    /* Native-style status bar */
    QStatusBar {
        background-color: #f0f0f0;
        border-top: 1px solid #adadad;
        color: #333333;
    }

    /* Native-style menu bar */
    QMenuBar {
        background-color: #f0f0f0;
        border-bottom: 1px solid #adadad;
        color: #333333;
    }
    QMenuBar::item {
        padding: 4px 8px;
        background-color: transparent;
    }
    QMenuBar::item:selected {
        background-color: #e5f1fb;
    }

    /* Native-style menus */
    QMenu {
        background-color: white;
        border: 1px solid #adadad;
        color: #333333;
    }
    QMenu::item {
        padding: 4px 20px;
    }
    QMenu::item:selected {
        background-color: #0078d4;
        color: white;
    }

    /* Native-style progress bars */
    QProgressBar {
        border: 1px solid #adadad;
        text-align: center;
        background-color: white;
        color: #333333;
    }
    QProgressBar::chunk {
        background-color: #0078d4;
    }
    """


def get_dark_theme_stylesheet():
    """
    Modern dark theme stylesheet for users who prefer dark mode
    """
    return """
    /* Dark Theme Global Styles */
    QMainWindow {
        background-color: #1e1e1e;
        color: #ffffff;
        font-family: 'Segoe UI Variable', 'Segoe UI', system-ui, -apple-system, sans-serif;
        font-size: 14px;
        font-weight: 400;
        line-height: 1.4;
    }

    /* Dark Menu Bar */
    QMenuBar {
        background-color: #2d2d30;
        color: #ffffff;
        border: none;
        border-bottom: 1px solid #3e3e42;
        padding: 8px 16px;
        font-size: 14px;
    }
    QMenuBar::item {
        background-color: transparent;
        padding: 10px 16px;
        margin: 0px 4px;
        border-radius: 6px;
        color: #cccccc;
    }
    QMenuBar::item:selected {
        background-color: #404040;
        color: #0078d4;
    }

    /* Dark Tab Design */
    QTabWidget::pane {
        border: none;
        background-color: #252526;
        border-radius: 12px;
    }
    QTabBar::tab {
        background-color: transparent;
        color: #cccccc;
        padding: 14px 24px;
        border-radius: 8px 8px 0px 0px;
        font-weight: 500;
        font-size: 14px;
    }
    QTabBar::tab:selected {
        background-color: #252526;
        color: #0078d4;
        font-weight: 600;
        border-bottom: 3px solid #0078d4;
    }
    QTabBar::tab:hover:!selected {
        background-color: #2d2d30;
    }

    /* Dark Cards */
    QGroupBox {
        color: #ffffff;
        border: 1px solid #3e3e42;
        background-color: #252526;
    }
    QGroupBox::title {
        background-color: #0078d4;
        color: #ffffff;
    }

    /* Dark Buttons */
    QPushButton {
        background-color: #0078d4;
        color: #ffffff;
    }
    QPushButton:hover {
        background-color: #106ebe;
    }
    QPushButton:pressed {
        background-color: #005a9e;
    }

    /* Dark Input Fields */
    QLineEdit, QTextEdit {
        border: 2px solid #3e3e42;
        background-color: #1e1e1e;
        color: #ffffff;
    }
    QLineEdit:focus, QTextEdit:focus {
        border-color: #0078d4;
    }

    /* Dark Tables */
    QTableWidget {
        background-color: #252526;
        gridline-color: #3e3e42;
        border: 1px solid #3e3e42;
        color: #ffffff;
    }
    QHeaderView::section {
        background-color: #2d2d30;
        color: #cccccc;
        border-bottom: 2px solid #0078d4;
    }
    """


def apply_responsive_layout(widget):
    """
    Apply responsive layout adjustments based on widget size
    """
    try:
        from PyQt5.QtCore import QTimer
        from PyQt5.QtWidgets import QApplication

        def adjust_layout():
            screen = QApplication.primaryScreen()
            if screen:
                screen_size = screen.size()
                widget_size = widget.size()

                # Adjust font sizes and spacing based on screen/widget size
                if widget_size.width() < 1000:
                    # Compact layout for smaller screens
                    widget.setStyleSheet(widget.styleSheet() + """
                        QTabBar::tab { padding: 8px 12px; font-size: 12px; }
                        QPushButton { padding: 8px 16px; font-size: 12px; }
                        QGroupBox { font-size: 13px; }
                    """)
                elif widget_size.width() > 1600:
                    # Expanded layout for larger screens
                    widget.setStyleSheet(widget.styleSheet() + """
                        QTabBar::tab { padding: 16px 28px; font-size: 15px; }
                        QPushButton { padding: 14px 28px; font-size: 15px; }
                        QGroupBox { font-size: 16px; }
                    """)

        # Apply initial adjustments
        adjust_layout()

        # Set up timer to reapply on resize
        timer = QTimer()
        timer.timeout.connect(adjust_layout)
        timer.start(500)  # Check every 500ms

    except Exception as e:
        print(f"Error applying responsive layout: {e}")


def get_material_design_stylesheet():
    """Legacy function - redirects to modern native stylesheet"""
    return get_modern_native_stylesheet()