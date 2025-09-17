#!/usr/bin/env python3
"""
Test strict parameter filtering in HALOGx unified parser.
Validates that only parameters from mapedname.txt are processed.
"""

import os
import sys
sys.path.append('.')

def test_enhanced_mapper_counts():
    """Test that enhanced mapper loads correct parameter counts"""
    from enhanced_parameter_mapper import EnhancedParameterMapper
    
    print("🧪 Testing Enhanced Parameter Mapper Counts")
    print("=" * 50)
    
    mapper = EnhancedParameterMapper()
    stats = mapper.get_mapping_statistics()
    
    print(f"✅ Total mappings loaded: {stats['total_mappings']}")
    print(f"🔒 Parameter allowlist size: {stats['allowlist_size']}")
    print(f"🔗 Merged parameter groups: {stats['merged_parameter_groups']}")
    print(f"📊 Unique parameters (accounting for merges): {stats.get('unique_parameters', 'N/A')}")
    
    # Verify expected counts
    expected_mappings = 35  # 36 lines minus 1 header
    assert stats['total_mappings'] == expected_mappings, f"Expected {expected_mappings} mappings, got {stats['total_mappings']}"
    
    # Check merged parameters
    expected_merged_groups = 2  # magnetronFlow and targetAndCirculatorFlow
    assert stats['merged_parameter_groups'] == expected_merged_groups, f"Expected {expected_merged_groups} merged groups, got {stats['merged_parameter_groups']}"
    
    print("✅ All mapper count tests passed!")
    return True

def test_parameter_filtering():
    """Test that parameter filtering works correctly"""
    from enhanced_parameter_mapper import EnhancedParameterMapper
    
    print("\n🧪 Testing Parameter Filtering")
    print("=" * 30)
    
    mapper = EnhancedParameterMapper()
    
    # Test cases: (parameter_name, should_be_allowed)
    test_cases = [
        ("magnetronFlow", True),
        ("targetAndCirculatorFlow", True), 
        ("CoolingmagnetronFlowLowStatistics", True),  # Should be allowed because it's in merged params
        ("CoolingtargetFlowLowStatistics", True),     # Should be allowed because it's in merged params
        ("FanremoteTempStatistics", True),
        ("randomUnmappedParameter", False),
        ("anotherInvalidParam", False),
        ("unknownStatistic", False)
    ]
    
    all_passed = True
    for param, expected in test_cases:
        result = mapper.is_parameter_allowed(param)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {param}: {'ALLOWED' if result else 'FILTERED'} (expected: {'ALLOWED' if expected else 'FILTERED'})")
        if result != expected:
            all_passed = False
    
    if all_passed:
        print("✅ All filtering tests passed!")
    else:
        print("❌ Some filtering tests failed!")
    
    return all_passed

def test_merging_logic():
    """Test parameter merging logic"""
    from enhanced_parameter_mapper import EnhancedParameterMapper
    
    print("\n🧪 Testing Parameter Merging Logic")
    print("=" * 35)
    
    mapper = EnhancedParameterMapper()
    
    # Test merged parameters
    test_cases = [
        ("magnetronFlow", True, "magnetronFlow"),
        ("CoolingmagnetronFlowLowStatistics", True, "magnetronFlow"),
        ("targetAndCirculatorFlow", True, "targetAndCirculatorFlow"),
        ("CoolingtargetFlowLowStatistics", True, "targetAndCirculatorFlow"),
        ("FanremoteTempStatistics", False, "FanremoteTempStatistics")
    ]
    
    all_passed = True
    for param, should_merge, expected_unified in test_cases:
        should_merge_result, unified_name, sources = mapper.should_merge_parameter(param)
        status = "✅" if should_merge_result == should_merge and unified_name == expected_unified else "❌"
        print(f"  {status} {param}: {'MERGE' if should_merge_result else 'NO MERGE'} → {unified_name}")
        if should_merge_result != should_merge or unified_name != expected_unified:
            all_passed = False
    
    if all_passed:
        print("✅ All merging tests passed!")
    else:
        print("❌ Some merging tests failed!")
    
    return all_passed

if __name__ == "__main__":
    print("🚀 HALOGx Strict Filtering Test Suite")
    print("=" * 45)
    
    try:
        mapper_test = test_enhanced_mapper_counts()
        filter_test = test_parameter_filtering() 
        merge_test = test_merging_logic()
        
        if mapper_test and filter_test and merge_test:
            print("\n🎉 ALL TESTS PASSED! Strict filtering is working correctly.")
            print(f"📊 Summary: Only {35} parameters from mapedname.txt will be processed")
            print(f"🔗 {2} merged parameter groups configured")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED! Check the implementation.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)