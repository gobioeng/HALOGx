#!/usr/bin/env python3
"""
Simple test script to verify the tab-separated parser works
"""

import sys
import os
sys.path.append('.')

from unified_parser import UnifiedParser
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