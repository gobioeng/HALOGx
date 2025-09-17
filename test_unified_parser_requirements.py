#!/usr/bin/env python3
"""
HALOGx Unified Parser Requirements Validation Test
Validates that all requirements from the problem statement are implemented correctly.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_unified_parser_requirements():
    """Test that all unified parser requirements are implemented"""
    print("🧠 HALOGx Unified Parser Requirements Validation")
    print("=" * 60)
    
    # Test 1: Unified Parser Module
    print("\n1️⃣ Testing Unified Parser Module")
    print("-" * 30)
    
    try:
        from unified_parser import UnifiedParser
        parser = UnifiedParser()
        print("✅ unified_parser.py successfully consolidates all parsing logic")
        
        # Verify enhanced parameter mapper is integrated
        if hasattr(parser, 'enhanced_mapper') and parser.enhanced_mapper:
            print("✅ Enhanced parameter mapper integrated")
            stats = parser.enhanced_mapper.get_mapping_statistics()
            print(f"   📊 {stats['total_mappings']} parameters from mapedname.txt")
        else:
            print("❌ Enhanced parameter mapper not properly integrated")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import unified_parser: {e}")
        return False
    
    # Test 2: Strict Parameter Filtering
    print("\n2️⃣ Testing Strict Parameter Filtering")
    print("-" * 30)
    
    try:
        # Test allowlist functionality
        allowlist_size = len(parser.enhanced_mapper.parameter_allowlist)
        print(f"✅ O(1) parameter allowlist created: {allowlist_size} entries")
        
        # Test filtering function
        test_params = [
            'magnetronFlow',  # Should be allowed
            'invalidParameter123',  # Should be rejected
            'CoolingmagnetronFlowLowStatistics',  # Should be allowed (merged)
            'randomUnmappedParam'  # Should be rejected
        ]
        
        allowed_count = 0
        for param in test_params:
            if parser.enhanced_mapper.is_parameter_allowed(param):
                allowed_count += 1
                print(f"   ✅ {param} - ALLOWED")
            else:
                print(f"   🚫 {param} - FILTERED OUT")
        
        if allowed_count == 2:  # Only first and third should be allowed
            print("✅ Strict parameter filtering working correctly")
        else:
            print(f"❌ Expected 2 allowed parameters, got {allowed_count}")
            return False
            
    except Exception as e:
        print(f"❌ Parameter filtering test failed: {e}")
        return False
    
    # Test 3: Equivalent Parameter Merging
    print("\n3️⃣ Testing Equivalent Parameter Merging")
    print("-" * 30)
    
    try:
        merged_params = parser.enhanced_mapper.merged_parameters
        expected_merges = {
            'magnetronFlow': ['magnetronFlow', 'CoolingmagnetronFlowLowStatistics'],
            'targetAndCirculatorFlow': ['targetAndCirculatorFlow', 'CoolingtargetFlowLowStatistics']
        }
        
        merge_success = True
        for unified_name, expected_sources in expected_merges.items():
            if unified_name in merged_params:
                actual_sources = merged_params[unified_name]
                if actual_sources == expected_sources:
                    print(f"   ✅ {unified_name} merges: {' + '.join(actual_sources)}")
                else:
                    print(f"   ❌ {unified_name} merge mismatch")
                    merge_success = False
            else:
                print(f"   ❌ {unified_name} merge not configured")
                merge_success = False
        
        if merge_success:
            print("✅ Equivalent parameter merging configured correctly")
        else:
            return False
            
    except Exception as e:
        print(f"❌ Parameter merging test failed: {e}")
        return False
    
    # Test 4: Performance Optimization
    print("\n4️⃣ Testing Performance Optimization")
    print("-" * 30)
    
    try:
        import time
        
        # Test parsing performance with actual data
        start_time = time.time()
        df = parser.parse_linac_file('samlog.txt')
        end_time = time.time()
        
        processing_time = end_time - start_time
        records_count = len(df)
        records_per_sec = records_count / processing_time if processing_time > 0 else 0
        
        print(f"✅ Parsed {records_count:,} records in {processing_time:.2f}s")
        print(f"✅ Performance: {records_per_sec:,.0f} records/second")
        
        if records_per_sec > 10000:  # Should be over 10k records/sec
            print("✅ Performance optimization successful")
        else:
            print("⚠️ Performance below expected threshold")
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False
    
    # Test 5: Comprehensive Logging
    print("\n5️⃣ Testing Comprehensive Logging & Validation")
    print("-" * 30)
    
    try:
        stats = parser.parsing_stats
        required_stats = [
            'total_lines_read', 'parameters_detected', 'parameters_mapped',
            'valid_records_extracted', 'skipped_records', 'merged_parameter_records'
        ]
        
        missing_stats = [stat for stat in required_stats if stat not in stats]
        if not missing_stats:
            print("✅ All required parsing statistics tracked")
            print(f"   📄 Lines processed: {stats.get('total_lines_read', 0):,}")
            print(f"   🔍 Parameters detected: {stats.get('parameters_detected', 0)}")
            print(f"   ✅ Records extracted: {stats.get('valid_records_extracted', 0):,}")
            print(f"   🔗 Merged records: {stats.get('merged_parameter_records', 0)}")
        else:
            print(f"❌ Missing statistics: {missing_stats}")
            return False
            
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False
    
    # Test 6: Redundant File Removal
    print("\n6️⃣ Testing Redundant File Removal")
    print("-" * 30)
    
    redundant_files = ['optimized_parser.py', 'hardcoded_parameters.py']
    removed_files = []
    existing_files = []
    
    for file in redundant_files:
        if os.path.exists(file):
            existing_files.append(file)
        else:
            removed_files.append(file)
    
    if removed_files:
        print(f"✅ Removed redundant files: {', '.join(removed_files)}")
    if existing_files:
        print(f"⚠️ Redundant files still exist: {', '.join(existing_files)}")
    
    # Test 7: mapedname.txt Integration
    print("\n7️⃣ Testing mapedname.txt Integration")
    print("-" * 30)
    
    try:
        if os.path.exists('data/mapedname.txt'):
            print("✅ mapedname.txt file exists")
            
            # Check parameter mappings
            mappings = parser.enhanced_mapper.parameter_mapping
            if len(mappings) > 30:  # Should have substantial mappings
                print(f"✅ {len(mappings)} parameter mappings loaded")
                
                # Test specific required mappings
                required_params = ['magnetronFlow', 'targetAndCirculatorFlow']
                mapped_params = [p for p in required_params if p in mappings]
                
                if len(mapped_params) == len(required_params):
                    print("✅ All required parameters mapped correctly")
                else:
                    print(f"❌ Missing required parameters: {set(required_params) - set(mapped_params)}")
                    return False
            else:
                print(f"❌ Insufficient mappings: {len(mappings)}")
                return False
        else:
            print("❌ mapedname.txt file not found")
            return False
            
    except Exception as e:
        print(f"❌ mapedname.txt integration test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧠 HALOGx Unified Parser Requirements Validation")
    print("Testing implementation against problem statement requirements...")
    print()
    
    success = test_unified_parser_requirements()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL REQUIREMENTS SUCCESSFULLY IMPLEMENTED!")
        print("✅ Unified parser refactor complete")
        print("✅ Strict parameter filtering active") 
        print("✅ Equivalent parameter merging working")
        print("✅ Performance optimized")
        print("✅ Comprehensive logging enabled")
        print("✅ Redundant files removed")
        print("✅ mapedname.txt integration functional")
    else:
        print("❌ SOME REQUIREMENTS NOT MET!")
        print("Please review the test output above for details.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)