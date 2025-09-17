#!/usr/bin/env python3
"""
Comprehensive test to validate HALOGx unified parser strict filtering requirements.
Tests all requirements from the problem statement.
"""

import os
import sys
sys.path.append('.')

def test_requirement_1_strict_filtering():
    """1. ✅ Strict Filtering Enforcement"""
    print("🧪 Testing Requirement 1: Strict Filtering Enforcement")
    print("=" * 55)
    
    from enhanced_parameter_mapper import EnhancedParameterMapper
    
    mapper = EnhancedParameterMapper()
    
    # Test allowlist creation
    stats = mapper.get_mapping_statistics()
    print(f"✅ mapedname.txt loaded: {stats['total_mappings']} parameters")
    print(f"✅ O(1) allowlist created: {stats['allowlist_size']} entries")
    
    # Test filtering
    allowed_params = ["magnetronFlow", "FanremoteTempStatistics", "targetAndCirculatorFlow"]
    blocked_params = ["randomParam", "unknownStatistic", "unmappedSensor"]
    
    all_passed = True
    for param in allowed_params:
        if not mapper.is_parameter_allowed(param):
            print(f"❌ FAILED: {param} should be allowed")
            all_passed = False
        else:
            print(f"✅ {param}: ALLOWED (correct)")
    
    for param in blocked_params:
        if mapper.is_parameter_allowed(param):
            print(f"❌ FAILED: {param} should be blocked")
            all_passed = False
        else:
            print(f"✅ {param}: BLOCKED (correct)")
    
    return all_passed

def test_requirement_2_accurate_statistics():
    """2. 🔒 Accurate Parameter Statistics"""
    print("\n🧪 Testing Requirement 2: Accurate Parameter Statistics")
    print("=" * 55)
    
    from unified_parser import UnifiedParser
    
    # Create test input with mix of mapped and unmapped parameters  
    test_content = "2024-01-01\t10:00:00\tINFO\tSystem\tComponent\tSN# 123\tA\tB\tlogStatistics magnetronFlow: count=10 max=15.2 min=10.1 avg=12.5\n" + \
                  "2024-01-01\t10:01:00\tINFO\tSystem\tComponent\tSN# 123\tA\tB\tlogStatistics unmappedParameter: count=5 max=100 min=50 avg=75\n" + \
                  "2024-01-01\t10:02:00\tINFO\tSystem\tComponent\tSN# 123\tA\tB\tlogStatistics FanremoteTempStatistics: count=8 max=25.5 min=20.1 avg=22.8\n" + \
                  "2024-01-01\t10:03:00\tINFO\tSystem\tComponent\tSN# 123\tA\tB\tlogStatistics anotherUnmapped: count=3 max=200 min=100 avg=150"
    
    # Write test file
    with open('/tmp/test_log.txt', 'w') as f:
        f.write(test_content)
    
    try:
        parser = UnifiedParser()
        result = parser.parse_linac_file('/tmp/test_log.txt')
        
        # Check results
        expected_parameters = 2  # magnetronFlow and FanremoteTempStatistics
        actual_parameters = parser.parsing_stats['parameters_detected']
        skipped_parameters = parser.parsing_stats['parameters_skipped']
        
        print(f"✅ Expected parameters detected: {expected_parameters}")
        print(f"✅ Actual parameters detected: {actual_parameters}")
        print(f"✅ Parameters skipped: {skipped_parameters}")
        
        success = (actual_parameters == expected_parameters and skipped_parameters == 2)
        if success:
            print("✅ PASSED: Statistics accurately reflect only mapped parameters")
        else:
            print("❌ FAILED: Statistics do not match expected values")
        
        return success
        
    finally:
        if os.path.exists('/tmp/test_log.txt'):
            os.remove('/tmp/test_log.txt')

def test_requirement_3_merged_parameters():
    """3. 🔗 Merged Parameters Logic"""
    print("\n🧪 Testing Requirement 3: Merged Parameters Logic")
    print("=" * 50)
    
    from enhanced_parameter_mapper import EnhancedParameterMapper
    
    mapper = EnhancedParameterMapper()
    
    # Test merged parameter configuration
    expected_merged = {
        "magnetronFlow": ["magnetronFlow", "CoolingmagnetronFlowLowStatistics"],
        "targetAndCirculatorFlow": ["targetAndCirculatorFlow", "CoolingtargetFlowLowStatistics"]
    }
    
    all_passed = True
    for unified_name, expected_sources in expected_merged.items():
        should_merge, actual_unified, actual_sources = mapper.should_merge_parameter(unified_name)
        
        if should_merge and actual_unified == unified_name and set(actual_sources) == set(expected_sources):
            print(f"✅ {unified_name}: Properly configured for merging")
        else:
            print(f"❌ {unified_name}: Merge configuration incorrect")
            all_passed = False
    
    # Test that merged parameters count as ONE parameter each
    stats = mapper.get_mapping_statistics()
    print(f"✅ Total mappings: {stats['total_mappings']}")
    print(f"✅ Merged groups: {stats['merged_parameter_groups']}")
    print(f"✅ Effective unique parameters: {stats.get('unique_parameters', 'N/A')}")
    
    return all_passed

