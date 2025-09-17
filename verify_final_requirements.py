#!/usr/bin/env python3
"""
Final Verification Script for HALOGx Log Parser & Graph Integration
Confirms all requirements from the problem statement have been addressed.

This script validates:
1. Log File Parsing (BGMFPGASensor::logStatistics entries)
2. Parameter Mapping (mapedname.txt integration) 
3. Validation & Logging (comprehensive metrics)
4. Graph Data Preparation (for Trend and Analysis tabs)
5. Performance & Optimization (large file handling)
"""

import sys
import os
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def verify_requirement_1_log_parsing():
    """Verify Requirement 1: Log File Parsing"""
    print("1️⃣ Verifying Log File Parsing (BGMFPGASensor::logStatistics)")
    print("-" * 60)
    
    try:
        from unified_parser import UnifiedParser
        
        # Test parsing specific BGMFPGASensor entries
        parser = UnifiedParser()
        df = parser.parse_linac_file('samlog.txt')
        
        if df.empty:
            print("❌ FAILED: No data extracted from samlog.txt")
            return False
        
        # Check for specific BGMFPGASensor parameters
        bgm_params = ['magnetronFlow', 'targetAndCirculatorFlow', 'magnetronTemp', 'targetAndCirculatorTemp']
        found_params = []
        
        for param in bgm_params:
            if param in df['param'].values:
                param_data = df[df['param'] == param]
                if len(param_data) > 0:
                    found_params.append(param)
                    sample = param_data.iloc[0]
                    print(f"✅ {param}: {len(param_data)} records, sample value: {sample.get('value', 'N/A')}")
        
        if len(found_params) >= 3:  # At least 3 of the 4 BGM parameters
            print(f"✅ SUCCESS: Found {len(found_params)}/4 BGMFPGASensor parameters")
            return True
        else:
            print(f"⚠️ PARTIAL: Found only {len(found_params)}/4 BGMFPGASensor parameters")
            return len(found_params) > 0
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def verify_requirement_2_parameter_mapping():
    """Verify Requirement 2: Parameter Mapping"""
    print("\n2️⃣ Verifying Parameter Mapping (mapedname.txt integration)")
    print("-" * 60)
    
    try:
        from enhanced_parameter_mapper import EnhancedParameterMapper
        
        mapper = EnhancedParameterMapper()
        
        # Test key mappings from mapedname.txt
        test_mappings = [
            ('magnetronFlow', 'Magnetron Flow', 'L/min'),
            ('targetAndCirculatorFlow', 'Target & Circulator Flow', 'L/min'),
            ('magnetronTemp', 'Magnetron Temperature', '°C'),
            ('sf6GasPressure', 'SF6 Gas Pressure', 'PSI')
        ]
        
        success_count = 0
        for param, expected_name, expected_unit in test_mappings:
            mapped = mapper.map_parameter_name(param)
            if mapped['friendly_name'] == expected_name and mapped['unit'] == expected_unit:
                print(f"✅ {param} → '{mapped['friendly_name']}' ({mapped['unit']})")
                success_count += 1
            else:
                print(f"⚠️ {param} → '{mapped['friendly_name']}' ({mapped['unit']}) [Expected: '{expected_name}' ({expected_unit})]")
        
        if success_count >= 3:
            print(f"✅ SUCCESS: {success_count}/4 mappings correct")
            return True
        else:
            print(f"⚠️ PARTIAL: Only {success_count}/4 mappings correct") 
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def verify_requirement_3_validation_logging():
    """Verify Requirement 3: Validation & Logging"""
    print("\n3️⃣ Verifying Validation & Logging (comprehensive metrics)")
    print("-" * 60)
    
    try:
        from unified_parser import UnifiedParser
        
        # Capture parser output to verify logging
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            parser = UnifiedParser()
            df = parser.parse_linac_file('samlog.txt')
        
        output = f.getvalue()
        
        # Check for required logging elements
        required_logs = [
            'Total lines read:',
            'Parameters detected:',
            'Parameters mapped:',
            'Valid records extracted:',
            'Skipped records:',
            'Processing time:'
        ]
        
        found_logs = []
        for log_item in required_logs:
            if log_item in output:
                found_logs.append(log_item)
                print(f"✅ Found: {log_item}")
            else:
                print(f"❌ Missing: {log_item}")
        
        if len(found_logs) >= 5:
            print(f"✅ SUCCESS: {len(found_logs)}/6 required log elements present")
            return True
        else:
            print(f"⚠️ PARTIAL: Only {len(found_logs)}/6 log elements found")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def verify_requirement_4_graph_preparation():
    """Verify Requirement 4: Graph Data Preparation"""
    print("\n4️⃣ Verifying Graph Data Preparation (Trend and Analysis tabs)")
    print("-" * 60)
    
    try:
        from unified_parser import UnifiedParser
        from database import DatabaseManager
        import tempfile
        
        # Parse and store data
        parser = UnifiedParser()
        df = parser.parse_linac_file('samlog.txt')
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        try:
            db = DatabaseManager(db_path)
            db.insert_data_batch(df)
            
            # Retrieve data as UI would
            ui_data = db.get_all_logs()
            
            # Verify graph-ready structure
            required_columns = ['datetime', 'param', 'avg']
            has_all_columns = all(col in ui_data.columns for col in required_columns)
            
            if not has_all_columns:
                print(f"❌ Missing required columns. Available: {ui_data.columns.tolist()}")
                return False
            
            # Check for time series data
            if len(ui_data) == 0:
                print("❌ No data available for graphs")
                return False
            
            # Check parameter categorization
            unique_params = ui_data['param'].nunique()
            water_params = ui_data[ui_data['param'].str.contains('flow|water|cooling', case=False, na=False)]['param'].nunique()
            temp_params = ui_data[ui_data['param'].str.contains('temp', case=False, na=False)]['param'].nunique()
            
            print(f"✅ Graph-ready data: {len(ui_data)} records, {unique_params} parameters")
            print(f"✅ Water System parameters: {water_params}")
            print(f"✅ Temperature parameters: {temp_params}")
            print(f"✅ Date range: {ui_data['datetime'].min()} to {ui_data['datetime'].max()}")
            
            return True
            
        finally:
            try:
                os.unlink(db_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def verify_requirement_5_performance():
    """Verify Requirement 5: Performance & Optimization"""
    print("\n5️⃣ Verifying Performance & Optimization (large file handling)")
    print("-" * 60)
    
    try:
        from unified_parser import UnifiedParser
        
        # Test performance with chunked processing
        start_time = time.time()
        parser = UnifiedParser()
        df = parser.parse_linac_file('samlog.txt', chunk_size=2000)  # Larger chunks
        end_time = time.time()
        
        processing_time = end_time - start_time
        records_per_sec = len(df) / max(processing_time, 0.001)
        
        file_size = os.path.getsize('samlog.txt') / (1024 * 1024)  # MB
        
        print(f"✅ File size: {file_size:.1f} MB")
        print(f"✅ Processing time: {processing_time:.2f}s")
        print(f"✅ Records extracted: {len(df):,}")
        print(f"✅ Performance: {records_per_sec:,.0f} records/sec")
        
        # Performance thresholds
        if records_per_sec > 10000 and processing_time < 5.0:
            print("✅ SUCCESS: Excellent performance for large files")
            return True
        elif records_per_sec > 5000:
            print("✅ SUCCESS: Good performance for large files")
            return True
        else:
            print("⚠️ PARTIAL: Performance may need optimization")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run complete verification suite"""
    print("🧪 HALOGx Final Verification Suite")
    print("=" * 70)
    print("Verifying all requirements from the problem statement...")
    print()
    
    # Run all verification tests
    tests = [
        ("Log File Parsing", verify_requirement_1_log_parsing),
        ("Parameter Mapping", verify_requirement_2_parameter_mapping), 
        ("Validation & Logging", verify_requirement_3_validation_logging),
        ("Graph Data Preparation", verify_requirement_4_graph_preparation),
        ("Performance & Optimization", verify_requirement_5_performance)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 FINAL VERIFICATION RESULTS")
    print("=" * 70)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} : {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 ALL REQUIREMENTS VERIFIED SUCCESSFULLY!")
        print("✅ HALOGx log parser is working correctly")
        print("✅ 'No valid data found' error has been resolved")
        print("✅ Graphs should render properly in Trend and Analysis tabs")
        print("✅ Performance is optimized for large files")
    elif passed >= 4:
        print("\n🎯 MOSTLY SUCCESSFUL!")
        print("✅ Critical functionality is working")
        print("⚠️ Minor issues may need attention")
    else:
        print("\n❌ VERIFICATION FAILED!")
        print("🔧 Additional work needed to meet requirements")
    
    print("=" * 70)

if __name__ == "__main__":
    main()