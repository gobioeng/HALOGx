"""
Enhanced Unified Plotting Utilities for HALbasic
Combines plotting widgets with LINAC-specific data processing
Developer: gobioeng.com
Date: 2025-01-21
"""

# CRITICAL: Import matplotlib and configure before other imports
import matplotlib
# FIXED: Try Qt5Agg first, fall back gracefully for headless environments
try:
    matplotlib.use('Qt5Agg')
except ImportError:
    # Fallback to Agg for headless environments
    matplotlib.use('Agg')
    print("ℹ️ Using Agg backend for headless environment")

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='matplotlib')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import timedelta
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from typing import Optional, Dict, List

# Set matplotlib style for professional appearance
plt.style.use('default')


class InteractivePlotManager:
    """Manages interactive functionality for matplotlib plots"""

    def __init__(self, fig, ax, canvas):
        self.fig = fig
        self.ax = ax if isinstance(ax, list) else [ax]  # Support multiple axes
        self.canvas = canvas
        self.press = None
        self.initial_xlim = None
        self.initial_ylim = None
        self.tooltip_annotation = None

        # Store initial view for reset functionality
        self._store_initial_view()

        # Connect event handlers
        self._connect_events()

    def _store_initial_view(self):
        """Store initial view limits for reset functionality"""
        self.initial_views = []
        for ax in self.ax:
            self.initial_views.append({
                'xlim': ax.get_xlim(),
                'ylim': ax.get_ylim()
            })

    def _connect_events(self):
        """Connect interactive event handlers"""
        self.canvas.mpl_connect('scroll_event', self._handle_zoom)
        self.canvas.mpl_connect('button_press_event', self._handle_button_press)
        self.canvas.mpl_connect('button_release_event', self._handle_button_release)
        self.canvas.mpl_connect('motion_notify_event', self._handle_motion)
        self.canvas.mpl_connect('key_press_event', self._handle_key_press)

    def _handle_key_press(self, event):
        """Handle keyboard shortcuts for time scale control"""
        if event.inaxes is None:
            return
            
        ax = event.inaxes
        
        # Time scale shortcuts
        if event.key == 'h':  # Zoom to last hour
            self._zoom_to_time_range(ax, hours=1)
        elif event.key == 'd':  # Zoom to last day
            self._zoom_to_time_range(ax, hours=24)
        elif event.key == 'w':  # Zoom to last week
            self._zoom_to_time_range(ax, hours=24*7)
        elif event.key == 'm':  # Zoom to last month
            self._zoom_to_time_range(ax, hours=24*30)
        elif event.key == 'r':  # Reset view
            self.reset_view()
        elif event.key == 'f':  # Fit all data
            self._fit_all_data(ax)
            
    def _zoom_to_time_range(self, ax, hours=24):
        """Zoom to show last N hours of data"""
        try:
            # Get the latest time from all lines in the axis
            latest_time = None
            for line in ax.get_lines():
                xdata = line.get_xdata()
                if len(xdata) > 0:
                    # Assume x-axis is time data
                    line_latest = max(xdata)
                    if latest_time is None or line_latest > latest_time:
                        latest_time = line_latest
                        
            if latest_time is not None:
                # Calculate time range (hours in matplotlib date units)
                hours_in_days = hours / 24.0
                start_time = latest_time - hours_in_days
                
                ax.set_xlim([start_time, latest_time])
                self.canvas.draw()
                
        except Exception as e:
            print(f"Error zooming to time range: {e}")

    def _handle_zoom(self, event):
        """Handle mouse wheel zoom"""
        if event.inaxes is None:
            return

        ax = event.inaxes
        scale_factor = 1.1 if event.button == 'up' else 0.9

        # Get current limits and mouse position
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        xdata = event.xdata
        ydata = event.ydata

        if xdata is None or ydata is None:
            return

        # Calculate new limits
        x_range = (xlim[1] - xlim[0]) * scale_factor
        y_range = (ylim[1] - ylim[0]) * scale_factor

        # Center zoom on mouse position
        new_xlim = [xdata - x_range / 2, xdata + x_range / 2]
        new_ylim = [ydata - y_range / 2, ydata + y_range / 2]

        # Set new limits
        ax.set_xlim(new_xlim)
        ax.set_ylim(new_ylim)

        # Redraw
        self.canvas.draw()

    def _handle_button_press(self, event):
        """Handle button press events"""
        if event.inaxes is None:
            return

        # Double-click to reset view
        if event.dblclick:
            self.reset_view()
            return

        # Start pan operation on left mouse button
        if event.button == 1:  # Left mouse button
            self.press = (event.xdata, event.ydata)
            self.current_ax = event.inaxes

    def _handle_button_release(self, event):
        """Handle button release events"""
        self.press = None
        self.current_ax = None
        self.canvas.draw()

    def _handle_motion(self, event):
        """Handle mouse motion for panning and tooltips"""
        if event.inaxes is None:
            return

        # Handle panning
        if self.press is not None and event.button == 1:
            ax = self.current_ax
            if ax is None:
                return

            # Calculate movement
            dx = event.xdata - self.press[0]
            dy = event.ydata - self.press[1]

            # Get current limits
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()

            # Apply pan
            ax.set_xlim([xlim[0] - dx, xlim[1] - dx])
            ax.set_ylim([ylim[0] - dy, ylim[1] - dy])

            self.canvas.draw_idle()

        # Handle tooltips
        else:
            self._update_tooltip(event)

    def _update_tooltip(self, event):
        """Update tooltip showing data values"""
        # Implementation for tooltips could be added here
        pass

    def reset_view(self):
        """Reset all axes to initial view"""
        for i, ax in enumerate(self.ax):
            if i < len(self.initial_views):
                ax.set_xlim(self.initial_views[i]['xlim'])
                ax.set_ylim(self.initial_views[i]['ylim'])
        self.canvas.draw()