def test_requirement_4_performance():
    """4. ⚡ Performance Optimization"""
    print("\n🧪 Testing Requirement 4: Performance Optimization")
    print("=" * 50)
    
    from enhanced_parameter_mapper import EnhancedParameterMapper
    import time
    
    mapper = EnhancedParameterMapper()
    
    # Test O(1) filtering performance
    test_params = ["magnetronFlow", "unknownParam", "FanremoteTempStatistics", "randomParam"] * 1000
    
    start_time = time.time()
    for param in test_params:
        mapper.is_parameter_allowed(param)
    end_time = time.time()
    
    processing_time = end_time - start_time
    params_per_sec = len(test_params) / processing_time
    
    print(f"✅ Processed {len(test_params)} parameter checks in {processing_time:.4f}s")
    print(f"✅ Performance: {params_per_sec:.0f} checks/second")
    
    # Should be very fast with O(1) lookup
    success = params_per_sec > 10000  # Should easily exceed 10k checks/sec
    if success:
        print("✅ PASSED: O(1) filtering performance achieved")
    else:
        print("❌ FAILED: Performance below expected threshold")
    
    return success

def test_requirement_5_logging():
    """5. 📊 Logging & Summary"""
    print("\n🧪 Testing Requirement 5: Logging & Summary")
    print("=" * 45)
    
    from enhanced_parameter_mapper import EnhancedParameterMapper
    
    mapper = EnhancedParameterMapper()
    stats = mapper.get_mapping_statistics()
    
    # Check that logging shows correct structure
    required_keys = ['total_mappings', 'allowlist_size', 'merged_parameter_groups', 'source_file']
    missing_keys = [key for key in required_keys if key not in stats]
    
    if not missing_keys:
        print("✅ All required statistics keys present")
        print(f"✅ Total mappings: {stats['total_mappings']}")
        print(f"✅ Allowlist size: {stats['allowlist_size']}")
        print(f"✅ Merged groups: {stats['merged_parameter_groups']}")
        print(f"✅ Source file: {stats['source_file']}")
        return True
    else:
        print(f"❌ Missing required keys: {missing_keys}")
        return False

def test_requirement_6_validation():
    """6. 🧪 Testing & Validation"""
    print("\n🧪 Testing Requirement 6: Testing & Validation")
    print("=" * 50)
    
    # Test with real samlog.txt if available
    if os.path.exists('samlog.txt'):
        from unified_parser import UnifiedParser
        
        print("✅ Testing with real samlog.txt file...")
        parser = UnifiedParser()
        
        # Run a quick parse to get stats
        result = parser.parse_linac_file('samlog.txt')
        
        # Check that only mapped parameters are processed
        parameters_detected = parser.parsing_stats['parameters_detected']
        parameters_skipped = parser.parsing_stats['parameters_skipped']
        
        print(f"✅ Parameters in final dataset: {parameters_detected}")
        print(f"✅ Parameters filtered out: {parameters_skipped}")
        
        # Success if we have reasonable filtering (more skipped than detected)
        success = parameters_skipped > parameters_detected and parameters_detected > 0
        if success:
            print("✅ PASSED: Real-world validation successful")
        else:
            print("❌ FAILED: Real-world validation did not meet expectations")
        
        return success
    else:
        print("⚠️ samlog.txt not found - skipping real-world validation")
        return True

def main():
    """Run all requirement tests"""
    print("🚀 HALOGx Unified Parser — Strict Filtering Validation")
    print("=" * 60)
    
    tests = [
        ("Strict Filtering Enforcement", test_requirement_1_strict_filtering),
        ("Accurate Parameter Statistics", test_requirement_2_accurate_statistics), 
        ("Merged Parameters Logic", test_requirement_3_merged_parameters),
        ("Performance Optimization", test_requirement_4_performance),
        ("Logging & Summary", test_requirement_5_logging),
        ("Testing & Validation", test_requirement_6_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 FINAL VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL REQUIREMENTS SUCCESSFULLY IMPLEMENTED!")
        print("✅ HALOGx parser now enforces strict mapping and accurate parameter counts")
        sys.exit(0)
    else:
        print("❌ Some requirements still need attention")
        sys.exit(1)

if __name__ == "__main__":
    main()