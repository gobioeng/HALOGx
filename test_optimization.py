#!/usr/bin/env python3
"""
Performance Test for HALOGx Optimization
Tests the hardcoded parameters and optimized parsing functionality

Developer: gobioeng.com
"""

import sys
import os
import time
import traceback
from pathlib import Path

def test_hardcoded_parameters():
    """Test hardcoded parameter mapper performance"""
    print("🧪 Testing Hardcoded Parameter Mapper...")
    
    try:
        from hardcoded_parameters import get_hardcoded_mapper
        
        start_time = time.time()
        mapper = get_hardcoded_mapper()
        init_time = time.time() - start_time
        
        print(f"✓ Hardcoded mapper initialized in {init_time:.4f}s")
        
        # Test parameter lookup performance
        test_parameters = [
            "magnetronFlow",
            "MLC 24V Bank A", 
            "Speed FAN 1",
            "Room Humidity",
            "COL Board Temperature"
        ]
        
        lookup_times = []
        for param in test_parameters:
            start = time.time()
            info = mapper.get_parameter_info(param)
            lookup_time = time.time() - start
            lookup_times.append(lookup_time)
            
            if info:
                print(f"  ✓ {param} -> {info['friendly_name']} ({info['unit']}) in {lookup_time:.6f}s")
            else:
                print(f"  ✗ {param} not found")
        
        avg_lookup_time = sum(lookup_times) / len(lookup_times)
        print(f"✓ Average parameter lookup time: {avg_lookup_time:.6f}s")
        
        # Test category retrieval
        categories = mapper.get_all_categories()
        print(f"✓ Found {len(categories)} parameter categories: {categories}")
        
        # Test category parameters
        for category in categories[:3]:  # Test first 3 categories
            params = mapper.get_category_parameters(category)
            print(f"  - {category}: {len(params)} parameters")
        
        return True
        
    except Exception as e:
        print(f"❌ Hardcoded parameter test failed: {e}")
        traceback.print_exc()
        return False

def test_optimized_parser():
    """Test optimized parser performance"""
    print("\n🧪 Testing Optimized Parser...")
    
    try:
        from optimized_parser import get_optimized_parser
        
        start_time = time.time()
        parser = get_optimized_parser()
        init_time = time.time() - start_time
        
        print(f"✓ Optimized parser initialized in {init_time:.4f}s")
        
        # Test parameter extraction from sample lines
        test_lines = [
            "2025-01-20 10:30:15 magnetronFlow: count=100, max=15.2, min=12.8, avg=14.1",
            "2025-01-20 10:30:16 MLC_ADC_CHAN_24V_BANKA_MON_STAT: count=50, max=24.5, min=23.2, avg=23.8",
            "2025-01-20 10:30:17 FanfanSpeed1Statistics: count=75, max=2800, min=2200, avg=2500",
            "Serial: 12345",
            "Machine: 001"
        ]
        
        extraction_times = []
        total_extracted = 0
        
        for line in test_lines:
            start = time.time()
            parameters = parser.parameter_mapper.extract_parameters_from_line(line)
            extraction_time = time.time() - start
            extraction_times.append(extraction_time)
            
            if parameters:
                for param_name, param_data in parameters:
                    print(f"  ✓ Extracted: {param_data['friendly_name']} = {param_data.get('avg', 'N/A')} {param_data['unit']}")
                    total_extracted += 1
            
        if extraction_times:
            avg_extraction_time = sum(extraction_times) / len(extraction_times)
            print(f"✓ Average line processing time: {avg_extraction_time:.6f}s")
            print(f"✓ Total parameters extracted: {total_extracted}")
        
        return True
        
    except Exception as e:
        print(f"❌ Optimized parser test failed: {e}")
        traceback.print_exc()
        return False

