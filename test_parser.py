#!/usr/bin/env python3
"""
Test the unified parser with the samlog.txt file to verify data extraction
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_parser_with_samlog():
    """Test the unified parser with samlog.txt"""
    print("🧪 Testing Unified Parser with samlog.txt")
    print("=" * 50)
    
    try:
        from unified_parser import UnifiedParser
        
        # Initialize parser
        parser = UnifiedParser()
        print("✓ UnifiedParser initialized")
        
        # Parse the samlog.txt file
        samlog_path = "samlog.txt"
        if not os.path.exists(samlog_path):
            print(f"❌ samlog.txt not found at {samlog_path}")
            return False
            
        print(f"📂 Parsing {samlog_path}...")
        df = parser.parse_linac_file(samlog_path)
        
        print(f"📊 Parser Results:")
        print(f"   Records extracted: {len(df)}")
        
        if len(df) > 0:
            print(f"   Columns: {list(df.columns)}")
            print(f"   Date range: {df['datetime'].min()} to {df['datetime'].max()}")
            
            # Show unique parameters extracted
            if 'param' in df.columns:
                params = df['param'].unique()
                print(f"   Unique parameters: {len(params)}")
                print(f"   Sample parameters:")
                for param in params[:10]:
                    count = len(df[df['param'] == param])
                    print(f"     - {param}: {count} records")
                    
                if len(params) > 10:
                    print(f"     ... and {len(params) - 10} more")
            
            # Show sample data
            print(f"\n📋 Sample extracted data:")
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            print(df.head(5).to_string())
            
            return True
        else:
            print("❌ No data extracted from samlog.txt")
            
            # Debug: Check what lines contain statistics
            print("\n🔍 Debugging - checking for statistics patterns...")
            with open(samlog_path, 'r') as f:
                lines = f.readlines()
                
            stats_lines = []
            for i, line in enumerate(lines[:50]):  # Check first 50 lines
                if any(keyword in line.lower() for keyword in ['logstatistics', 'count=', 'avg=', 'max=', 'min=']):
                    stats_lines.append((i+1, line.strip()))
            
            if stats_lines:
                print(f"   Found {len(stats_lines)} lines with statistics in first 50 lines:")
                for line_num, line in stats_lines[:3]:
                    print(f"     Line {line_num}: {line[:100]}...")
            else:
                print("   No statistics patterns found in first 50 lines")
                
            return False
            
    except Exception as e:
        print(f"❌ Error testing parser: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parameter_mapping():
    """Test parameter mapping with mapedname.txt"""
    print("\n🗺️ Testing Parameter Mapping")
    print("=" * 30)
    
    try:
        mapedname_path = "data/mapedname.txt"
        if not os.path.exists(mapedname_path):
            print(f"❌ mapedname.txt not found at {mapedname_path}")
            return False
            
        print(f"📂 Reading {mapedname_path}...")
        with open(mapedname_path, 'r') as f:
            lines = f.readlines()
            
        # Parse mapping file
        mappings = []
        for line in lines[2:]:  # Skip header lines
            line = line.strip()
            if line and '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3 and parts[0] and not parts[0].startswith('-'):
                    mappings.append({
                        'machine_name': parts[0],
                        'friendly_name': parts[1], 
                        'unit': parts[2] if len(parts) > 2 else ''
                    })
        
        print(f"📊 Parameter mappings found: {len(mappings)}")
        print(f"   Sample mappings:")
        for mapping in mappings[:5]:
            print(f"     - {mapping['machine_name']} → {mapping['friendly_name']} ({mapping['unit']})")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing parameter mapping: {e}")
        return False

if __name__ == "__main__":
    print("🚀 HALOGx Parser Testing")
    print("=" * 50)
    
    success1 = test_parser_with_samlog()
    success2 = test_parameter_mapping() 
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Check output above.")
        
    print("=" * 50)
from datetime import datetime

def test_parser():
    """Test the parser with sample lines from the log file"""
    parser = UnifiedParser()
    
    # Test lines from the sample file
    test_lines = [
        # Line with temperature data
        (1, "2025-09-07\t00:05:38\tLocal0\tInfo\t00:05:37:971\tSN# 2182\tCOL\tController\tCMNSubsystemBase::logStatistics cpuTemperatureSensor0: count=7204, max=42.000000, min=42.000000, avg=42.000000"),
        # Line with system mode
        (2, "2025-09-07\t00:02:53\tLocal0\tInfo\t00:02:53:432\tHAL-TRT-SN2182\tVMS\\SYSTEM|4496|LEClinacModelServer.Server\tSystemInfo\tMachineSerialNumber:2182 SystemMode:SERVICE"),
        # Line with EMO event
        (3, "2025-09-07\t00:05:53\tLocal0\tInfo\t00:05:53:082\tSN# 2182\tCOL\tHardwareAPI\tHWAPICommonInterface::printLogEMOGood EMO Good Event Detected!"),
        # Line with odometer
        (4, "2025-09-07\t00:01:36\tLocal0\tInfo\t00:01:36:212\tSN# 2182\tBGM\tController\tCMNDataItem::storeData Odometer data stored under: /ramdisk0/odometerOut.xml"),
    ]
    
    print("Testing tab-separated parser...")
    print("=" * 50)
    
    total_records = 0
    for line_number, line in test_lines:
        print(f"\nTesting line {line_number}: {line[:80]}...")
        
        # Parse the line
        records = parser._parse_tab_separated_line(line, line_number)
        
        print(f"  → Extracted {len(records)} records:")
        for i, record in enumerate(records):
            print(f"    {i+1}. {record['parameter']} = {record['value']} {record['unit']} (SN: {record['serial_number']})")
        
        total_records += len(records)
    
    print(f"\n{'='*50}")
    print(f"TOTAL RECORDS EXTRACTED: {total_records}")
    print(f"Parser test {'✅ PASSED' if total_records > 0 else '❌ FAILED'}")
    
    return total_records > 0

if __name__ == "__main__":
    success = test_parser()
    sys.exit(0 if success else 1)