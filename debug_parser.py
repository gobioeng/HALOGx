#!/usr/bin/env python3
"""
Debug the tab-separated parsing to see why it's not working
"""

import sys
import os
sys.path.append('.')

from unified_parser import UnifiedParser

def debug_tab_parsing():
    """Debug tab-separated parsing"""
    print("🔍 Debugging Tab-Separated Parsing")
    print("=" * 50)
    
    # Read a few lines from samlog.txt
    with open('samlog.txt', 'r') as f:
        lines = f.readlines()
    
    print(f"📂 Total lines in samlog.txt: {len(lines)}")
    
    parser = UnifiedParser()
    
    for i, line in enumerate(lines[:5]):
        print(f"\n📋 Line {i+1}:")
        print(f"   Raw: {repr(line[:100])}...")
        print(f"   Tab count: {line.count('\t')}")
        print(f"   Tab detected: {'\t' in line and line.count('\t') >= 7}")
        
        if '\t' in line:
            parts = line.split('\t')
            print(f"   Parts count: {len(parts)}")
            if len(parts) >= 9:
                print(f"   Date: {repr(parts[0])}")
                print(f"   Time: {repr(parts[1])}")
                print(f"   SN Field: {repr(parts[5])}")
                print(f"   System: {repr(parts[6])}")
                print(f"   Component: {repr(parts[7])}")
                print(f"   Message: {repr(parts[8][:50])}...")
                
                # Check if message contains logStatistics
                message = parts[8]
                has_log_stats = 'logStatistics' in message
                has_count = 'count=' in message
                print(f"   Has logStatistics: {has_log_stats}")
                print(f"   Has count=: {has_count}")
                
                if has_log_stats and has_count:
                    # Try to extract records
                    records = parser._parse_tab_separated_line(line, i+1)
                    print(f"   Records extracted: {len(records)}")
                    if records:
                        for j, record in enumerate(records):
                            print(f"     Record {j+1}: {record}")
        else:
            print("   No tabs found in line")

if __name__ == "__main__":
    debug_tab_parsing()