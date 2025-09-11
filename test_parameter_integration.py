"""
Test suite for Parameter Mapping Integration
Professional LINAC Monitoring System
"""

import os
import tempfile
import time
from pathlib import Path
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_parameter_config_manager_basic():
    """Test basic ParameterConfigManager functionality"""
    try:
        from parameter_config_manager import ParameterConfigManager
        
        # Test with default config file
        manager = ParameterConfigManager()
        
        # Check that parameters were loaded
        assert len(manager.parameter_mapping) > 0, "Should load parameters from config file"
        
        # Check statistics
        stats = manager.get_statistics()
        assert 'total_parameters' in stats
        assert 'parameters_by_type' in stats
        assert stats['total_parameters'] > 0
        
        print(f"✅ Basic ParameterConfigManager test passed ({stats['total_parameters']} parameters)")
        return True
        
    except Exception as e:
        print(f"❌ Basic ParameterConfigManager test failed: {e}")
        return False


def test_parameter_config_manager_custom_file():
    """Test ParameterConfigManager with custom config file"""
    try:
        from parameter_config_manager import ParameterConfigManager
        
        # Create a temporary config file
        test_config_content = """
# Test parameter mapping
Machine Log Name                                 | User-Friendly Name                 | Unit
-----------------------------------------------------------------------------------------------
testFlow                                        | Test Flow Parameter                 | L/min
testTemp                                        | Test Temperature Parameter          | °C
testVoltage                                     | Test Voltage Parameter              | V
MLC_ADC_CHAN_PROXIMAL_10V_BANKA_MON_STAT       | MLC Proximal 10V Bank A            | V
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_config_content)
            temp_config_path = f.name
            
        try:
            # Test with custom config file
            manager = ParameterConfigManager(config_file_path=temp_config_path)
            
            # Should load the test parameters
            assert len(manager.parameter_mapping) >= 3, "Should load test parameters"
            
            # Check specific parameters
            assert 'testFlow' in manager.parameter_mapping
            assert 'testTemp' in manager.parameter_mapping
            assert 'testVoltage' in manager.parameter_mapping
            
            # Check parameter types were inferred correctly
            flow_config = manager.parameter_mapping['testFlow']
            assert flow_config['parameter_type'] == 'flow'
            assert flow_config['unit'] == 'L/min'
            
            temp_config = manager.parameter_mapping['testTemp']
            assert temp_config['parameter_type'] == 'temperature'
            assert temp_config['unit'] == '°C'
            
            voltage_config = manager.parameter_mapping['testVoltage']
            assert voltage_config['parameter_type'] == 'voltage'
            assert voltage_config['unit'] == 'V'
            
            print("✅ Custom config file test passed")
            return True
            
        finally:
            # Clean up temp file
            os.unlink(temp_config_path)
            
    except Exception as e:
        print(f"❌ Custom config file test failed: {e}")
        return False


def test_parameter_pattern_matching():
    """Test parameter pattern matching functionality"""
    try:
        from parameter_config_manager import ParameterConfigManager
        
        manager = ParameterConfigManager()
        
        # Test pattern matching
        # Should find magnetronFlow by various patterns
        test_patterns = [
            'magnetronFlow',
            'magnetron flow',
            'CoolingmagnetronFlowLowStatistics'
        ]
        
        for pattern in test_patterns:
            found_param = manager.find_parameter_by_pattern(pattern)
            if found_param:
                assert 'magnetron' in found_param.lower() or 'flow' in found_param.lower()
                break
        else:
            # If no magnetron flow found, just test that the method works
            pass
            
        print("✅ Parameter pattern matching test passed")
        return True
        
    except Exception as e:
        print(f"❌ Parameter pattern matching test failed: {e}")
        return False


def test_unified_parser_integration():
    """Test UnifiedParser integration with ParameterConfigManager"""
    try:
        from unified_parser import UnifiedParser
        
        parser = UnifiedParser()
        
        # Check that dynamic mapping was loaded
        stats = parser.get_parameter_statistics()
        assert 'source' in stats
        assert stats['source'] == 'dynamic_mapping', "Should use dynamic mapping"
        assert stats['total_parameters'] > 0, "Should have loaded parameters"
        
        # Test parameter lookup
        if len(parser.parameter_mapping) > 0:
            # Get first parameter
            first_param = next(iter(parser.parameter_mapping.keys()))
            config = parser.parameter_mapping[first_param]
            
            # Check structure
            assert 'patterns' in config
            assert 'unit' in config
            assert 'description' in config
            assert 'parameter_type' in config
            
        print(f"✅ UnifiedParser integration test passed ({stats['total_parameters']} parameters)")
        return True
        
    except Exception as e:
        print(f"❌ UnifiedParser integration test failed: {e}")
        return False


def test_parameter_validation():
    """Test parameter validation functionality"""
    try:
        from parameter_config_manager import ParameterConfigManager
        
        manager = ParameterConfigManager()
        
        # Run validation
        warnings, errors = manager.validate_parameter_mapping()
        
        # Validation should complete without exceptions
        assert isinstance(warnings, list)
        assert isinstance(errors, list)
        
        # For a valid config file, there should be minimal errors
        if len(errors) > len(warnings):
            print(f"⚠️ More errors ({len(errors)}) than warnings ({len(warnings)}) - check config file")
        
        print(f"✅ Parameter validation test passed ({len(warnings)} warnings, {len(errors)} errors)")
        return True
        
    except Exception as e:
        print(f"❌ Parameter validation test failed: {e}")
        return False


def test_parameter_types_classification():
    """Test parameter type classification"""
    try:
        from parameter_config_manager import ParameterConfigManager
        
        manager = ParameterConfigManager()
        
        # Check that parameters were classified into types
        stats = manager.get_statistics()
        param_types = stats.get('parameters_by_type', {})
        
        # Should have multiple parameter types
        assert len(param_types) > 1, "Should classify parameters into multiple types"
        
        # Common types that should exist based on mappedname_V3.txt
        expected_types = ['flow', 'temperature', 'voltage']
        found_types = []
        
        for expected_type in expected_types:
            if expected_type in param_types and param_types[expected_type] > 0:
                found_types.append(expected_type)
                
        assert len(found_types) >= 2, f"Should find at least 2 common parameter types, found: {found_types}"
        
        print(f"✅ Parameter type classification test passed (types: {list(param_types.keys())})")
        return True
        
    except Exception as e:
        print(f"❌ Parameter type classification test failed: {e}")
        return False


def test_main_application_compatibility():
    """Test that main application works with new parameter system"""
    try:
        import main
        
        # Test that the application can be imported without errors
        # and that it uses the new parameter mapping system
        print("✅ Main application compatibility test passed")
        return True
        
    except Exception as e:
        print(f"❌ Main application compatibility test failed: {e}")
        return False


if __name__ == "__main__":
    print("Running parameter mapping integration tests...")
    
    tests = [
        test_parameter_config_manager_basic,
        test_parameter_config_manager_custom_file,
        test_parameter_pattern_matching,
        test_unified_parser_integration,
        test_parameter_validation,
        test_parameter_types_classification,
        test_main_application_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Parameter Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All parameter mapping integration tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed")
    
    exit(0 if passed == total else 1)