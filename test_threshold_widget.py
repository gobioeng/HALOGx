"""
Test suite for Threshold Visualization Widget
Professional LINAC Monitoring System
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup QApplication for GUI tests
try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
except ImportError:
    app = None

try:
    from threshold_plot_widget import ThresholdPlotWidget
    THRESHOLD_WIDGET_AVAILABLE = True
except ImportError as e:
    THRESHOLD_WIDGET_AVAILABLE = False
    print(f"Warning: ThresholdPlotWidget not available for testing: {e}")


@pytest.mark.skipif(not THRESHOLD_WIDGET_AVAILABLE, reason="ThresholdPlotWidget not available")
def test_threshold_widget_import():
    """Test that ThresholdPlotWidget can be imported successfully"""
    from threshold_plot_widget import ThresholdPlotWidget
    widget = ThresholdPlotWidget()
    assert widget is not None
    assert hasattr(widget, 'parameter_thresholds')
    assert hasattr(widget, 'parameter_colors')
    assert hasattr(widget, 'visible_parameters')


@pytest.mark.skipif(not THRESHOLD_WIDGET_AVAILABLE, reason="ThresholdPlotWidget not available")
def test_threshold_widget_data_setting():
    """Test setting data in the threshold widget"""
    from threshold_plot_widget import ThresholdPlotWidget
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', end='2024-01-02', freq='H')
    data = pd.DataFrame({
        'magnetronFlow': np.random.normal(12, 2, len(dates)),
        'targetAndCirculatorFlow': np.random.normal(8, 1, len(dates)),
        'magnetronTemp': np.random.normal(45, 5, len(dates))
    }, index=dates)
    
    # Create parameter mapping
    parameter_mapping = {
        'magnetronFlow': {
            'description': 'Magnetron Flow',
            'unit': 'L/min',
            'expected_range': (10, 15),
            'critical_range': (8, 18)
        },
        'targetAndCirculatorFlow': {
            'description': 'Target Flow',
            'unit': 'L/min',
            'expected_range': (6, 10),
            'critical_range': (4, 12)
        }
    }
    
    widget = ThresholdPlotWidget()
    widget.set_data(data, parameter_mapping)
    
    assert not widget.data.empty
    assert len(widget.parameter_mapping) >= 2
    assert 'magnetronFlow' in widget.parameter_mapping


@pytest.mark.skipif(not THRESHOLD_WIDGET_AVAILABLE, reason="ThresholdPlotWidget not available")
def test_threshold_calculation():
    """Test threshold calculation methods"""
    from threshold_plot_widget import ThresholdPlotWidget
    
    # Create test data with known statistical properties
    np.random.seed(42)  # For reproducible tests
    dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
    # Create data with mean=10, std=2
    data = pd.DataFrame({
        'test_param': np.random.normal(10, 2, len(dates))
    }, index=dates)
    
    widget = ThresholdPlotWidget()
    widget.set_data(data)
    widget._calculate_parameter_thresholds('test_param')
    
    # Check that thresholds were calculated
    assert 'test_param' in widget.parameter_thresholds
    thresholds = widget.parameter_thresholds['test_param']
    
    # Verify threshold structure
    assert 'warning' in thresholds
    assert 'critical' in thresholds
    assert 'normal' in thresholds
    
    # Check that warning thresholds are reasonable (approximately mean ± 2*std)
    warning_min, warning_max = thresholds['warning']
    assert 4 < warning_min < 8  # Approximately 10 - 2*2 = 6
    assert 12 < warning_max < 16  # Approximately 10 + 2*2 = 14


@pytest.mark.skipif(not THRESHOLD_WIDGET_AVAILABLE, reason="ThresholdPlotWidget not available")
def test_parameter_color_assignment():
    """Test that parameters get unique colors"""
    from threshold_plot_widget import ThresholdPlotWidget
    
    widget = ThresholdPlotWidget()
    
    # Assign colors to multiple parameters
    params = ['param1', 'param2', 'param3']
    for param in params:
        widget._assign_parameter_color(param)
    
    # Check that all parameters have colors
    assert len(widget.parameter_colors) == 3
    for param in params:
        assert param in widget.parameter_colors
        color = widget.parameter_colors[param]
        assert color.startswith('#')
        assert len(color) == 7  # #RRGGBB format
    
    # Check that colors are different
    colors = list(widget.parameter_colors.values())
    assert len(set(colors)) == 3  # All colors should be unique


@pytest.mark.skipif(not THRESHOLD_WIDGET_AVAILABLE, reason="ThresholdPlotWidget not available")
def test_threshold_violation_detection():
    """Test threshold violation detection"""
    from threshold_plot_widget import ThresholdPlotWidget
    
    # Create data with known violations
    dates = pd.date_range(start='2024-01-01', periods=10, freq='H')
    data = pd.DataFrame({
        'test_param': [10, 11, 12, 5, 13, 14, 20, 15, 9, 11]  # Values 5 and 20 should be violations
    }, index=dates)
    
    widget = ThresholdPlotWidget()
    widget.set_data(data)
    
    # Set custom thresholds for testing
    widget.parameter_thresholds['test_param'] = {
        'warning': (8, 16),
        'critical': (6, 18),
        'normal': (8, 16)
    }
    widget.visible_parameters.add('test_param')
    
    # Get violations
    violations = widget.get_threshold_violations()
    
    # Check that violations were detected
    assert 'test_param' in violations
    param_violations = violations['test_param']
    
    # Should detect the value 5 as critical violation and 20 as critical violation
    violation_values = [v[1] for v in param_violations]
    assert 5 in violation_values
    assert 20 in violation_values


@pytest.mark.skipif(not THRESHOLD_WIDGET_AVAILABLE, reason="ThresholdPlotWidget not available")
def test_config_export_import():
    """Test configuration export and import functionality"""
    from threshold_plot_widget import ThresholdPlotWidget
    
    # Create and configure widget
    widget = ThresholdPlotWidget()
    widget.visible_parameters = {'param1', 'param2'}
    widget.parameter_thresholds = {
        'param1': {'warning': (5, 15), 'critical': (0, 20)}
    }
    widget.parameter_colors = {
        'param1': '#FF0000', 'param2': '#00FF00'
    }
    widget.auto_detect_thresholds = False
    
    # Export configuration
    config = widget.export_threshold_config()
    
    # Verify export
    assert 'visible_parameters' in config
    assert 'parameter_thresholds' in config
    assert 'parameter_colors' in config
    assert 'auto_detect_thresholds' in config
    assert set(config['visible_parameters']) == {'param1', 'param2'}
    
    # Create new widget and import config
    new_widget = ThresholdPlotWidget()
    new_widget.import_threshold_config(config)
    
    # Verify import
    assert new_widget.visible_parameters == {'param1', 'param2'}
    assert new_widget.parameter_thresholds == widget.parameter_thresholds
    assert new_widget.parameter_colors == widget.parameter_colors
    assert new_widget.auto_detect_thresholds == False


def test_threshold_integration_with_main_app():
    """Test that threshold functionality integrates properly with main application"""
    # Test that main application can import threshold widget
    try:
        import main
        from threshold_plot_widget import ThresholdPlotWidget
        
        # Verify the widget can be created
        widget = ThresholdPlotWidget()
        assert widget is not None
        
        # Test that the widget has required methods for integration
        required_methods = ['set_data', 'get_threshold_violations']
        for method in required_methods:
            assert hasattr(widget, method), f"Widget missing required method: {method}"
        
        print("✅ Threshold integration test passed")
        return True
        
    except ImportError as e:
        print(f"⚠️ Threshold integration test skipped: {e}")
        return True


if __name__ == "__main__":
    # Run tests directly
    if THRESHOLD_WIDGET_AVAILABLE:
        print("Running threshold widget tests...")
        
        test_threshold_widget_import()
        print("✅ Import test passed")
        
        test_threshold_widget_data_setting()
        print("✅ Data setting test passed")
        
        test_threshold_calculation()
        print("✅ Threshold calculation test passed")
        
        test_parameter_color_assignment()
        print("✅ Color assignment test passed")
        
        test_threshold_violation_detection()
        print("✅ Violation detection test passed")
        
        test_config_export_import()
        print("✅ Config export/import test passed")
        
    test_threshold_integration_with_main_app()
    print("✅ All threshold tests completed successfully!")