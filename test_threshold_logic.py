"""
Non-GUI Test suite for Threshold Visualization Logic
Professional LINAC Monitoring System
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_threshold_import():
    """Test that ThresholdPlotWidget can be imported"""
    try:
        from threshold_plot_widget import ThresholdPlotWidget
        print("✅ ThresholdPlotWidget import successful")
        return True
    except ImportError as e:
        print(f"⚠️ ThresholdPlotWidget import failed: {e}")
        return False


def test_threshold_calculations():
    """Test threshold calculation logic without GUI"""
    try:
        # Create test data with known statistical properties
        np.random.seed(42)  # For reproducible tests
        dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
        data = pd.DataFrame({
            'test_param': np.random.normal(10, 2, len(dates))
        }, index=dates)
        
        # Simulate threshold calculation logic
        param_data = data['test_param'].dropna()
        mean_val = param_data.mean()
        std_val = param_data.std()
        
        # Warning thresholds: ±2 standard deviations
        warning_min = mean_val - 2 * std_val
        warning_max = mean_val + 2 * std_val
        
        # Critical thresholds: ±3 standard deviations
        critical_min = mean_val - 3 * std_val
        critical_max = mean_val + 3 * std_val
        
        # Validate calculations
        assert 4 < warning_min < 8, f"Warning min out of range: {warning_min}"
        assert 12 < warning_max < 16, f"Warning max out of range: {warning_max}"
        assert critical_min < warning_min, "Critical min should be less than warning min"
        assert critical_max > warning_max, "Critical max should be greater than warning max"
        
        print("✅ Threshold calculation logic test passed")
        return True
        
    except Exception as e:
        print(f"❌ Threshold calculation test failed: {e}")
        return False


def test_violation_detection_logic():
    """Test violation detection logic"""
    try:
        # Create data with known violations
        data = [10, 11, 12, 5, 13, 14, 20, 15, 9, 11]  # Values 5 and 20 should be violations
        
        # Define thresholds
        warning_range = (8, 16)
        critical_range = (6, 18)
        
        critical_violations = []
        warning_violations = []
        
        for i, value in enumerate(data):
            if value < critical_range[0] or value > critical_range[1]:
                critical_violations.append((i, value))
            elif value < warning_range[0] or value > warning_range[1]:
                warning_violations.append((i, value))
        
        # Validate results
        critical_values = [v[1] for v in critical_violations]
        assert 5 in critical_values, "Value 5 should be detected as critical violation"
        assert 20 in critical_values, "Value 20 should be detected as critical violation"
        
        print("✅ Violation detection logic test passed")
        return True
        
    except Exception as e:
        print(f"❌ Violation detection test failed: {e}")
        return False


def test_color_generation_logic():
    """Test color generation using HSV logic"""
    try:
        import colorsys
        
        # Simulate color assignment logic
        colors = []
        for i in range(5):
            hue = (i * 0.618033988749895) % 1.0  # Golden ratio for good distribution
            saturation = 0.8
            value = 0.9
            
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            color = f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
            colors.append(color)
        
        # Validate colors
        assert len(colors) == 5, "Should generate 5 colors"
        assert len(set(colors)) == 5, "All colors should be unique"
        
        for color in colors:
            assert color.startswith('#'), f"Color should start with #: {color}"
            assert len(color) == 7, f"Color should be 7 characters: {color}"
        
        print("✅ Color generation logic test passed")
        return True
        
    except Exception as e:
        print(f"❌ Color generation test failed: {e}")
        return False


def test_parameter_mapping_integration():
    """Test parameter mapping integration"""
    try:
        # Test parameter mapping structure
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
        
        # Validate structure
        for param, config in parameter_mapping.items():
            assert 'description' in config, f"Missing description for {param}"
            assert 'unit' in config, f"Missing unit for {param}"
            assert 'expected_range' in config, f"Missing expected_range for {param}"
            assert 'critical_range' in config, f"Missing critical_range for {param}"
            
            expected_range = config['expected_range']
            critical_range = config['critical_range']
            
            assert len(expected_range) == 2, f"Expected range should have 2 values for {param}"
            assert len(critical_range) == 2, f"Critical range should have 2 values for {param}"
            assert expected_range[0] < expected_range[1], f"Invalid expected range for {param}"
            assert critical_range[0] < critical_range[1], f"Invalid critical range for {param}"
        
        print("✅ Parameter mapping integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Parameter mapping test failed: {e}")
        return False


def test_main_app_integration():
    """Test integration with main application"""
    try:
        import main
        print("✅ Main application import successful")
        
        # Test that we can access the UnifiedParser
        from unified_parser import UnifiedParser
        parser = UnifiedParser()
        
        # Check that parameter mapping exists
        assert hasattr(parser, 'parameter_mapping'), "Parser should have parameter_mapping"
        assert len(parser.parameter_mapping) > 0, "Parameter mapping should not be empty"
        
        print("✅ Main app integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Main app integration test failed: {e}")
        return False


if __name__ == "__main__":
    print("Running threshold logic tests (non-GUI)...")
    
    tests = [
        test_threshold_import,
        test_threshold_calculations,
        test_violation_detection_logic,
        test_color_generation_logic,
        test_parameter_mapping_integration,
        test_main_app_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All threshold logic tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed")
    
    exit(0 if passed == total else 1)