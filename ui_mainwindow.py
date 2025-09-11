
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QComboBox,
    QTextEdit, QLineEdit, QGroupBox, QGridLayout, QSplitter,
    QHeaderView, QAbstractItemView, QMenuBar, QAction, QStatusBar,
    QProgressBar, QFrame, QSpacerItem, QSizePolicy, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import pandas as pd
from typing import Optional, List, Dict


class Ui_MainWindow:
    """Main window UI with comprehensive tabs and functionality"""
    
    def __init__(self):
        self.central_widget = None
        self.main_layout = None
        self.tab_widget = None
        
        # Dashboard components
        self.dashboard_tab = None
        self.status_label = None
        self.record_count_label = None
        self.file_count_label = None
        
        # Trends components
        self.trends_tab = None
        self.trend_sub_tabs = None
        self.chart_widgets = {}
        
        # Data table components
        self.data_tab = None
        self.data_table = None
        self.table_info_label = None
        self.limit_combo = None
        self.table_param_combo = None
        
        # Fault code components
        self.fault_tab = None
        self.fault_search_input = None
        self.fault_results_table = None
        self.search_type_combo = None
        
        # Analysis components
        self.analysis_tab = None
        self.analysis_param_combo = None
        self.analysis_results = None
        
        # Progress bar
        self.progress_bar = None
    
    def setupUi(self, MainWindow):
        """Setup the complete UI"""
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1400, 900)
        MainWindow.setMinimumSize(1000, 700)
        MainWindow.setWindowTitle("HALog 1.0.0 - LINAC Log Analyzer")
        
        # Central widget
        self.central_widget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Create menu bar
        self.create_menu_bar(MainWindow)
        
        # Header section
        self.create_header()
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)
        
        # Main tabs
        self.create_main_tabs()
        
        # Status bar
        MainWindow.setStatusBar(QStatusBar())
        MainWindow.statusBar().showMessage("Ready - HALog 1.0.0")
    
    def create_menu_bar(self, MainWindow):
        """Create comprehensive menu bar"""
        menubar = MainWindow.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        open_action = QAction('&Open Log File...', MainWindow)
        open_action.setShortcut('Ctrl+O')
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_action = QAction('&Export Data...', MainWindow)
        export_action.setShortcut('Ctrl+E')
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', MainWindow)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(MainWindow.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        refresh_action = QAction('&Refresh', MainWindow)
        refresh_action.setShortcut('F5')
        view_menu.addAction(refresh_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        clear_action = QAction('&Clear Database', MainWindow)
        tools_menu.addAction(clear_action)
        
        optimize_action = QAction('&Optimize Database', MainWindow)
        tools_menu.addAction(optimize_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About HALog', MainWindow)
        help_menu.addAction(about_action)
    
    def create_header(self):
        """Create application header"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Box)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Title section
        title_layout = QVBoxLayout()
        title_label = QLabel("HALog - LINAC Water System Monitor")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        title_layout.addWidget(title_label)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        title_layout.addWidget(self.status_label)
        
        header_layout.addLayout(title_layout)
        
        # Stats section
        stats_layout = QVBoxLayout()
        self.record_count_label = QLabel("Records: 0")
        self.file_count_label = QLabel("Files: 0")
        stats_layout.addWidget(self.record_count_label)
        stats_layout.addWidget(self.file_count_label)
        header_layout.addLayout(stats_layout)
        
        header_layout.addStretch()
        
        # Action buttons
        load_btn = QPushButton("📂 Load Log File")
        refresh_btn = QPushButton("🔄 Refresh")
        clear_btn = QPushButton("🗑️ Clear Data")
        
        for btn in [load_btn, refresh_btn, clear_btn]:
            btn.setMinimumWidth(120)
            header_layout.addWidget(btn)
        
        self.main_layout.addWidget(header_frame)
    
    def create_main_tabs(self):
        """Create main content tabs"""
        self.tab_widget = QTabWidget()
        
        # Dashboard tab
        self.create_dashboard_tab()
        
        # Trends tab with sub-tabs
        self.create_trends_tab()
        
        # Data table tab
        self.create_data_tab()
        
        # Fault Code tab
        self.create_fault_code_tab()
        
        # Analysis tab
        self.create_analysis_tab()
        
        self.main_layout.addWidget(self.tab_widget)
    
    def create_dashboard_tab(self):
        """Create dashboard overview tab"""
        self.dashboard_tab = QWidget()
        layout = QVBoxLayout(self.dashboard_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Welcome section
        welcome_label = QLabel("<h2>📊 HALog Dashboard</h2><p>Professional LINAC Water System Monitoring</p>")
        layout.addWidget(welcome_label)
        
        # Summary cards
        cards_layout = QHBoxLayout()
        
        # System status card
        status_card = self.create_card("🔧 System Status", [
            ("Serial Number:", "system_serial_label"),
            ("Last Update:", "last_update_label"),
            ("Data Quality:", "data_quality_label")
        ])
        cards_layout.addWidget(status_card)
        
        # Data summary card
        data_card = self.create_card("📈 Data Summary", [
            ("Total Records:", "total_records_label"),
            ("Parameters:", "parameters_count_label"),
            ("Date Range:", "date_range_label")
        ])
        cards_layout.addWidget(data_card)
        
        layout.addLayout(cards_layout)
        layout.addStretch()
        
        self.tab_widget.addTab(self.dashboard_tab, "📊 Dashboard")
    
    def create_trends_tab(self):
        """Create trends visualization tab with sub-tabs"""
        self.trends_tab = QWidget()
        layout = QVBoxLayout(self.trends_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Sub-tabs for different parameter groups
        self.trend_sub_tabs = QTabWidget()
        
        # Water System tab
        self.setup_water_system_tab()
        
        # Voltages tab
        self.setup_voltages_tab()
        
        # Temperatures tab
        self.setup_temperatures_tab()
        
        # Humidity tab
        self.setup_humidity_tab()
        
        # Fan Speeds tab
        self.setup_fan_speeds_tab()
        
        layout.addWidget(self.trend_sub_tabs)
        self.tab_widget.addTab(self.trends_tab, "📈 Trends")
    
    def setup_water_system_tab(self):
        """Setup water system sub-tab"""
        tab_water = QWidget()
        self.trend_sub_tabs.addTab(tab_water, "🌊 Water System")
        layout = QVBoxLayout(tab_water)
        
        # Controls
        controls_group = QGroupBox("Water System Graph Selection")
        controls_layout = QHBoxLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Top Graph:"))
        self.combo_water_top = QComboBox()
        self.combo_water_top.addItems(["Mag Flow", "Flow Target", "Flow Chiller Water", "Cooling Pump Pressure"])
        controls_layout.addWidget(self.combo_water_top)
        
        controls_layout.addWidget(QLabel("Bottom Graph:"))
        self.combo_water_bottom = QComboBox()
        self.combo_water_bottom.addItems(["Flow Target", "Mag Flow", "Flow Chiller Water", "Cooling Pump Pressure"])
        controls_layout.addWidget(self.combo_water_bottom)
        
        controls_layout.addStretch()
        layout.addWidget(controls_group)
        
        # Chart placeholder
        chart_placeholder = QLabel("Chart will be displayed here")
        chart_placeholder.setMinimumHeight(400)
        chart_placeholder.setStyleSheet("border: 1px solid #ccc; background: #f9f9f9;")
        layout.addWidget(chart_placeholder)
    
    def setup_voltages_tab(self):
        """Setup voltages sub-tab"""
        tab_voltages = QWidget()
        self.trend_sub_tabs.addTab(tab_voltages, "⚡ Voltages")
        layout = QVBoxLayout(tab_voltages)
        
        # Controls
        controls_group = QGroupBox("Voltage Graph Selection")
        controls_layout = QHBoxLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Top Graph:"))
        self.combo_voltage_top = QComboBox()
        self.combo_voltage_top.addItems(["MLC Bank A 24V", "MLC Bank B 24V", "COL 48V"])
        controls_layout.addWidget(self.combo_voltage_top)
        
        controls_layout.addWidget(QLabel("Bottom Graph:"))
        self.combo_voltage_bottom = QComboBox()
        self.combo_voltage_bottom.addItems(["MLC Bank B 24V", "MLC Bank A 24V", "COL 48V"])
        controls_layout.addWidget(self.combo_voltage_bottom)
        
        controls_layout.addStretch()
        layout.addWidget(controls_group)
        
        # Chart placeholder
        chart_placeholder = QLabel("Voltage charts will be displayed here")
        chart_placeholder.setMinimumHeight(400)
        chart_placeholder.setStyleSheet("border: 1px solid #ccc; background: #f9f9f9;")
        layout.addWidget(chart_placeholder)
    
    def setup_temperatures_tab(self):
        """Setup temperatures sub-tab"""
        tab_temp = QWidget()
        self.trend_sub_tabs.addTab(tab_temp, "🌡️ Temperatures")
        layout = QVBoxLayout(tab_temp)
        
        # Controls
        controls_group = QGroupBox("Temperature Graph Selection")
        controls_layout = QHBoxLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Top Graph:"))
        self.combo_temp_top = QComboBox()
        self.combo_temp_top.addItems(["Temp Room", "Temp PDU", "Temp COL Board", "Temp Magnetron"])
        controls_layout.addWidget(self.combo_temp_top)
        
        controls_layout.addWidget(QLabel("Bottom Graph:"))
        self.combo_temp_bottom = QComboBox()
        self.combo_temp_bottom.addItems(["Temp PDU", "Temp Room", "Temp COL Board", "Temp Magnetron"])
        controls_layout.addWidget(self.combo_temp_bottom)
        
        controls_layout.addStretch()
        layout.addWidget(controls_group)
        
        # Chart placeholder
        chart_placeholder = QLabel("Temperature charts will be displayed here")
        chart_placeholder.setMinimumHeight(400)
        chart_placeholder.setStyleSheet("border: 1px solid #ccc; background: #f9f9f9;")
        layout.addWidget(chart_placeholder)
    
    def setup_humidity_tab(self):
        """Setup humidity sub-tab"""
        tab_humidity = QWidget()
        self.trend_sub_tabs.addTab(tab_humidity, "💧 Humidity")
        layout = QVBoxLayout(tab_humidity)
        
        # Controls
        controls_group = QGroupBox("Humidity Graph Selection")
        controls_layout = QHBoxLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Top Graph:"))
        self.combo_humidity_top = QComboBox()
        self.combo_humidity_top.addItems(["Room Humidity", "Temp Room"])
        controls_layout.addWidget(self.combo_humidity_top)
        
        controls_layout.addWidget(QLabel("Bottom Graph:"))
        self.combo_humidity_bottom = QComboBox()
        self.combo_humidity_bottom.addItems(["Temp Room", "Room Humidity"])
        controls_layout.addWidget(self.combo_humidity_bottom)
        
        controls_layout.addStretch()
        layout.addWidget(controls_group)
        
        # Chart placeholder
        chart_placeholder = QLabel("Humidity charts will be displayed here")
        chart_placeholder.setMinimumHeight(400)
        chart_placeholder.setStyleSheet("border: 1px solid #ccc; background: #f9f9f9;")
        layout.addWidget(chart_placeholder)
    
    def setup_fan_speeds_tab(self):
        """Setup fan speeds sub-tab"""
        tab_fans = QWidget()
        self.trend_sub_tabs.addTab(tab_fans, "🌀 Fan Speeds")
        layout = QVBoxLayout(tab_fans)
        
        # Controls
        controls_group = QGroupBox("Fan Speed Graph Selection")
        controls_layout = QHBoxLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Top Graph:"))
        self.combo_fan_top = QComboBox()
        self.combo_fan_top.addItems(["Speed FAN 1", "Speed FAN 2", "Speed FAN 3", "Speed FAN 4"])
        controls_layout.addWidget(self.combo_fan_top)
        
        controls_layout.addWidget(QLabel("Bottom Graph:"))
        self.combo_fan_bottom = QComboBox()
        self.combo_fan_bottom.addItems(["Speed FAN 2", "Speed FAN 1", "Speed FAN 3", "Speed FAN 4"])
        controls_layout.addWidget(self.combo_fan_bottom)
        
        controls_layout.addStretch()
        layout.addWidget(controls_group)
        
        # Chart placeholder
        chart_placeholder = QLabel("Fan speed charts will be displayed here")
        chart_placeholder.setMinimumHeight(400)
        chart_placeholder.setStyleSheet("border: 1px solid #ccc; background: #f9f9f9;")
        layout.addWidget(chart_placeholder)
    
    def create_data_tab(self):
        """Create data table tab"""
        self.data_tab = QWidget()
        layout = QVBoxLayout(self.data_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Show:"))
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(["100", "500", "1000", "2000", "All"])
        self.limit_combo.setCurrentText("1000")
        controls_layout.addWidget(self.limit_combo)
        
        controls_layout.addWidget(QLabel("Parameter:"))
        self.table_param_combo = QComboBox()
        self.table_param_combo.addItem("All")
        controls_layout.addWidget(self.table_param_combo)
        
        controls_layout.addStretch()
        
        export_btn = QPushButton("💾 Export CSV")
        controls_layout.addWidget(export_btn)
        
        layout.addLayout(controls_layout)
        
        # Table info
        self.table_info_label = QLabel("No data loaded")
        layout.addWidget(self.table_info_label)
        
        # Data table
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table.setSortingEnabled(True)
        layout.addWidget(self.data_table)
        
        self.tab_widget.addTab(self.data_tab, "📋 Data Table")
    
    def create_fault_code_tab(self):
        """Create fault code lookup tab"""
        self.fault_tab = QWidget()
        layout = QVBoxLayout(self.fault_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Search controls
        search_group = QGroupBox("🔍 Fault Code Search")
        search_layout = QHBoxLayout(search_group)
        
        search_layout.addWidget(QLabel("Search Type:"))
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Fault Code", "Description"])
        search_layout.addWidget(self.search_type_combo)
        
        search_layout.addWidget(QLabel("Search:"))
        self.fault_search_input = QLineEdit()
        self.fault_search_input.setPlaceholderText("Enter fault code or description...")
        search_layout.addWidget(self.fault_search_input)
        
        search_btn = QPushButton("🔍 Search")
        search_layout.addWidget(search_btn)
        
        clear_search_btn = QPushButton("🗑️ Clear")
        search_layout.addWidget(clear_search_btn)
        
        layout.addWidget(search_group)
        
        # Results table
        results_group = QGroupBox("📋 Search Results")
        results_layout = QVBoxLayout(results_group)
        
        self.fault_results_table = QTableWidget()
        self.fault_results_table.setAlternatingRowColors(True)
        self.fault_results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fault_results_table.setSortingEnabled(True)
        
        # Set column headers
        self.fault_results_table.setColumnCount(4)
        self.fault_results_table.setHorizontalHeaderLabels(["Code", "Description", "Database", "Category"])
        
        results_layout.addWidget(self.fault_results_table)
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(self.fault_tab, "🚨 Fault Codes")
    
    def create_analysis_tab(self):
        """Create analysis tab"""
        self.analysis_tab = QWidget()
        layout = QVBoxLayout(self.analysis_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Analysis controls
        controls_group = QGroupBox("🔍 Analysis Tools")
        controls_layout = QHBoxLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Analyze Parameter:"))
        self.analysis_param_combo = QComboBox()
        controls_layout.addWidget(self.analysis_param_combo)
        
        analyze_btn = QPushButton("🔍 Run Analysis")
        controls_layout.addWidget(analyze_btn)
        
        controls_layout.addStretch()
        layout.addWidget(controls_group)
        
        # Results display
        results_group = QGroupBox("📊 Analysis Results")
        results_layout = QVBoxLayout(results_group)
        
        self.analysis_results = QTextEdit()
        self.analysis_results.setReadOnly(True)
        results_layout.addWidget(self.analysis_results)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(self.analysis_tab, "🔍 Analysis")
    
    def create_card(self, title: str, labels: List[tuple]) -> QGroupBox:
        """Create a dashboard card"""
        card = QGroupBox(title)
        layout = QGridLayout(card)
        layout.setContentsMargins(15, 20, 15, 15)
        
        for i, (text, attr_name) in enumerate(labels):
            label_text = QLabel(text)
            label_value = QLabel("--")
            label_value.setStyleSheet("font-weight: bold;")
            
            # Set attribute for later access
            setattr(self, attr_name, label_value)
            
            layout.addWidget(label_text, i, 0)
            layout.addWidget(label_value, i, 1)
        
        return card
