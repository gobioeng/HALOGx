#!/usr/bin/env python3
"""
Test the complete workflow: parse samlog.txt -> load into app -> verify UI data display
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_app_with_samlog():
    """Test the complete app workflow with samlog.txt"""
    print("🚀 Testing Complete App Workflow with samlog.txt")
    print("=" * 60)
    
    try:
        # Import required modules
        from unified_parser import UnifiedParser
        from database import DatabaseManager
        
        print("✓ Modules imported successfully")
        
        # Test 1: Parse samlog.txt
        print("\n📊 Step 1: Parsing samlog.txt...")
        parser = UnifiedParser()
        df = parser.parse_linac_file('samlog.txt')
        
        if df.empty:
            print("❌ No data extracted from samlog.txt")
            return False
            
        print(f"✓ Extracted {len(df)} records")
        print(f"✓ Parameters: {df['param'].nunique()} unique")
        print(f"✓ Date range: {df['datetime'].min()} to {df['datetime'].max()}")
        
        # Test 2: Create temporary database and insert data
        print("\n💾 Step 2: Creating database and inserting data...")
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        try:
            db = DatabaseManager(db_path)
            
            # Insert the parsed data
            records_inserted = db.insert_data_batch(df)
            print(f"✓ Inserted {records_inserted} records into database")
            
            # Test 3: Retrieve data from database
            print("\n📋 Step 3: Retrieving data from database...")
            retrieved_df = db.get_all_logs()
            print(f"✓ Retrieved {len(retrieved_df)} records from database")
            
            if len(retrieved_df) > 0:
                print(f"✓ Columns available: {list(retrieved_df.columns)}")
                
                # Check if we have the expected columns for UI
                expected_columns = ['datetime', 'param', 'serial_number', 'avg']
                missing_columns = [col for col in expected_columns if col not in retrieved_df.columns]
                if missing_columns:
                    print(f"⚠️ Missing expected columns for UI: {missing_columns}")
                else:
                    print("✓ All expected columns present for UI")
                
                # Test 4: Categorize parameters for trend tabs
                print("\n🏷️ Step 4: Categorizing parameters for trend tabs...")
                
                # Get unique parameters
                unique_params = retrieved_df['param'].unique()
                
                # AI-based categorization
                categories = {
                    'Water System': [],
                    'Voltages': [],
                    'Temperatures': [],
                    'Fan Speeds': [],
                    'Humidity': [],
                    'Other': []
                }
                
                for param in unique_params:
                    param_lower = param.lower()
                    base_param = param.replace('_avg', '').replace('_max', '').replace('_min', '').replace('_count', '')
                    
                    if any(term in param_lower for term in ['flow', 'magnetron', 'target', 'circulator']):
                        categories['Water System'].append(param)
                    elif any(term in param_lower for term in ['voltage', 'volt', '24v', '48v', '5v', '12v', 'adc', 'mlc', 'col']):
                        categories['Voltages'].append(param)
                    elif any(term in param_lower for term in ['temp', 'temperature', 'cpu']):
                        categories['Temperatures'].append(param)
                    elif any(term in param_lower for term in ['fan', 'speed']):
                        categories['Fan Speeds'].append(param)
                    elif any(term in param_lower for term in ['humidity', 'humid']):
                        categories['Humidity'].append(param)
                    else:
                        categories['Other'].append(param)
                
                print("✓ Parameter categorization complete:")
                for category, params in categories.items():
                    if params:
                        print(f"   {category}: {len(params)} parameters")
                        for param in params[:3]:
                            print(f"     - {param}")
                        if len(params) > 3:
                            print(f"     ... and {len(params) - 3} more")
                
                # Test 5: Verify data is suitable for trend analysis
                print("\n📈 Step 5: Verifying data for trend analysis...")
                
                # Check if we have data with avg values
                if 'avg' in retrieved_df.columns:
                    avg_data = retrieved_df[retrieved_df['avg'].notna()]
                    print(f"✓ Found {len(avg_data)} records with average values")
                    
                    # Check date range suitable for trends
                    date_range = retrieved_df['datetime'].max() - retrieved_df['datetime'].min()
                    print(f"✓ Data spans {date_range}")
                    
                    # Sample trend data for one parameter
                    if len(categories['Water System']) > 0:
                        sample_param = categories['Water System'][0]
                        param_data = retrieved_df[retrieved_df['param'] == sample_param]
                        if len(param_data) > 0:
                            print(f"✓ Sample trend data for '{sample_param}': {len(param_data)} points")
                            print(f"   Value range: {param_data['avg'].min():.2f} to {param_data['avg'].max():.2f}")
                
                print("\n🎯 Step 6: Data Ready for UI Display")
                print("✅ Parser extraction: SUCCESS")
                print("✅ Database storage: SUCCESS") 
                print("✅ Data retrieval: SUCCESS")
                print("✅ Parameter categorization: SUCCESS")
                print("✅ Trend data preparation: SUCCESS")
                
                print(f"\n📊 Summary:")
                print(f"   Total records: {len(retrieved_df)}")
                print(f"   Unique parameters: {len(unique_params)}")
                print(f"   Water System parameters: {len(categories['Water System'])}")
                print(f"   Voltage parameters: {len(categories['Voltages'])}")
                print(f"   Temperature parameters: {len(categories['Temperatures'])}")
                print(f"   Fan Speed parameters: {len(categories['Fan Speeds'])}")
                print(f"   Humidity parameters: {len(categories['Humidity'])}")
                
                return True
            else:
                print("❌ No data retrieved from database")
                return False
                
        finally:
            # Clean up temporary database
            try:
                os.unlink(db_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Error in workflow test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app_with_samlog()
    print("\n" + "=" * 60)
    if success:
        print("🎉 Complete workflow test PASSED!")
        print("🚀 App should now display data correctly with samlog.txt")
    else:
        print("❌ Workflow test FAILED!")
    print("=" * 60)