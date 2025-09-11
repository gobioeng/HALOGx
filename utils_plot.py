"""
Legacy utils_plot.py - Now redirects to unified plot_utils.py
This file maintains backwards compatibility while using the enhanced unified plotting system.
"""

# Import everything from the unified plotting system
from plot_utils import (
    PlotUtils, 
    InteractivePlotManager,
    EnhancedPlotWidget,
    EnhancedDualPlotWidget,
    plot_trend,
    reset_plot_view,
    create_summary_chart,
    apply_professional_style
)

# Legacy imports for backwards compatibility
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import timedelta

# Set matplotlib style for professional appearance
plt.style.use('default')

# All functionality is now handled by the unified system in plot_utils.py
# This file serves as a compatibility layer for existing imports

# Legacy function aliases for specific functions that might be called directly
def _zoom_to_hours(canvas, axes, hours):
    """Legacy zoom function - redirects to InteractivePlotManager"""
    if hasattr(axes, '__iter__'):
        ax = axes[0]
    else:
        ax = axes
    
    if hasattr(ax, 'figure'):
        manager = InteractivePlotManager(ax.figure, ax, canvas)
        manager._zoom_to_time_range(ax, hours)

def _fit_all_data(canvas, axes):
    """Legacy fit data function - redirects to InteractivePlotManager"""
    if hasattr(axes, '__iter__'):
        ax = axes[0]
    else:
        ax = axes
        
    if hasattr(ax, 'figure'):
        manager = InteractivePlotManager(ax.figure, ax, canvas)
        manager._fit_all_data(ax)

# All other legacy functions are handled by the unified PlotUtils class
# and the enhanced widget classes in plot_utils.py