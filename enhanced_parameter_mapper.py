"""
Enhanced Parameter Mapper for HALog Application
Uses mapedname.txt file to provide strict parameter filtering and mapping.
Implements the requirement to process only mapped parameters from mapedname.txt.

Developer: HALog Enhancement Team
Company: gobioeng.com
"""

import os
import re
from typing import Dict, List, Tuple, Optional, Set


class EnhancedParameterMapper:
    """
    Streamlined parameter mapper focused on strict filtering using mapedname.txt.
    Only processes parameters explicitly listed in the mapping file.
    """
    
    def __init__(self, mapedname_file_path: str = "data/mapedname.txt"):
        self.mapedname_file_path = mapedname_file_path
        self.parameter_mapping: Dict[str, Dict] = {}
        
        # O(1) lookup sets for efficient filtering
        self.parameter_allowlist: Set[str] = set()
        self.parameter_variations: Set[str] = set()
        
        # Merged parameter configuration for equivalent parameters
        self.merged_parameters: Dict[str, List[str]] = {}
        
        # Load parameter mappings from mapedname.txt
        self._load_parameter_mappings()
        self._setup_parameter_merging()
        self._create_parameter_allowlist()
    
    def _load_parameter_mappings(self):
        """Load parameter mappings from mapedname.txt file with strict filtering"""
        try:
            if not os.path.exists(self.mapedname_file_path):
                print(f"❌ Error: {self.mapedname_file_path} not found!")
                print("🔒 Strict filtering mode: No parameters will be processed without mapedname.txt")
                return
            
            print(f"📋 Loading parameter mappings from {self.mapedname_file_path}")
            
            with open(self.mapedname_file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # Parse the mapedname.txt file format
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip empty lines, headers, and separators
                if not line or line.startswith('#') or '---' in line or line.startswith('1.') or line.startswith('2.'):
                    continue
                
                # Parse parameter mapping lines
                parsed = self._parse_mapping_line(line, line_num)
                if parsed:
                    machine_name, friendly_name, unit = parsed
                    
                    # Store mapping with category classification
                    category = self._classify_parameter_category(machine_name, friendly_name)
                    
                    self.parameter_mapping[machine_name] = {
                        'friendly_name': friendly_name,
                        'unit': unit,
                        'machine_name': machine_name,
                        'category': category,
                        'line_number': line_num
                    }
            
            loaded_count = len(self.parameter_mapping)
            print(f"✅ Loaded {loaded_count} parameter mappings from mapedname.txt")
            
            if loaded_count == 0:
                print("❌ No valid mappings found in mapedname.txt!")
                print("🔒 Strict filtering mode: No parameters will be processed")
                
        except Exception as e:
            print(f"❌ Error loading parameter mappings: {e}")
            print("🔒 Strict filtering mode: No parameters will be processed")

    def _parse_mapping_line(self, line: str, line_num: int) -> Optional[Tuple[str, str, str]]:
        """Parse a single line from mapedname.txt"""
        try:
            # Handle line format: "machine_name | friendly_name | unit"
            if '|' in line:
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 3:
                    machine_name = parts[0]
                    friendly_name = parts[1] 
                    unit = parts[2]
                    
                    # Validate that we have all required fields
                    if machine_name and friendly_name and unit:
                        return (machine_name, friendly_name, unit)
                        
        except Exception as e:
            print(f"⚠️ Warning: Error parsing line {line_num}: {e}")
        
        return None
    
    def _classify_parameter_category(self, machine_name: str, friendly_name: str) -> str:
        """Classify parameters into categories for trend tab organization"""
        name_lower = (machine_name + " " + friendly_name).lower()
        
        # Cooling System
        if any(keyword in name_lower for keyword in ['flow', 'pump', 'cooling', 'water', 'temp']):
            return 'Cooling System'
        
        # Voltages  
        elif any(keyword in name_lower for keyword in ['volt', 'v', '+12v', '-12v', '+5v', '-5v', '24v', '48v']):
            return 'Voltages'
        
        # Temperatures
        elif any(keyword in name_lower for keyword in ['temperature', 'temp', '°c']):
            return 'Temperatures'
        
        # Environmental
        elif any(keyword in name_lower for keyword in ['fan', 'speed', 'humidity', 'humid', 'rpm']):
            return 'Environmental'
        
        # System Diagnostics
        elif any(keyword in name_lower for keyword in ['pressure', 'psi', 'drift', 'deviation', 'motor', 'gantry', 'collimator']):
            return 'System Diagnostics'
        
        else:
            return 'Other'

    def _setup_parameter_merging(self):
        """Setup merged parameter configuration for equivalent parameters"""
        # Define parameter groups that should be merged
        self.merged_parameters = {
            # Magnetron Flow - merge multiple sources into unified metric
            "magnetronFlow": ["magnetronFlow", "CoolingmagnetronFlowLowStatistics"],
            
            # Target & Circulator Flow - merge multiple sources into unified metric  
            "targetAndCirculatorFlow": ["targetAndCirculatorFlow", "CoolingtargetFlowLowStatistics"]
        }
        
        print(f"✅ Configured {len(self.merged_parameters)} merged parameter groups")
        
        # Ensure merged parameters have proper categorization
        for unified_name, source_params in self.merged_parameters.items():
            if unified_name in self.parameter_mapping:
                config = self.parameter_mapping[unified_name]
                # Add category for trend tab organization
                if 'flow' in unified_name.lower():
                    config['category'] = 'Cooling System'
                    config['priority'] = 1  # High priority for merging
                print(f"📊 Merged parameter '{unified_name}' configured with sources: {source_params}")

    def _create_parameter_allowlist(self):
        """Create O(1) allowlist for strict parameter filtering"""
        self.parameter_allowlist.clear()
        self.parameter_variations.clear()
        
        for machine_name in self.parameter_mapping.keys():
            # Add exact machine name
            self.parameter_allowlist.add(machine_name)
            self.parameter_allowlist.add(machine_name.lower())
            
            # Add variations for better matching
            variations = [
                machine_name,
                machine_name.lower(),
                re.sub(r'[_\s\-]+', '', machine_name.lower()),
                re.sub(r'statistics$', '', machine_name.lower(), flags=re.IGNORECASE)
            ]
            
            for variation in variations:
                if variation:
                    self.parameter_variations.add(variation)
        
        # Add merged parameter sources to allowlist
        for unified_name, source_params in self.merged_parameters.items():
            for source_param in source_params:
                self.parameter_allowlist.add(source_param)
                self.parameter_allowlist.add(source_param.lower())
                self.parameter_variations.add(source_param.lower())
        
        print(f"🔒 Created parameter allowlist with {len(self.parameter_allowlist)} entries for strict filtering")

    def is_parameter_allowed(self, parameter_name: str) -> bool:
        """
        Strict parameter filtering - only allow parameters from mapedname.txt
        This implements the core requirement for strict parameter filtering.
        """
        if not parameter_name:
            return False
        
        # Check against allowlist with O(1) lookup
        if parameter_name in self.parameter_allowlist:
            return True
        
        # Check parameter variations
        cleaned = re.sub(r'[_\s\-]+', '', parameter_name.lower())
        return cleaned in self.parameter_variations

    def map_parameter_name(self, parameter_name: str) -> Dict[str, str]:
        """Map parameter name to friendly name and unit"""
        # Direct lookup first
        if parameter_name in self.parameter_mapping:
            return self.parameter_mapping[parameter_name]
        
        # Check merged parameters
        for unified_name, source_params in self.merged_parameters.items():
            if parameter_name in source_params:
                if unified_name in self.parameter_mapping:
                    return self.parameter_mapping[unified_name]
        
        # Fallback
        return {
            'friendly_name': parameter_name,
            'unit': '',
            'machine_name': parameter_name,
            'category': 'Other'
        }

    def should_merge_parameter(self, parameter_name: str) -> Tuple[bool, str, List[str]]:
        """
        Check if parameter should be merged and return merge info
        Returns: (should_merge, unified_name, source_parameters)
        """
        for unified_name, source_params in self.merged_parameters.items():
            if parameter_name in source_params:
                return True, unified_name, source_params
        return False, parameter_name, [parameter_name]

    def get_merged_parameter_sources(self, unified_name: str) -> List[str]:
        """Get list of source parameters for a merged parameter"""
        return self.merged_parameters.get(unified_name, [unified_name])

    def get_mapping_statistics(self) -> Dict[str, int]:
        """Get statistics about parameter mappings"""
        return {
            'total_mappings': len(self.parameter_mapping),
            'allowlist_size': len(self.parameter_allowlist),
            'merged_parameter_groups': len(self.merged_parameters),
            'source_file': self.mapedname_file_path
        }

    def get_categories(self) -> Dict[str, List[str]]:
        """Get parameters organized by category for trend tabs"""
        categories = {}
        for machine_name, mapping in self.parameter_mapping.items():
            category = mapping.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(machine_name)
        return categories