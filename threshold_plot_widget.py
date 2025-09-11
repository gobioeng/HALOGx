"""
Advanced Threshold Visualization Widget for HALog Application
Professional LINAC monitoring system with threshold boundaries and alert zones

Developer: HALog Enhancement Team
Company: gobioeng.com
"""

import matplotlib
# Ensure proper backend for PyQt5
try:
    matplotlib.use('Qt5Agg')
except ImportError:
    matplotlib.use('Agg')

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='matplotlib')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Optional, Dict, List, Tuple, Any
import colorsys

from plot_utils import EnhancedPlotWidget, PlotUtils


class ThresholdPlotWidget(EnhancedPlotWidget):
    """
    Advanced threshold visualization widget with professional monitoring features:
    - Multi-parameter overlay with unique colors
    - Horizontal min/max threshold lines 
    - Shaded threshold bands between min/max values
    - Alert zones (red highlighting) when parameters exceed thresholds
    - Interactive tooltips and zoom/pan capabilities
    """
    
    # Signal emitted when threshold violation is detected
    threshold_violation = pyqtSignal(str, float, tuple)  # parameter, value, threshold_range
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parameter_thresholds = {}
        self.parameter_colors = {}
        self.threshold_bands = {}
        self.alert_zones = {}
        self.visible_parameters = set()
        self.auto_detect_thresholds = True
        self.setup_threshold_ui()
        
    def setup_threshold_ui(self):
        """Setup threshold-specific UI controls"""
        # Add controls above the plot
        controls_layout = QHBoxLayout()
        
        # Parameter selection
        self.parameter_combo = QComboBox()
        self.parameter_combo.addItem("Select Parameter...")
        controls_layout.addWidget(QLabel("Parameter:"))
        controls_layout.addWidget(self.parameter_combo)
        
        # Threshold mode toggle
        self.auto_threshold_checkbox = QCheckBox("Auto-detect thresholds")
        self.auto_threshold_checkbox.setChecked(True)
        self.auto_threshold_checkbox.stateChanged.connect(self._toggle_threshold_mode)
        controls_layout.addWidget(self.auto_threshold_checkbox)
        
        # Add/Remove parameter buttons
        self.add_param_btn = QPushButton("+ Add")
        self.add_param_btn.clicked.connect(self._add_parameter)
        controls_layout.addWidget(self.add_param_btn)
        
        self.remove_param_btn = QPushButton("- Remove")
        self.remove_param_btn.clicked.connect(self._remove_parameter)
        controls_layout.addWidget(self.remove_param_btn)
        
        # Clear all button
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self._clear_all_parameters)
        controls_layout.addWidget(self.clear_btn)
        
        controls_layout.addStretch()
        
        # Insert controls at the top of the layout
        self.layout.insertLayout(0, controls_layout)
        
    def set_data(self, data: pd.DataFrame, parameter_mapping: Dict = None):
        """Set data and initialize parameter options"""
        self.data = data.copy() if not data.empty else pd.DataFrame()
        
        if parameter_mapping:
            self.parameter_mapping = parameter_mapping
        else:
            # Fallback to column names if no mapping provided
            self.parameter_mapping = {col: {"description": col, "unit": "", "expected_range": None} 
                                    for col in data.columns if data[col].dtype in ['float64', 'int64']}
        
        # Update parameter dropdown
        self.parameter_combo.clear()
        self.parameter_combo.addItem("Select Parameter...")
        for param, config in self.parameter_mapping.items():
            if param in data.columns:
                description = config.get('description', param)
                unit = config.get('unit', '')
                display_name = f"{description} ({unit})" if unit else description
                self.parameter_combo.addItem(display_name, param)
    
    def _toggle_threshold_mode(self, state):
        """Toggle between auto-detect and manual threshold mode"""
        self.auto_detect_thresholds = state == Qt.Checked
        self._refresh_thresholds()
        
    def _add_parameter(self):
        """Add selected parameter to the plot"""
        current_param = self.parameter_combo.currentData()
        if current_param and current_param not in self.visible_parameters:
            self.visible_parameters.add(current_param)
            self._assign_parameter_color(current_param)
            self._calculate_parameter_thresholds(current_param)
            self._update_plot()
            
    def _remove_parameter(self):
        """Remove selected parameter from the plot"""
        current_param = self.parameter_combo.currentData()
        if current_param and current_param in self.visible_parameters:
            self.visible_parameters.discard(current_param)
            if current_param in self.parameter_colors:
                del self.parameter_colors[current_param]
            if current_param in self.parameter_thresholds:
                del self.parameter_thresholds[current_param]
            self._update_plot()
            
    def _clear_all_parameters(self):
        """Clear all parameters from the plot"""
        self.visible_parameters.clear()
        self.parameter_colors.clear()
        self.parameter_thresholds.clear()
        self.threshold_bands.clear()
        self.alert_zones.clear()
        self._update_plot()
        
    def _assign_parameter_color(self, parameter: str):
        """Assign a unique color to a parameter"""
        # Generate distinct colors using HSV color space
        num_existing = len(self.parameter_colors)
        hue = (num_existing * 0.618033988749895) % 1.0  # Golden ratio for good distribution
        saturation = 0.8
        value = 0.9
        
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        color = f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
        self.parameter_colors[parameter] = color
        
    def _calculate_parameter_thresholds(self, parameter: str):
        """Calculate thresholds for a parameter"""
        if parameter not in self.data.columns:
            return
            
        param_data = self.data[parameter].dropna()
        if param_data.empty:
            return
            
        if self.auto_detect_thresholds:
            # Auto-detect thresholds using statistical analysis
            mean_val = param_data.mean()
            std_val = param_data.std()
            
            # Warning thresholds: ±2 standard deviations
            warning_min = mean_val - 2 * std_val
            warning_max = mean_val + 2 * std_val
            
            # Critical thresholds: ±3 standard deviations
            critical_min = mean_val - 3 * std_val
            critical_max = mean_val + 3 * std_val
            
            self.parameter_thresholds[parameter] = {
                "warning": (warning_min, warning_max),
                "critical": (critical_min, critical_max),
                "normal": (warning_min, warning_max)
            }
        else:
            # Use predefined thresholds from parameter mapping
            if parameter in self.parameter_mapping:
                config = self.parameter_mapping[parameter]
                expected_range = config.get('expected_range')
                critical_range = config.get('critical_range')
                
                if expected_range:
                    warning_thresholds = expected_range
                else:
                    # Fallback to data-based thresholds
                    q25 = param_data.quantile(0.25)
                    q75 = param_data.quantile(0.75)
                    warning_thresholds = (q25, q75)
                
                if critical_range:
                    critical_thresholds = critical_range
                else:
                    # Expand warning range for critical
                    range_width = warning_thresholds[1] - warning_thresholds[0]
                    critical_thresholds = (warning_thresholds[0] - range_width * 0.5, 
                                         warning_thresholds[1] + range_width * 0.5)
                
                self.parameter_thresholds[parameter] = {
                    "warning": warning_thresholds,
                    "critical": critical_thresholds,
                    "normal": warning_thresholds
                }
                
    def _update_plot(self):
        """Update the plot with current parameters and thresholds"""
        if self.figure is None:
            return
            
        self.figure.clear()
        
        if not self.visible_parameters or self.data.empty:
            # Show empty state
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Add parameters to view threshold visualization', 
                   ha='center', va='center', fontsize=12, color='#666', alpha=0.7)
            self.canvas.draw()
            return
            
        ax = self.figure.add_subplot(111)
        
        # Plot each parameter with thresholds
        for parameter in self.visible_parameters:
            self._plot_parameter_with_thresholds(ax, parameter)
            
        # Configure the plot
        self._configure_plot_appearance(ax)
        
        # Add legend
        self._add_threshold_legend(ax)
        
        # Apply tight layout and draw
        self.figure.tight_layout()
        self.canvas.draw()
        
    def _plot_parameter_with_thresholds(self, ax, parameter: str):
        """Plot a parameter with its threshold bands and alert zones"""
        if parameter not in self.data.columns:
            return
            
        param_data = self.data[parameter].dropna()
        if param_data.empty:
            return
            
        # Get parameter configuration
        color = self.parameter_colors.get(parameter, '#1f77b4')
        thresholds = self.parameter_thresholds.get(parameter, {})
        
        # Plot the parameter line
        ax.plot(param_data.index, param_data.values, 
               color=color, linewidth=2, alpha=0.8, label=parameter)
        
        # Plot threshold bands
        if thresholds:
            self._plot_threshold_bands(ax, thresholds, color)
            
        # Detect and highlight threshold violations
        self._highlight_threshold_violations(ax, parameter, param_data, thresholds, color)
        
    def _plot_threshold_bands(self, ax, thresholds: Dict, color: str):
        """Plot threshold bands (normal, warning, critical zones)"""
        xlim = ax.get_xlim() if ax.get_xlim() != (0.0, 1.0) else (0, len(self.data))
        
        # Critical zone (outermost)
        if 'critical' in thresholds:
            critical_min, critical_max = thresholds['critical']
            ax.axhspan(critical_min, critical_max, alpha=0.1, color='red', 
                      label='Critical Zone', zorder=0)
            ax.axhline(y=critical_min, color='red', linestyle='--', alpha=0.6, linewidth=1)
            ax.axhline(y=critical_max, color='red', linestyle='--', alpha=0.6, linewidth=1)
            
        # Warning zone (middle)
        if 'warning' in thresholds:
            warning_min, warning_max = thresholds['warning']
            ax.axhspan(warning_min, warning_max, alpha=0.15, color='orange',
                      label='Warning Zone', zorder=1)
            ax.axhline(y=warning_min, color='orange', linestyle='-', alpha=0.7, linewidth=1.5)
            ax.axhline(y=warning_max, color='orange', linestyle='-', alpha=0.7, linewidth=1.5)
            
        # Normal zone (innermost)
        if 'normal' in thresholds:
            normal_min, normal_max = thresholds['normal']
            ax.axhspan(normal_min, normal_max, alpha=0.2, color='green',
                      label='Normal Zone', zorder=2)
                      
    def _highlight_threshold_violations(self, ax, parameter: str, param_data: pd.Series, 
                                      thresholds: Dict, color: str):
        """Highlight points where parameter exceeds thresholds"""
        if not thresholds:
            return
            
        # Check for critical violations
        if 'critical' in thresholds:
            critical_min, critical_max = thresholds['critical']
            critical_violations = param_data[(param_data < critical_min) | (param_data > critical_max)]
            
            if not critical_violations.empty:
                ax.scatter(critical_violations.index, critical_violations.values,
                          color='red', s=50, alpha=0.8, marker='x', linewidth=3,
                          label=f'{parameter} Critical Violations', zorder=10)
                
                # Emit signal for violations
                for idx, value in critical_violations.items():
                    self.threshold_violation.emit(parameter, value, thresholds['critical'])
                    
        # Check for warning violations (but not critical)
        if 'warning' in thresholds:
            warning_min, warning_max = thresholds['warning']
            warning_violations = param_data[(param_data < warning_min) | (param_data > warning_max)]
            
            # Exclude points already marked as critical
            if 'critical' in thresholds:
                critical_min, critical_max = thresholds['critical']
                warning_violations = warning_violations[
                    (warning_violations >= critical_min) & (warning_violations <= critical_max)
                ]
            
            if not warning_violations.empty:
                ax.scatter(warning_violations.index, warning_violations.values,
                          color='orange', s=40, alpha=0.7, marker='o',
                          label=f'{parameter} Warning Violations', zorder=9)
                          
    def _configure_plot_appearance(self, ax):
        """Configure professional plot appearance"""
        # Set title
        ax.set_title('Multi-Parameter Threshold Monitoring', fontsize=14, fontweight='bold', pad=20)
        
        # Configure axes
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Parameter Values', fontsize=12)
        
        # Format time axis if datetime index
        if isinstance(self.data.index, pd.DatetimeIndex):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
        # Grid
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CCCCCC')
        ax.spines['bottom'].set_color('#CCCCCC')
        
    def _add_threshold_legend(self, ax):
        """Add a comprehensive legend for parameters and thresholds"""
        # Get existing legend handles and labels
        handles, labels = ax.get_legend_handles_labels()
        
        # Create legend with proper positioning
        if handles:
            legend = ax.legend(handles, labels, loc='upper right', bbox_to_anchor=(1.0, 1.0),
                             frameon=True, fancybox=True, shadow=True, fontsize=10)
            legend.get_frame().set_facecolor('white')
            legend.get_frame().set_alpha(0.9)
            
    def _refresh_thresholds(self):
        """Refresh thresholds for all visible parameters"""
        for parameter in self.visible_parameters:
            self._calculate_parameter_thresholds(parameter)
        self._update_plot()
        
    def add_parameter_with_thresholds(self, parameter: str, warning_range: Tuple[float, float] = None,
                                    critical_range: Tuple[float, float] = None):
        """Programmatically add a parameter with custom thresholds"""
        if parameter not in self.data.columns:
            print(f"Warning: Parameter '{parameter}' not found in data")
            return
            
        self.visible_parameters.add(parameter)
        self._assign_parameter_color(parameter)
        
        if warning_range or critical_range:
            # Use custom thresholds
            thresholds = {}
            if warning_range:
                thresholds['warning'] = warning_range
                thresholds['normal'] = warning_range
            if critical_range:
                thresholds['critical'] = critical_range
                
            self.parameter_thresholds[parameter] = thresholds
        else:
            # Auto-calculate thresholds
            self._calculate_parameter_thresholds(parameter)
            
        self._update_plot()
        
    def get_threshold_violations(self) -> Dict[str, List[Tuple[Any, float]]]:
        """Get all current threshold violations"""
        violations = {}
        
        for parameter in self.visible_parameters:
            if parameter not in self.data.columns or parameter not in self.parameter_thresholds:
                continue
                
            param_data = self.data[parameter].dropna()
            thresholds = self.parameter_thresholds[parameter]
            param_violations = []
            
            # Check critical violations
            if 'critical' in thresholds:
                critical_min, critical_max = thresholds['critical']
                critical_viols = param_data[(param_data < critical_min) | (param_data > critical_max)]
                for idx, value in critical_viols.items():
                    param_violations.append((idx, value, 'critical'))
                    
            # Check warning violations
            if 'warning' in thresholds:
                warning_min, warning_max = thresholds['warning']
                warning_viols = param_data[(param_data < warning_min) | (param_data > warning_max)]
                # Exclude critical violations already counted
                if 'critical' in thresholds:
                    critical_min, critical_max = thresholds['critical']
                    warning_viols = warning_viols[
                        (warning_viols >= critical_min) & (warning_viols <= critical_max)
                    ]
                for idx, value in warning_viols.items():
                    param_violations.append((idx, value, 'warning'))
                    
            if param_violations:
                violations[parameter] = param_violations
                
        return violations
        
    def export_threshold_config(self) -> Dict:
        """Export current threshold configuration"""
        return {
            'visible_parameters': list(self.visible_parameters),
            'parameter_thresholds': self.parameter_thresholds.copy(),
            'parameter_colors': self.parameter_colors.copy(),
            'auto_detect_thresholds': self.auto_detect_thresholds
        }
        
    def import_threshold_config(self, config: Dict):
        """Import threshold configuration"""
        self.visible_parameters = set(config.get('visible_parameters', []))
        self.parameter_thresholds = config.get('parameter_thresholds', {})
        self.parameter_colors = config.get('parameter_colors', {})
        self.auto_detect_thresholds = config.get('auto_detect_thresholds', True)
        self.auto_threshold_checkbox.setChecked(self.auto_detect_thresholds)
        self._update_plot()