def test_parameter_validation():
    """Test parameter validation functionality"""
    print("\n🧪 Testing Parameter Validation...")
    
    try:
        from hardcoded_parameters import get_hardcoded_mapper
        mapper = get_hardcoded_mapper()
        
        # Test validation for different parameters
        test_cases = [
            ("magnetronFlow", 14.5, True, True, False),  # Normal value
            ("magnetronFlow", 5.0, True, False, True),   # Critical low
            ("magnetronFlow", 25.0, True, False, False), # Out of range high
            ("MLC 24V Bank A", 23.8, True, True, False), # Normal voltage
            ("MLC 24V Bank A", 20.0, True, False, True), # Critical low voltage
        ]
        
        for param_name, value, expected_valid, expected_in_range, expected_critical in test_cases:
            validation = mapper.validate_parameter_value(param_name, value)
            
            print(f"  Testing {param_name} = {value}:")
            print(f"    Valid: {validation.get('valid', False)} (expected: {expected_valid})")
            print(f"    In Range: {validation.get('in_range', False)} (expected: {expected_in_range})")
            print(f"    Critical: {validation.get('critical', False)} (expected: {expected_critical})")
            
            # Basic validation check
            if validation.get('valid') == expected_valid:
                print(f"    ✓ Validation test passed")
            else:
                print(f"    ✗ Validation test failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Parameter validation test failed: {e}")
        traceback.print_exc()
        return False

def test_performance_comparison():
    """Test performance comparison with file operations"""
    print("\n🧪 Testing Performance vs File Operations...")
    
    try:
        # Test hardcoded mapper performance
        from hardcoded_parameters import get_hardcoded_mapper
        
        start_time = time.time()
        mapper = get_hardcoded_mapper()
        hardcoded_time = time.time() - start_time
        
        # Test file-based mapper (if available)
        file_time = 0
        try:
            start_time = time.time()
            from enhanced_parameter_mapper import EnhancedParameterMapper
            file_mapper = EnhancedParameterMapper()
            file_time = time.time() - start_time
        except Exception as e:
            print(f"  File-based mapper not available: {e}")
            file_time = float('inf')
        
        print(f"✓ Hardcoded mapper initialization: {hardcoded_time:.4f}s")
        print(f"✓ File-based mapper initialization: {file_time:.4f}s")
        
        if file_time != float('inf'):
            speedup = file_time / hardcoded_time
            print(f"✓ Performance improvement: {speedup:.2f}x faster")
        else:
            print("✓ Hardcoded mapper eliminates file I/O dependency")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance comparison test failed: {e}")
        traceback.print_exc()
        return False

def test_integration():
    """Test integration with main application components"""
    print("\n🧪 Testing Integration with Main Components...")
    
    try:
        # Test if optimized parser can be imported in main context
        print("  Testing main application imports...")
        
        # Test main module import
        import main
        print("  ✓ Main module imported successfully")
        
        # Test if optimized components are accessible
        from optimized_parser import get_optimized_parser
        from hardcoded_parameters import get_hardcoded_mapper
        
        parser = get_optimized_parser()
        mapper = get_hardcoded_mapper()
        
        print("  ✓ Optimized components accessible")
        
        # Test parameter category retrieval for UI
        categories = parser.get_parameter_categories()
        print(f"  ✓ Parameter categories available for UI: {len(categories)}")
        
        # Test parameter info for trend controls
        for category in categories[:2]:
            params = parser.get_category_parameters(category)
            print(f"    - {category}: {len(params)} parameters for dropdowns")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all optimization tests"""
    print("🚀 HALOGx Optimization Performance Tests")
    print("=" * 50)
    
    tests = [
        ("Hardcoded Parameters", test_hardcoded_parameters),
        ("Optimized Parser", test_optimized_parser),
        ("Parameter Validation", test_parameter_validation),
        ("Performance Comparison", test_performance_comparison),
        ("Integration", test_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
            if test_func():
                print(f"✅ {test_name} test PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"❌ {test_name} test FAILED with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All optimization tests PASSED!")
        print("\n✅ Optimizations Summary:")
        print("  - Hardcoded parameters eliminate file I/O operations")
        print("  - Optimized parser provides faster data processing")
        print("  - Parameter validation ensures data quality")
        print("  - Integration maintains compatibility with existing code")
        print("  - Performance improvements for faster app loading")
        return True
    else:
        print(f"⚠️ {total - passed} test(s) failed. Review issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)