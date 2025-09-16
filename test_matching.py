#!/usr/bin/env python3
"""
Test if the extracted parameters match the mapedname.txt mappings
"""

import sys
import os
import pandas as pd
sys.path.append('.')

from unified_parser import UnifiedParser

def test_parameter_matching():
    """Test if extracted parameters match mapedname.txt mappings"""
    print("🔍 Testing Parameter Matching")
    print("=" * 50)
    
    # Parse samlog.txt
    parser = UnifiedParser()
    df = parser.parse_linac_file('samlog.txt')
    
    if df.empty:
        print("❌ No data extracted")
        return
    
    print(f"📊 Extracted {len(df)} records with {df['param'].nunique()} unique parameters")
    
    # Get unique parameters from parsed data
    extracted_params = df['param'].unique()
    
    # Load mapedname.txt mappings
    mapedname_path = "data/mapedname.txt"
    mappings = {}
    with open(mapedname_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines[2:]:  # Skip header lines
        line = line.strip()
        if line and '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3 and parts[0] and not parts[0].startswith('-'):
                mappings[parts[0]] = {
                    'friendly_name': parts[1],
                    'unit': parts[2]
                }
    
    print(f"📋 Loaded {len(mappings)} parameter mappings")
    
    # Check matches
    print(f"\n🔍 Checking parameter matches:")
    
    matches = []
    partial_matches = []
    no_matches = []
    
    for param in extracted_params:
        # Remove suffixes like _avg, _max, _min, _count
        base_param = param.replace('_avg', '').replace('_max', '').replace('_min', '').replace('_count', '')
        
        # Check exact match
        if base_param in mappings:
            matches.append((param, base_param, mappings[base_param]))
        else:
            # Check partial matches
            partial_match = None
            for mapped_param in mappings:
                if mapped_param.lower() in base_param.lower() or base_param.lower() in mapped_param.lower():
                    partial_match = (mapped_param, mappings[mapped_param])
                    break
            
            if partial_match:
                partial_matches.append((param, partial_match[0], partial_match[1]))
            else:
                no_matches.append(param)
    
    print(f"✅ Exact matches: {len(matches)}")
    for param, mapped, config in matches[:5]:
        print(f"   {param} → {config['friendly_name']} ({config['unit']})")
    if len(matches) > 5:
        print(f"   ... and {len(matches) - 5} more")
    
    print(f"\n🔍 Partial matches: {len(partial_matches)}")
    for param, mapped, config in partial_matches[:5]:
        print(f"   {param} ≈ {mapped} → {config['friendly_name']} ({config['unit']})")
    if len(partial_matches) > 5:
        print(f"   ... and {len(partial_matches) - 5} more")
    
    print(f"\n❌ No matches: {len(no_matches)}")
    for param in no_matches[:5]:
        print(f"   {param}")
    if len(no_matches) > 5:
        print(f"   ... and {len(no_matches) - 5} more")
    
    # Suggest adding missing parameters to mapedname.txt
    if no_matches:
        print(f"\n💡 Suggested additions to mapedname.txt:")
        for param in no_matches[:10]:
            base_param = param.replace('_avg', '').replace('_max', '').replace('_min', '').replace('_count', '')
            
            # AI-based categorization
            friendly_name = base_param
            unit = "count"
            
            if 'temp' in base_param.lower() or 'temperature' in base_param.lower():
                friendly_name = f"Temperature {base_param.split('Temperature')[0] if 'Temperature' in base_param else base_param}"
                unit = "°C"
            elif 'flow' in base_param.lower():
                friendly_name = f"Flow {base_param.replace('Flow', '').replace('flow', '')}"
                unit = "L/min"
            elif 'speed' in base_param.lower() or 'fan' in base_param.lower():
                friendly_name = f"Fan Speed {base_param.replace('Speed', '').replace('speed', '').replace('Fan', '').replace('fan', '')}"
                unit = "RPM"
            elif 'voltage' in base_param.lower() or 'volt' in base_param.lower() or any(v in base_param.lower() for v in ['24v', '48v', '5v', '12v', '3_3v', '1_2v']):
                friendly_name = f"Voltage {base_param.replace('_MON_STAT', '').replace('_', ' ')}"
                unit = "V"
            elif 'humidity' in base_param.lower():
                friendly_name = f"Humidity {base_param.replace('humidity', '').replace('Humidity', '')}"
                unit = "%"
            
            print(f"   {base_param} | {friendly_name} | {unit}")

if __name__ == "__main__":
    test_parameter_matching()