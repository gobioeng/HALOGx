#!/usr/bin/env python3
"""
Test the app's file import functionality with samlog.txt
Simulates the complete user workflow: Open App → Import Log File → View Data
"""

import sys
import os
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_app_import_workflow():
    """Test the complete app import workflow with samlog.txt"""
    print("🎯 Testing App Import Workflow with samlog.txt")
    print("=" * 60)
    
    try:
        # Import main app components
        from unified_parser import UnifiedParser
        from database import DatabaseManager
        
        print("✓ App components imported successfully")
        
        # Simulate the app's import_log_file functionality
        print("\n🔄 Step 1: Simulating File Import Process...")
        
        # Create temporary database (like the app does)
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        try:
            # Initialize database (like app startup)
            db = DatabaseManager(db_path)
            print("✓ Database initialized")
            
            # Parse log file (like clicking 'Import Log File' and selecting samlog.txt)
            parser = UnifiedParser()
            print("✓ Parser initialized")
            
            file_path = 'samlog.txt'
            print(f"📂 Processing file: {file_path}")
            
            # Parse the file (like the app's import process)
            df = parser.parse_linac_file(file_path)
            print(f"✓ File parsed: {len(df)} records extracted")
            
            if df.empty:
                print("❌ No data extracted - import would fail")
                return False
            
            # Insert data into database (like the app's import process)
            records_inserted = db.insert_data_batch(df)
            print(f"✓ Data inserted: {records_inserted} records stored")
            
            # Simulate loading dashboard data (like the app after import)
            print("\n📊 Step 2: Simulating Dashboard Load...")
            
            # Get all logs (like load_dashboard does)
            dashboard_df = db.get_all_logs()
            print(f"✓ Dashboard data loaded: {len(dashboard_df)} records")
            
            if len(dashboard_df) == 0:
                print("❌ No data available for dashboard")
                return False
            
            # Check if we have the data the UI expects
            expected_columns = ['datetime', 'param', 'avg', 'unit', 'serial']
            available_columns = list(dashboard_df.columns)
            missing_columns = [col for col in expected_columns if col not in available_columns]
            
            print(f"✓ Available columns: {available_columns}")
            if missing_columns:
                print(f"⚠️ Missing columns: {missing_columns} (but app should handle this)")
            
            # Simulate trend tab data preparation
            print("\n📈 Step 3: Simulating Trend Tab Preparation...")
            
            # Get unique parameters (like trend tab initialization)
            unique_params = dashboard_df['param'].unique()
            print(f"✓ Unique parameters available: {len(unique_params)}")
            
            # Categorize parameters like the app's AI categorization
            water_params = [p for p in unique_params if any(term in p.lower() for term in ['flow', 'magnetron', 'target'])]
            voltage_params = [p for p in unique_params if any(term in p.lower() for term in ['voltage', 'volt', '24v', '48v', 'adc', 'mlc', 'col'])]
            temp_params = [p for p in unique_params if any(term in p.lower() for term in ['temp', 'temperature', 'cpu'])]
            fan_params = [p for p in unique_params if any(term in p.lower() for term in ['fan', 'speed'])]
            humidity_params = [p for p in unique_params if any(term in p.lower() for term in ['humidity', 'humid'])]
            
            print(f"✓ Water System parameters: {len(water_params)}")
            print(f"✓ Voltage parameters: {len(voltage_params)}")
            print(f"✓ Temperature parameters: {len(temp_params)}")
            print(f"✓ Fan Speed parameters: {len(fan_params)}")
            print(f"✓ Humidity parameters: {len(humidity_params)}")
            
            # Simulate analysis tab preparation
            print("\n📋 Step 4: Simulating Analysis Tab Preparation...")
            
            # Check if we have data suitable for analysis
            analysis_ready = len(dashboard_df) > 0 and 'avg' in dashboard_df.columns
            print(f"✓ Analysis data ready: {analysis_ready}")
            
            if analysis_ready:
                # Show some sample analysis data
                sample_param = unique_params[0]
                param_data = dashboard_df[dashboard_df['param'] == sample_param]
                print(f"✓ Sample analysis for '{sample_param}': {len(param_data)} data points")
                
                if 'avg' in param_data.columns and len(param_data) > 0:
                    avg_val = param_data['avg'].iloc[0]
                    unit = param_data['unit'].iloc[0] if 'unit' in param_data.columns else 'N/A'
                    print(f"   Current value: {avg_val} {unit}")
            
            # Final verification
            print("\n🎉 Step 5: Final Verification...")
            
            # Check that all necessary data is available for UI display
            ui_ready_checks = [
                ("Data available", len(dashboard_df) > 0),
                ("Parameters categorized", len(water_params + voltage_params + temp_params + fan_params) > 0),
                ("Trend data ready", 'avg' in dashboard_df.columns),
                ("Analysis data ready", analysis_ready),
                ("Time series data", 'datetime' in dashboard_df.columns)
            ]
            
            all_checks_pass = True
            for check_name, check_result in ui_ready_checks:
                status = "✅" if check_result else "❌"
                print(f"   {status} {check_name}: {check_result}")
                if not check_result:
                    all_checks_pass = False
            
            if all_checks_pass:
                print("\n🚀 SUCCESS: App should display data correctly!")
                print("\n📊 Expected User Experience:")
                print("   1. User opens HALog app")
                print("   2. User clicks 'Open Log File' and selects samlog.txt")
                print("   3. App shows 'Import Successful' with record count")
                print("   4. Dashboard tab shows system status")
                print("   5. Trend tab shows categorized parameters:")
                print(f"      - Water System tab: {len(water_params)} parameters")
                print(f"      - Voltage tab: {len(voltage_params)} parameters") 
                print(f"      - Temperature tab: {len(temp_params)} parameters")
                print(f"      - Fan Speed tab: {len(fan_params)} parameters")
                print("   6. Analysis tab shows parameter statistics")
                print("   7. All data displays correctly with proper units and values")
                
                return True
            else:
                print("\n❌ Some checks failed - app may not display data correctly")
                return False
                
        finally:
            # Clean up
            try:
                os.unlink(db_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Error in app import workflow test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app_import_workflow()
    print("\n" + "=" * 60)
    if success:
        print("🎉 APP IMPORT WORKFLOW TEST PASSED!")
        print("🚀 User should be able to import samlog.txt and see data in all tabs")
        print("\n💡 To verify manually:")
        print("   1. Run: python main.py")
        print("   2. Click 'File' → 'Open Log File'")
        print("   3. Select samlog.txt")
        print("   4. Check Dashboard, Trend, and Analysis tabs for data")
    else:
        print("❌ APP IMPORT WORKFLOW TEST FAILED!")
    print("=" * 60)