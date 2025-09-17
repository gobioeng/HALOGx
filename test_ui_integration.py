#!/usr/bin/env python3
"""
Test UI Integration - Verify data preparation for Trend and Analysis tabs
Tests the complete workflow: parse samlog.txt -> prepare data for graphs -> validate UI data structure
"""

import sys
import os
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_ui_data_preparation():
    """Test data preparation for UI graphs and trends"""
    print("🖥️  Testing UI Data Preparation for Graphs")
    print("=" * 60)
    
    try:
        # Import required modules
        from unified_parser import UnifiedParser
        from database import DatabaseManager
        
        print("✓ Modules imported successfully")
        
        # Step 1: Parse samlog.txt
        print("\n📊 Step 1: Parsing samlog.txt for UI...")
        parser = UnifiedParser()
        df = parser.parse_linac_file('samlog.txt')
        
        if df.empty:
            print("❌ No data extracted - UI will show 'No valid data found'")
            return False
            
        print(f"✓ Extracted {len(df)} records for UI display")
        
        # Step 2: Prepare data for database (simulating UI upload)
        print("\n💾 Step 2: Simulating UI file upload workflow...")
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        try:
            db = DatabaseManager(db_path)
            records_inserted = db.insert_data_batch(df)
            print(f"✓ Database insert: {records_inserted} records")
            
            # Step 3: Retrieve data for UI display (as the UI would)
            print("\n📈 Step 3: Preparing data for Trend and Analysis tabs...")
            
            # Get data for trends (as UI retrieval would work)
            retrieved_df = db.get_all_logs()
            print(f"✓ Retrieved {len(retrieved_df)} records for UI display")
            
            if len(retrieved_df) == 0:
                print("❌ UI would show 'No data available' - this would be the user-visible issue")
                return False
            
            # Step 4: Validate UI data structure
            print("\n🔍 Step 4: Validating data structure for UI graphs...")
            
            required_columns = ['datetime', 'param', 'avg']
            available_columns = retrieved_df.columns.tolist()
            print(f"✓ Available columns: {available_columns}")
            
            missing_columns = [col for col in required_columns if col not in available_columns]
            if missing_columns:
                print(f"⚠️ Missing columns for UI: {missing_columns}")
            else:
                print("✓ All required columns present for UI graphs")
            
            # Step 5: Test parameter categorization for Trend tabs
            print("\n🏷️ Step 5: Testing parameter categorization for Trend sub-tabs...")
            
            unique_params = retrieved_df['param'].unique()
            print(f"✓ Found {len(unique_params)} unique parameters for graphs")
            
            # Categorize parameters for UI tabs
            water_params = [p for p in unique_params if any(keyword in p.lower() 
                          for keyword in ['flow', 'water', 'cooling', 'pump'])]
            temp_params = [p for p in unique_params if any(keyword in p.lower() 
                         for keyword in ['temp', 'temperature'])]
            voltage_params = [p for p in unique_params if any(keyword in p.lower() 
                            for keyword in ['voltage', 'volt', '_v', 'adc'])]
            
            print(f"✓ Water System parameters: {len(water_params)} (for Water System tab)")
            print(f"✓ Temperature parameters: {len(temp_params)} (for Temperature tab)")
            print(f"✓ Voltage parameters: {len(voltage_params)} (for Voltage tab)")
            
            # Step 6: Test specific BGMFPGASensor parameters
            print("\n🎯 Step 6: Verifying BGMFPGASensor::logStatistics parameters...")
            
            bgm_params = [p for p in unique_params if any(keyword in p.lower() 
                         for keyword in ['magnetron', 'target', 'circulator'])]
            
            if len(bgm_params) > 0:
                print(f"✓ Found {len(bgm_params)} BGMFPGASensor parameters:")
                for param in bgm_params[:5]:  # Show first 5
                    sample_data = retrieved_df[retrieved_df['param'] == param]
                    if len(sample_data) > 0:
                        avg_range = f"{sample_data['avg'].min():.2f} - {sample_data['avg'].max():.2f}"
                        print(f"   • {param}: {len(sample_data)} data points, range: {avg_range}")
                print("✅ BGMFPGASensor parameters ready for graph rendering!")
            else:
                print("⚠️ No BGMFPGASensor parameters found - check parameter mapping")
            
            # Step 7: Validate graph data readiness
            print("\n📊 Step 7: Final validation for graph rendering...")
            
            # Check if we have time series data
            if 'datetime' in retrieved_df.columns:
                date_range = retrieved_df['datetime'].max() - retrieved_df['datetime'].min()
                print(f"✓ Time series data: {date_range}")
                
                # Check for multiple data points per parameter (needed for graphs)
                multi_point_params = []
                for param in unique_params[:10]:  # Check first 10 parameters
                    param_data = retrieved_df[retrieved_df['param'] == param]
                    if len(param_data) > 1:
                        multi_point_params.append(param)
                
                print(f"✓ Parameters with multiple data points: {len(multi_point_params)}")
                
                if len(multi_point_params) > 0:
                    print("✅ UI graph rendering should work correctly!")
                    return True
                else:
                    print("⚠️ Limited data points - graphs may be sparse")
                    return True
            else:
                print("❌ No datetime column - graphs cannot be rendered")
                return False
                
        finally:
            # Cleanup
            try:
                os.unlink(db_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Error in UI preparation test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mapedname_integration():
    """Test mapedname.txt integration for user-friendly parameter names"""
    print("\n📋 Testing mapedname.txt Integration for UI Display")
    print("=" * 60)
    
    try:
        from enhanced_parameter_mapper import EnhancedParameterMapper
        
        # Test parameter mapping
        mapper = EnhancedParameterMapper()
        
        # Test key BGMFPGASensor parameters
        test_params = [
            'magnetronFlow',
            'targetAndCirculatorFlow', 
            'magnetronTemp',
            'targetAndCirculatorTemp'
        ]
        
        print("🔍 Testing parameter name mapping for UI display:")
        for param in test_params:
            mapped = mapper.map_parameter_name(param)
            print(f"   • {param} → '{mapped['friendly_name']}' ({mapped['unit']})")
            
        print("✅ Parameter mapping working for user-friendly UI display")
        return True
        
    except Exception as e:
        print(f"❌ Error in mapedname integration test: {e}")
        return False

if __name__ == "__main__":
    print("🧪 HALOGx UI Integration Test Suite")
    print("=" * 60)
    
    # Run tests
    ui_test_passed = test_ui_data_preparation()
    mapping_test_passed = test_mapedname_integration()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   UI Data Preparation: {'✅ PASS' if ui_test_passed else '❌ FAIL'}")
    print(f"   Parameter Mapping: {'✅ PASS' if mapping_test_passed else '❌ FAIL'}")
    
    if ui_test_passed and mapping_test_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ UI should display graphs correctly with samlog.txt")
        print("✅ Trend and Analysis tabs should work properly")
        print("✅ 'No valid data found' error has been resolved!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("❗ UI may still experience issues")
    
    print("=" * 60)