class PlotUtils:
    """Enhanced plotting utilities for LINAC water system data"""

    @staticmethod
    def setup_professional_style():
        """Setup professional plotting style with Calibri font"""
        try:
            # Set professional font
            plt.rcParams['font.family'] = ['Calibri', 'DejaVu Sans', 'sans-serif']
            plt.rcParams['font.size'] = 10
            plt.rcParams['axes.labelsize'] = 11
            plt.rcParams['axes.titlesize'] = 12
            plt.rcParams['xtick.labelsize'] = 9
            plt.rcParams['ytick.labelsize'] = 9
            plt.rcParams['legend.fontsize'] = 9
            
            # Set colors and styling
            plt.rcParams['axes.grid'] = True
            plt.rcParams['grid.alpha'] = 0.3
            plt.rcParams['axes.spines.top'] = False
            plt.rcParams['axes.spines.right'] = False
            plt.rcParams['figure.facecolor'] = 'white'
            
        except Exception as e:
            print(f"Style setup warning: {e}")

    @staticmethod
    def group_parameters(parameters):
        """Group parameters by type for better visualization"""
        parameter_groups = {
            'Temperature': [],
            'Pressure': [],
            'Flow': [],
            'Level': [],
            'Voltage': [],
            'Current': [],
            'Humidity': [],
            'Position': [],
            'Other': []
        }
        
        for param in parameters:
            param_lower = param.lower()
            if any(temp_keyword in param_lower for temp_keyword in ['temp', 'temperature', '°c', 'celsius', '°f']):
                parameter_groups['Temperature'].append(param)
            elif any(pres_keyword in param_lower for pres_keyword in ['press', 'pressure', 'psi', 'bar', 'mbar', 'pa']):
                parameter_groups['Pressure'].append(param)
            elif any(flow_keyword in param_lower for flow_keyword in ['flow', 'rate', 'gpm', 'lpm', 'l/min']):
                parameter_groups['Flow'].append(param)
            elif any(level_keyword in param_lower for level_keyword in ['level', 'height', 'depth', 'tank']):
                parameter_groups['Level'].append(param)
            elif any(volt_keyword in param_lower for volt_keyword in ['volt', 'voltage', 'v', 'kv']):
                parameter_groups['Voltage'].append(param)
            elif any(curr_keyword in param_lower for curr_keyword in ['current', 'amp', 'ampere', 'ma']):
                parameter_groups['Current'].append(param)
            elif any(humid_keyword in param_lower for humid_keyword in ['humid', 'humidity', '%rh', 'moisture']):
                parameter_groups['Humidity'].append(param)
            elif any(pos_keyword in param_lower for pos_keyword in ['pos', 'position', 'x', 'y', 'z', 'angle']):
                parameter_groups['Position'].append(param)
            else:
                parameter_groups['Other'].append(param)

        # Remove empty groups
        return {k: v for k, v in parameter_groups.items() if v}

    @staticmethod
    def get_group_colors():
        """Get consistent colors for parameter groups"""
        return {
            'Temperature': '#FF6B6B',  # Red
            'Pressure': '#4ECDC4',     # Teal
            'Flow': '#45B7D1',         # Blue
            'Level': '#96CEB4',        # Green
            'Voltage': '#FECA57',      # Yellow
            'Current': '#FF9FF3',      # Pink
            'Humidity': '#54A0FF',     # Light Blue
            'Position': '#5F27CD',     # Purple
            'Other': '#636E72'         # Gray
        }

    @staticmethod
    def find_time_clusters(df_times, gap_threshold=None, auto_threshold=True):
        """
        Find clusters of data based on time gaps with intelligent threshold detection.
        Fixed to handle large datasets (20+ days) without unnecessary breaks.
        """
        if len(df_times) == 0:
            return []
        
        df_times_sorted = sorted(df_times)
        
        # Intelligent gap threshold calculation
        if auto_threshold:
            # Calculate data time span
            total_span = df_times_sorted[-1] - df_times_sorted[0]
            
            # Adaptive threshold based on data span and density
            if total_span.total_seconds() < 24*3600:  # Less than 1 day
                default_threshold = timedelta(hours=1)
            elif total_span.total_seconds() < 7*24*3600:  # Less than 1 week
                default_threshold = timedelta(hours=6)
            elif total_span.total_seconds() < 30*24*3600:  # Less than 1 month
                default_threshold = timedelta(days=1)
            else:  # More than 1 month - use larger threshold to prevent excessive breaks
                default_threshold = timedelta(days=3)
                
            # Additional check: if we have dense data, increase threshold
            if len(df_times_sorted) > 1000:  # Dense data
                if total_span.total_seconds() > 20*24*3600:  # 20+ days
                    default_threshold = timedelta(days=7)  # Prevent breaks in long datasets
                    
            gap_threshold = gap_threshold or default_threshold
        else:
            gap_threshold = gap_threshold or timedelta(days=1)
        
        clusters = []
        current_cluster = [df_times_sorted[0]]
        
        for i in range(1, len(df_times_sorted)):
            time_gap = df_times_sorted[i] - df_times_sorted[i-1]
            
            if time_gap <= gap_threshold:
                current_cluster.append(df_times_sorted[i])
            else:
                # Only create a new cluster if the gap is significant
                # This prevents unnecessary breaks in continuous data
                clusters.append(current_cluster)
                current_cluster = [df_times_sorted[i]]
        
        clusters.append(current_cluster)
        
        # Post-process: merge small adjacent clusters if they're close enough
        if len(clusters) > 1:
            merged_clusters = [clusters[0]]
            
            for i in range(1, len(clusters)):
                prev_cluster_end = max(merged_clusters[-1])
                current_cluster_start = min(clusters[i])
                
                # If clusters are close (within 2x the threshold), merge them
                if (current_cluster_start - prev_cluster_end) <= (gap_threshold * 2):
                    merged_clusters[-1].extend(clusters[i])
                else:
                    merged_clusters.append(clusters[i])
            
            clusters = merged_clusters
        
        return clusters

    @staticmethod
    def _plot_parameter_data_single(widget, data, parameter_name):
        """Plot single parameter data with compressed timeline for distant dates"""
        if hasattr(widget, 'figure') and widget.figure:
            widget.figure.clear()
            ax = widget.figure.add_subplot(111)
            
            # Apply professional styling
            PlotUtils.setup_professional_style()
            
            if data.empty:
                ax.text(0.5, 0.5, f'No data available for {parameter_name}', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=14)
                widget.canvas.draw()
                return

            # Process time data
            if 'datetime' in data.columns:
                data_copy = data.copy()
                data_copy['datetime'] = pd.to_datetime(data_copy['datetime'])
                data_copy = data_copy.sort_values('datetime')
                
                # Find time clusters for compressed timeline
                time_clusters = PlotUtils.find_time_clusters(data_copy['datetime'].tolist())
                
                if len(time_clusters) > 1:
                    PlotUtils._plot_single_parameter_compressed(ax, data_copy, parameter_name, time_clusters)
                else:
                    PlotUtils._plot_single_parameter_continuous(ax, data_copy, parameter_name)
            
            ax.set_title(f"{parameter_name} Trends", fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            widget.figure.tight_layout()
            
            # Add interactive capabilities if canvas exists
            if hasattr(widget, 'canvas'):
                widget.canvas.draw()

    @staticmethod
    def _plot_parameter_data_multi_machine(widget, machine_data_dict, parameter_name, machine_colors):
        """Plot multi-machine parameter data with different colors per machine"""
        if hasattr(widget, 'figure') and widget.figure:
            widget.figure.clear()
            ax = widget.figure.add_subplot(111)
            
            # Apply professional styling
            PlotUtils.setup_professional_style()
            
            if not machine_data_dict:
                ax.text(0.5, 0.5, f'No data available for {parameter_name}', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=14)
                widget.canvas.draw()
                return

            plotted_count = 0
            for machine_id, data in machine_data_dict.items():
                if data.empty:
                    continue
                    
                # Process time data
                if 'datetime' in data.columns:
                    data_copy = data.copy()
                    data_copy['datetime'] = pd.to_datetime(data_copy['datetime'])
                    data_copy = data_copy.sort_values('datetime')
                    
                    color = machine_colors.get(machine_id, '#1976D2')
                    
                    # Plot average values for multi-machine view
                    if 'value' in data_copy.columns:
                        avg_data = data_copy.groupby(['datetime'])['value'].mean().reset_index()
                        ax.plot(avg_data['datetime'], avg_data['value'], 
                               label=f'{machine_id}', color=color, linewidth=2, marker='o', markersize=4)
                        plotted_count += 1
            
            if plotted_count > 0:
                ax.set_title(f"{parameter_name} Trends - Multi-Machine Comparison", fontsize=12, fontweight='bold')
                ax.set_xlabel('Time')
                ax.set_ylabel('Value')
                ax.grid(True, alpha=0.3)
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                
                # Format datetime axis
                if plotted_count > 0:
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
                    widget.figure.autofmt_xdate()
            else:
                ax.text(0.5, 0.5, f'No data available for {parameter_name}', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=14)
            
            widget.figure.tight_layout()
            
            # Add interactive capabilities if canvas exists
            if hasattr(widget, 'canvas'):
                widget.canvas.draw()

    @staticmethod
    def _plot_single_parameter_compressed(ax, data, parameter_name, time_clusters):
        """Plot single parameter with compressed timeline"""
        colors = {'avg': '#1976D2', 'min': '#388E3C', 'max': '#D32F2F'}
        
        x_positions = []
        labels = []
        
        for i, cluster in enumerate(time_clusters):
            cluster_data = data[data['datetime'].isin(cluster)]
            
            # Create compressed x-positions
            cluster_start = i * 10  # Space clusters apart
            cluster_positions = np.linspace(cluster_start, cluster_start + 8, len(cluster_data))
            x_positions.extend(cluster_positions)
            
            # Plot data for this cluster
            for stat in ['avg', 'min', 'max']:
                if stat in cluster_data.columns:
                    values = cluster_data[stat].dropna()
                    if not values.empty:
                        positions = cluster_positions[:len(values)]
                        ax.plot(positions, values, marker='o', markersize=3, 
                               label=stat.upper() if i == 0 else "", 
                               color=colors.get(stat, '#666666'), 
                               linewidth=2, alpha=0.8)
            
            # Add cluster label
            cluster_start_date = min(cluster).strftime('%m/%d')
            cluster_end_date = max(cluster).strftime('%m/%d')
            if cluster_start_date != cluster_end_date:
                labels.append(f"{cluster_start_date}-{cluster_end_date}")
            else:
                labels.append(cluster_start_date)
        
        # Customize x-axis
        if labels:
            tick_positions = [i * 10 + 4 for i in range(len(labels))]  # Center of each cluster
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(labels, rotation=45)
        
        ax.legend()

    @staticmethod
    def _plot_single_parameter_continuous(ax, data, parameter_name):
        """Plot single parameter with continuous timeline"""
        colors = {'avg': '#1976D2', 'min': '#388E3C', 'max': '#D32F2F'}
        
        for stat in ['avg', 'min', 'max']:
            if stat in data.columns:
                values = data[stat].dropna()
                if not values.empty:
                    times = data.loc[values.index, 'datetime']
                    ax.plot(times, values, marker='o', markersize=3, 
                           label=stat.upper(), 
                           color=colors.get(stat, '#666666'), 
                           linewidth=2, alpha=0.8)
        
        # Format x-axis for continuous timeline
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.figure.autofmt_xdate()
        ax.legend()


class EnhancedPlotWidget(QWidget):
    """Enhanced plotting widget with professional styling and LINAC data processing"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = None
        self.canvas = None
        self.interactive_manager = None
        self.data = pd.DataFrame()
        self.init_ui()
    
    def init_ui(self):
        """Initialize plotting UI with enhanced error handling and backend verification"""
        self.layout = QVBoxLayout(self)
        self.setMinimumHeight(300)
        
        try:
            # Ensure matplotlib backend is properly configured
            backend = matplotlib.get_backend()
            if backend.lower() != 'qt5agg':
                print(f"Warning: matplotlib backend is {backend}, expected Qt5Agg")
                matplotlib.use('Qt5Agg', force=True)
                
            # FIXED: Smaller figure size for embedded use with proper DPI
            self.figure = Figure(figsize=(8, 4), dpi=100)
            self.canvas = FigureCanvas(self.figure)
            
            # CRITICAL: Ensure proper parent-child relationship to prevent popup windows
            self.canvas.setParent(self)
            self.canvas.setFocusPolicy(1)  # Allow focus for interactions
            self.layout.addWidget(self.canvas)
            
            # Apply professional styling
            PlotUtils.setup_professional_style()
            
            # Add a test plot to verify functionality
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Graph Ready', ha='center', va='center', 
                   fontsize=12, color='#666', alpha=0.7)
            self.canvas.draw()
            
        except Exception as e:
            print(f"Plot widget initialization error: {e}")
            error_label = QLabel(f"Plotting initialization failed: {str(e)}\nCheck matplotlib backend configuration.")
            error_label.setStyleSheet("color: red; padding: 10px; background: #fff3cd; border: 1px solid #ffeaa7;")
            self.layout.addWidget(error_label)
    
    def plot_parameter_trends(self, data: pd.DataFrame, parameter: str, 
                            title: str = "", show_statistics: bool = True):
        """Plot parameter trends with enhanced visualization using PlotUtils"""
        try:
            if data.empty or self.figure is None:
                return
            
            # Use PlotUtils for enhanced plotting
            PlotUtils._plot_parameter_data_single(self, data, parameter)
            
            # Add interactive capabilities
            if self.canvas and self.figure:
                axes = self.figure.get_axes()
                if axes:
                    self.interactive_manager = InteractivePlotManager(
                        self.figure, axes, self.canvas
                    )
                    
        except Exception as e:
            print(f"Parameter trends plotting error: {e}")
            if self.figure:
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, f'Plot error: {str(e)}', 
                       ha='center', va='center', transform=ax.transAxes, 
                       fontsize=12, color='red')
                self.canvas.draw()

    def plot_comparison(self, data: pd.DataFrame, param1: str, param2: str):
        """Plot comparison between two parameters"""
        try:
            if data.empty or self.figure is None:
                return
            
            self.figure.clear()
            
            # Create subplots for comparison
            ax1 = self.figure.add_subplot(211)
            ax2 = self.figure.add_subplot(212)
            
            # Plot first parameter
            self._plot_single_parameter(ax1, data, param1, f"Top: {param1}")
            
            # Plot second parameter
            self._plot_single_parameter(ax2, data, param2, f"Bottom: {param2}")
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            # Add interactive capabilities
            self.interactive_manager = InteractivePlotManager(
                self.figure, [ax1, ax2], self.canvas
            )
            
        except Exception as e:
            print(f"Comparison plot error: {e}")
    
    def _plot_single_parameter(self, ax, data: pd.DataFrame, parameter: str, title: str):
        """Plot single parameter on given axis"""
        try:
            # Filter for parameter
            if 'param' in data.columns:
                param_data = data[data['param'] == parameter].copy()
            else:
                param_data = data.copy()
            
            if param_data.empty:
                ax.text(0.5, 0.5, f'No data for {parameter}', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(title)
                return
            
            # Ensure datetime
            if 'datetime' in param_data.columns:
                param_data['datetime'] = pd.to_datetime(param_data['datetime'], errors='coerce')
                param_data = param_data.dropna(subset=['datetime'])
                param_data = param_data.sort_values('datetime')
            
            # Plot with professional styling
            colors = {'avg': '#1976D2', 'min': '#388E3C', 'max': '#D32F2F'}
            line_styles = {'avg': '-', 'min': '--', 'max': '--'}
            
            plotted_any = False
            
            for stat in ['avg', 'min', 'max']:
                if stat in param_data.columns and not param_data[stat].isna().all():
                    values = param_data[stat].dropna()
                    if not values.empty:
                        ax.plot(param_data.loc[values.index, 'datetime'], values,
                               marker='o', markersize=3, label=f'{stat.upper()}',
                               color=colors.get(stat, '#666666'),
                               linestyle=line_styles.get(stat, '-'),
                               linewidth=2, alpha=0.8)
                        plotted_any = True
            
            if plotted_any:
                ax.set_title(title, fontsize=12, fontweight='bold')
                ax.grid(True, alpha=0.3)
                ax.legend(fontsize=9)
                
                # Format dates
                if 'datetime' in param_data.columns and len(param_data) > 0:
                    date_range = param_data['datetime'].max() - param_data['datetime'].min()
                    if pd.notna(date_range):
                        if date_range.total_seconds() < 24*3600:
                            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                        else:
                            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                
                self.figure.autofmt_xdate()
            
        except Exception as e:
            print(f"Single parameter plot error: {e}")


class EnhancedDualPlotWidget(QWidget):
    """Enhanced dual plot widget with LINAC data processing capabilities"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = None
        self.canvas = None
        self.interactive_manager = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize dual plot UI"""
        self.layout = QVBoxLayout(self)
        self.setMinimumHeight(500)  # Taller for dual plots
        
        try:
            # Create figure with subplots
            self.figure = Figure(figsize=(10, 8), dpi=80)
            self.canvas = FigureCanvas(self.figure)
            
            # CRITICAL: Ensure proper parent-child relationship
            self.canvas.setParent(self)
            self.layout.addWidget(self.canvas)
            
            # Apply professional styling
            PlotUtils.setup_professional_style()
            
        except Exception as e:
            error_label = QLabel(f"Dual plot initialization failed: {str(e)}")
            self.layout.addWidget(error_label)
    
    def update_comparison(self, data: pd.DataFrame, top_param: str, bottom_param: str):
        """Update comparison plots with enhanced LINAC data processing"""
        try:
            if data.empty or self.figure is None:
                return
            
            self.figure.clear()
            
            # Create subplots
            ax1 = self.figure.add_subplot(211)
            ax2 = self.figure.add_subplot(212)
            
            # Use enhanced plotting for both parameters
            self._plot_enhanced_parameter(ax1, data, top_param, f"📈 {top_param}")
            self._plot_enhanced_parameter(ax2, data, bottom_param, f"📉 {bottom_param}")
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            # Add interactive capabilities
            self.interactive_manager = InteractivePlotManager(
                self.figure, [ax1, ax2], self.canvas
            )
            
        except Exception as e:
            print(f"Dual plot comparison error: {e}")
    
    def _plot_enhanced_parameter(self, ax, data: pd.DataFrame, parameter: str, title: str):
        """Plot parameter with enhanced LINAC-specific processing"""
        try:
            # Filter for parameter using PlotUtils logic
            if 'param' in data.columns:
                param_data = data[data['param'] == parameter].copy()
            else:
                # Look for parameter in column names
                if parameter in data.columns:
                    param_data = data.copy()
                    param_data['value'] = data[parameter]
                else:
                    param_data = pd.DataFrame()
            
            if param_data.empty:
                ax.text(0.5, 0.5, f'No data available for {parameter}', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
                ax.set_title(title, fontsize=12, fontweight='bold')
                return
            
            # Process datetime with PlotUtils methodology
            if 'datetime' in param_data.columns:
                param_data['datetime'] = pd.to_datetime(param_data['datetime'], errors='coerce')
                param_data = param_data.dropna(subset=['datetime'])
                param_data = param_data.sort_values('datetime')
                
                # Check for time gaps and use appropriate plotting method
                time_clusters = PlotUtils.find_time_clusters(param_data['datetime'].tolist())
                
                if len(time_clusters) > 1:
                    # Use compressed timeline for multiple clusters
                    self._plot_compressed_timeline(ax, param_data, parameter, time_clusters)
                else:
                    # Use continuous timeline
                    self._plot_continuous_timeline(ax, param_data, parameter)
            
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
                
        except Exception as e:
            print(f"Enhanced parameter plot error: {e}")
            ax.text(0.5, 0.5, f'Plot error: {str(e)}', 
                   ha='center', va='center', transform=ax.transAxes, 
                   fontsize=10, color='red')
    
    def _plot_compressed_timeline(self, ax, data, parameter, time_clusters):
        """Plot with compressed timeline for multiple date ranges"""
        colors = PlotUtils.get_group_colors()
        default_color = colors.get('Other', '#1976D2')
        
        x_positions = []
        labels = []
        
        for i, cluster in enumerate(time_clusters):
            cluster_data = data[data['datetime'].isin(cluster)]
            
            # Create compressed x-positions
            cluster_start = i * 10
            cluster_positions = np.linspace(cluster_start, cluster_start + 8, len(cluster_data))
            
            # Plot statistics
            for stat in ['avg', 'min', 'max', 'value']:
                if stat in cluster_data.columns:
                    values = cluster_data[stat].dropna()
                    if not values.empty:
                        positions = cluster_positions[:len(values)]
                        ax.plot(positions, values, marker='o', markersize=3, 
                               label=stat.upper() if i == 0 else "", 
                               color=default_color, linewidth=2, alpha=0.8)
                        break  # Use first available statistic
            
            # Add cluster label
            cluster_start_date = min(cluster).strftime('%m/%d')
            cluster_end_date = max(cluster).strftime('%m/%d')
            if cluster_start_date != cluster_end_date:
                labels.append(f"{cluster_start_date}-{cluster_end_date}")
            else:
                labels.append(cluster_start_date)
        
        # Customize x-axis
        if labels:
            tick_positions = [i * 10 + 4 for i in range(len(labels))]
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(labels, rotation=45)
        
        if ax.get_legend_handles_labels()[0]:  # Only show legend if there are labels
            ax.legend(fontsize=9)
    
    def _plot_continuous_timeline(self, ax, data, parameter):
        """Plot with continuous timeline for single date range"""
        colors = {'avg': '#1976D2', 'min': '#388E3C', 'max': '#D32F2F', 'value': '#1976D2'}
        
        plotted = False
        for stat in ['avg', 'min', 'max', 'value']:
            if stat in data.columns:
                values = data[stat].dropna()
                if not values.empty:
                    times = data.loc[values.index, 'datetime']
                    ax.plot(times, values, marker='o', markersize=3, 
                           label=stat.upper(),
                           color=colors.get(stat, '#1976D2'), 
                           linewidth=2, alpha=0.8)
                    plotted = True
        
        if plotted:
            ax.legend(fontsize=9)
            
            # Format x-axis for continuous timeline
            date_range = data['datetime'].max() - data['datetime'].min()
            if pd.notna(date_range):
                if date_range.total_seconds() < 24*3600:
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                else:
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            
            # Y-axis label
            unit = data['unit'].iloc[0] if 'unit' in data.columns and not data.empty else ''
            ax.set_ylabel(f"Value ({unit})" if unit else "Value", fontsize=10)


# Maintain backwards compatibility - alias the enhanced classes
PlotWidget = EnhancedPlotWidget
DualPlotWidget = EnhancedDualPlotWidget


class ThresholdPlotWidget(EnhancedPlotWidget):
    """Advanced threshold visualization widget with min/max boundaries and alert zones"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thresholds = {}  # Store threshold data per parameter
        self.alert_zones = {}  # Store alert zone configurations
        
    def set_parameter_thresholds(self, parameter: str, min_threshold: float = None, 
                                max_threshold: float = None, warning_min: float = None, 
                                warning_max: float = None):
        """Set threshold boundaries for a parameter"""
        self.thresholds[parameter] = {
            'min': min_threshold,
            'max': max_threshold, 
            'warning_min': warning_min,
            'warning_max': warning_max
        }
        
    def plot_parameter_with_thresholds(self, data: pd.DataFrame, parameter: str, 
                                     title: str = "", auto_detect_thresholds: bool = True):
        """Plot parameter with threshold boundaries and alert zones"""
        try:
            if data.empty or self.figure is None:
                return
                
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Filter data for the parameter
            if 'param' in data.columns:
                param_data = data[data['param'] == parameter].copy()
            else:
                param_data = data.copy()
                
            if param_data.empty:
                ax.text(0.5, 0.5, f'No data available for {parameter}', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
                self.canvas.draw()
                return
                
            # Sort by datetime for proper line plotting
            param_data = param_data.sort_values('datetime')
            
            # Auto-detect thresholds if enabled and not manually set
            if auto_detect_thresholds and parameter not in self.thresholds:
                self._auto_detect_thresholds(param_data, parameter)
                
            # Plot the main parameter line
            x_data = param_data['datetime']
            y_data = param_data['avg'] if 'avg' in param_data.columns else param_data['average']
            
            # Color-code the line based on threshold status
            self._plot_threshold_colored_line(ax, x_data, y_data, parameter)
            
            # Add threshold bands and lines
            self._add_threshold_visualization(ax, x_data, parameter)
            
            # Add statistical bounds if available
            if 'min' in param_data.columns and 'max' in param_data.columns:
                ax.fill_between(x_data, param_data['min'], param_data['max'], 
                              alpha=0.1, color='blue', label='Min/Max Range')
                              
            # Configure the plot
            ax.set_title(f'{title}\nThreshold Monitoring: {parameter}', fontweight='bold', fontsize=12)
            ax.set_xlabel('Time', fontweight='bold')
            ax.set_ylabel('Value', fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right', framealpha=0.9)
            
            # Format time axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            self.figure.autofmt_xdate()
            
            # Add alert zone indicators
            self._add_alert_indicators(ax, param_data, parameter)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            # Add interactive capabilities
            if hasattr(self, 'interactive_manager'):
                self.interactive_manager = InteractivePlotManager(self.figure, ax, self.canvas)
                
        except Exception as e:
            print(f"Error plotting threshold visualization: {e}")
            
    def _auto_detect_thresholds(self, param_data: pd.DataFrame, parameter: str):
        """Automatically detect reasonable threshold values based on data statistics"""
        try:
            values = param_data['avg'] if 'avg' in param_data.columns else param_data['average']
            
            # Statistical analysis for threshold detection
            mean_val = values.mean()
            std_val = values.std()
            median_val = values.median()
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            
            # Use interquartile range method for robust threshold detection
            warning_min = q1 - (1.5 * iqr)
            warning_max = q3 + (1.5 * iqr)
            critical_min = q1 - (3 * iqr)  
            critical_max = q3 + (3 * iqr)
            
            # Ensure thresholds make sense (don't allow negative for certain parameters)
            if any(keyword in parameter.lower() for keyword in ['temp', 'flow', 'speed', 'voltage']):
                critical_min = max(0, critical_min)
                warning_min = max(0, warning_min)
                
            self.set_parameter_thresholds(
                parameter,
                min_threshold=critical_min,
                max_threshold=critical_max,
                warning_min=warning_min,
                warning_max=warning_max
            )
            
        except Exception as e:
            print(f"Error auto-detecting thresholds: {e}")
            
    def _plot_threshold_colored_line(self, ax, x_data, y_data, parameter: str):
        """Plot line with colors based on threshold status"""
        try:
            thresholds = self.thresholds.get(parameter, {})
            
            if not thresholds or all(v is None for v in thresholds.values()):
                # No thresholds defined, plot normal line
                ax.plot(x_data, y_data, linewidth=2, alpha=0.8, label=parameter)
                return
                
            # Create segments based on threshold status
            segments = []
            colors = []
            
            for i in range(len(y_data)):
                value = y_data.iloc[i]
                color = self._get_threshold_color(value, thresholds)
                
                if i == 0:
                    segments.append(([x_data.iloc[i]], [value]))
                    colors.append(color)
                else:
                    # Extend current segment or start new one
                    if colors[-1] == color:
                        segments[-1][0].append(x_data.iloc[i])
                        segments[-1][1].append(value)
                    else:
                        segments.append(([x_data.iloc[i-1], x_data.iloc[i]], [y_data.iloc[i-1], value]))
                        colors.append(color)
                        
            # Plot each segment with its color
            for segment, color in zip(segments, colors):
                if len(segment[0]) > 1:
                    ax.plot(segment[0], segment[1], color=color, linewidth=2, alpha=0.8)
                    
            # Add legend for threshold status
            ax.plot([], [], color='green', linewidth=2, label='Normal')
            ax.plot([], [], color='orange', linewidth=2, label='Warning')
            ax.plot([], [], color='red', linewidth=2, label='Critical')
            
        except Exception as e:
            print(f"Error plotting threshold-colored line: {e}")
            # Fallback to simple line
            ax.plot(x_data, y_data, linewidth=2, alpha=0.8, label=parameter)
            
    def _get_threshold_color(self, value: float, thresholds: dict) -> str:
        """Determine color based on threshold status"""
        warning_min = thresholds.get('warning_min')
        warning_max = thresholds.get('warning_max')
        critical_min = thresholds.get('min')
        critical_max = thresholds.get('max')
        
        # Check critical thresholds first
        if critical_min is not None and value < critical_min:
            return 'red'
        if critical_max is not None and value > critical_max:
            return 'red'
            
        # Check warning thresholds
        if warning_min is not None and value < warning_min:
            return 'orange'
        if warning_max is not None and value > warning_max:
            return 'orange'
            
        return 'green'  # Normal range
        
    def _add_threshold_visualization(self, ax, x_data, parameter: str):
        """Add threshold lines and bands to the plot"""
        try:
            thresholds = self.thresholds.get(parameter, {})
            if not thresholds:
                return
                
            x_min, x_max = ax.get_xlim() if hasattr(ax, 'get_xlim') else (x_data.min(), x_data.max())
            
            # Add critical threshold lines
            if thresholds.get('min') is not None:
                ax.axhline(y=thresholds['min'], color='red', linestyle='--', linewidth=2, 
                          alpha=0.7, label='Critical Min')
            if thresholds.get('max') is not None:
                ax.axhline(y=thresholds['max'], color='red', linestyle='--', linewidth=2, 
                          alpha=0.7, label='Critical Max')
                          
            # Add warning threshold lines
            if thresholds.get('warning_min') is not None:
                ax.axhline(y=thresholds['warning_min'], color='orange', linestyle=':', linewidth=1.5, 
                          alpha=0.7, label='Warning Min')
            if thresholds.get('warning_max') is not None:
                ax.axhline(y=thresholds['warning_max'], color='orange', linestyle=':', linewidth=1.5, 
                          alpha=0.7, label='Warning Max')
                          
            # Add threshold bands
            if thresholds.get('warning_min') is not None and thresholds.get('min') is not None:
                ax.fill_between([x_min, x_max], [thresholds['min']] * 2, [thresholds['warning_min']] * 2,
                              alpha=0.1, color='red', label='Critical Zone (Low)')
                              
            if thresholds.get('warning_max') is not None and thresholds.get('max') is not None:
                ax.fill_between([x_min, x_max], [thresholds['warning_max']] * 2, [thresholds['max']] * 2,
                              alpha=0.1, color='red', label='Critical Zone (High)')
                              
            # Add normal operating band
            if thresholds.get('warning_min') is not None and thresholds.get('warning_max') is not None:
                ax.fill_between([x_min, x_max], [thresholds['warning_min']] * 2, [thresholds['warning_max']] * 2,
                              alpha=0.05, color='green', label='Normal Operating Range')
                              
        except Exception as e:
            print(f"Error adding threshold visualization: {e}")
            
    def _add_alert_indicators(self, ax, param_data: pd.DataFrame, parameter: str):
        """Add visual alert indicators for threshold violations"""
        try:
            thresholds = self.thresholds.get(parameter, {})
            if not thresholds:
                return
                
            y_data = param_data['avg'] if 'avg' in param_data.columns else param_data['average']
            x_data = param_data['datetime']
            
            # Find threshold violations
            violations = []
            for i, (x, y) in enumerate(zip(x_data, y_data)):
                violation_type = None
                
                # Check for critical violations
                if (thresholds.get('min') is not None and y < thresholds['min']) or \
                   (thresholds.get('max') is not None and y > thresholds['max']):
                    violation_type = 'critical'
                # Check for warning violations
                elif (thresholds.get('warning_min') is not None and y < thresholds['warning_min']) or \
                     (thresholds.get('warning_max') is not None and y > thresholds['warning_max']):
                    violation_type = 'warning'
                    
                if violation_type:
                    violations.append((x, y, violation_type))
                    
            # Plot violation markers
            if violations:
                critical_x = [v[0] for v in violations if v[2] == 'critical']
                critical_y = [v[1] for v in violations if v[2] == 'critical']
                warning_x = [v[0] for v in violations if v[2] == 'warning']
                warning_y = [v[1] for v in violations if v[2] == 'warning']
                
                if critical_x:
                    ax.scatter(critical_x, critical_y, color='red', s=50, marker='X', 
                             alpha=0.8, label='Critical Alerts', zorder=5)
                if warning_x:
                    ax.scatter(warning_x, warning_y, color='orange', s=30, marker='!', 
                             alpha=0.8, label='Warning Alerts', zorder=5)
                             
        except Exception as e:
            print(f"Error adding alert indicators: {e}")
            
    def get_threshold_summary(self, parameter: str) -> dict:
        """Get summary of threshold status for a parameter"""
        try:
            thresholds = self.thresholds.get(parameter, {})
            return {
                'parameter': parameter,
                'has_thresholds': bool(thresholds),
                'thresholds': thresholds,
                'status': 'configured' if thresholds else 'not_configured'
            }
        except Exception as e:
            print(f"Error getting threshold summary: {e}")
            return {'parameter': parameter, 'status': 'error'}


# Standalone utility functions for backwards compatibility
def create_summary_chart(data: pd.DataFrame, title: str = "Parameter Summary") -> Figure:
    """Create summary chart with professional styling"""
    fig = Figure(figsize=(12, 8), dpi=100)
    
    # Apply professional styling
    PlotUtils.setup_professional_style()
    
    if data.empty:
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, 'No data available for summary', 
               ha='center', va='center', transform=ax.transAxes, fontsize=14)
        return fig
    
    # Group parameters and create multi-subplot visualization
    if 'param' in data.columns:
        unique_params = data['param'].unique()[:6]  # Limit to 6 for readability
        
        rows = min(3, len(unique_params))
        cols = min(2, (len(unique_params) + 1) // 2)
        
        for i, param in enumerate(unique_params):
            ax = fig.add_subplot(rows, cols, i + 1)
            param_data = data[data['param'] == param]
            
            # Plot using PlotUtils methodology
            if 'datetime' in param_data.columns and 'avg' in param_data.columns:
                param_data = param_data.sort_values('datetime')
                ax.plot(param_data['datetime'], param_data['avg'], 
                       marker='o', markersize=2, linewidth=1.5, alpha=0.8)
                ax.set_title(param, fontsize=10, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
                # Format x-axis
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                fig.autofmt_xdate()
    
    fig.suptitle(title, fontsize=14, fontweight='bold')
    fig.tight_layout()
    
    return fig


def apply_professional_style():
    """Apply professional styling globally"""
    PlotUtils.setup_professional_style()


# Legacy function aliases for backwards compatibility with main.py
def plot_trend(widget, df: pd.DataFrame, title_suffix: str = ""):
    """Plot trend data - legacy function for backwards compatibility"""
    try:
        if hasattr(widget, 'plot_parameter_trends'):
            # Use enhanced widget functionality
            if not df.empty and 'param' in df.columns:
                # Get the first parameter for plotting
                first_param = df['param'].iloc[0]
                widget.plot_parameter_trends(df, first_param, title_suffix)
            else:
                widget.plot_parameter_trends(df, "Data", title_suffix)
        else:
            # Fallback for legacy widgets
            PlotUtils._plot_parameter_data_single(widget, df, title_suffix or "Trend")
    except Exception as e:
        print(f"Legacy plot_trend error: {e}")


def reset_plot_view(widget):
    """Reset plot view - legacy function"""
    try:
        if hasattr(widget, 'interactive_manager') and widget.interactive_manager:
            widget.interactive_manager.reset_view()
        elif hasattr(widget, 'canvas'):
            widget.canvas.draw()
    except Exception as e:
        print(f"Reset plot view error: {e}")