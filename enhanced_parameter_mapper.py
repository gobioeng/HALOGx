"""
Enhanced Parameter Mapper for HALog Application
Uses mapedname.txt file to properly map log parameters to user-friendly names
Addresses the parameter parsing issues mentioned in the problem statement.

Developer: HALog Enhancement Team
Company: gobioeng.com
"""

import os
import re
from typing import Dict, List, Tuple, Optional
import pandas as pd


class EnhancedParameterMapper:
    """
    Enhanced parameter mapper that uses mapedname.txt to properly map
    raw log parameter names to user-friendly display names with units.
    """
    
    def __init__(self, mapedname_file_path: str = "data/mapedname.txt"):
        self.mapedname_file_path = mapedname_file_path
        self.parameter_mapping: Dict[str, Dict] = {}
        self.reverse_mapping: Dict[str, str] = {}
        self.pattern_cache: Dict[str, str] = {}
        
        # Load parameter mappings from mapedname.txt
        self._load_parameter_mappings()
    
    def _load_parameter_mappings(self):
        """Load parameter mappings from mapedname.txt file"""
        try:
            if not os.path.exists(self.mapedname_file_path):
                print(f"⚠️ Warning: {self.mapedname_file_path} not found. Using default mappings.")
                self._load_default_mappings()
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
                    
                    # Store mapping
                    self.parameter_mapping[machine_name] = {
                        'friendly_name': friendly_name,
                        'unit': unit,
                        'machine_name': machine_name,
                        'patterns': [machine_name.lower(), friendly_name.lower()],
                        'line_number': line_num
                    }
                    
                    # Create reverse mapping for quick lookup
                    self.reverse_mapping[friendly_name.lower()] = machine_name
                    
                    # Add pattern variations for better matching
                    self._add_pattern_variations(machine_name, friendly_name)
            
            loaded_count = len(self.parameter_mapping)
            print(f"✅ Loaded {loaded_count} parameter mappings from mapedname.txt")
            
            if loaded_count == 0:
                print("⚠️ No valid mappings found in mapedname.txt, using defaults")
                self._load_default_mappings()
                
        except Exception as e:
            print(f"❌ Error loading parameter mappings: {e}")
            print("⚠️ Falling back to default parameter mappings")
            self._load_default_mappings()
    
    def _parse_mapping_line(self, line: str, line_num: int) -> Optional[Tuple[str, str, str]]:
        """Parse a single line from mapedname.txt"""
        try:
            # Handle different line formats in mapedname.txt
            # Format: "machine_name | friendly_name | unit"
            if '|' in line:
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 3:
                    machine_name = parts[0]
                    friendly_name = parts[1] 
                    unit = parts[2]
                    
                    # Clean up the names
                    machine_name = self._clean_parameter_name(machine_name)
                    friendly_name = self._clean_parameter_name(friendly_name)
                    unit = unit.strip()
                    
                    # Validate we have meaningful names (not just header text)
                    if (machine_name and friendly_name and 
                        machine_name.lower() not in ['machine log name', 'machine', 'log', 'name'] and
                        friendly_name.lower() not in ['user-friendly name', 'user', 'friendly', 'name'] and
                        len(machine_name) > 2 and len(friendly_name) > 2):
                        return machine_name, friendly_name, unit
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error parsing line {line_num}: {e}")
            return None
    
    def _clean_parameter_name(self, name: str) -> str:
        """Clean parameter name by removing numbering and extra spaces"""
        if not name:
            return ""
        
        # Remove leading numbers like "3.", "15.", etc.
        name = re.sub(r'^\d+\.?\s*', '', name)
        
        # Remove any trailing/leading whitespace
        name = name.strip()
        
        return name
    
    def _add_pattern_variations(self, machine_name: str, friendly_name: str):
        """Add pattern variations for better parameter matching"""
        variations = []
        
        # Original names
        variations.extend([machine_name, friendly_name])
        
        # Lowercase versions
        variations.extend([machine_name.lower(), friendly_name.lower()])
        
        # Remove spaces, underscores, etc.
        clean_machine = re.sub(r'[_\s]+', '', machine_name.lower())
        clean_friendly = re.sub(r'[_\s]+', '', friendly_name.lower())
        variations.extend([clean_machine, clean_friendly])
        
        # Add all variations to pattern cache
        for variation in variations:
            if variation:
                self.pattern_cache[variation] = machine_name
    
    def _load_default_mappings(self):
        """Load default parameter mappings as fallback"""
        default_mappings = {
            'magnetronFlow': {
                'friendly_name': 'Magnetron Flow',
                'unit': 'L/min',
                'machine_name': 'magnetronFlow',
                'patterns': ['magnetronflow', 'magnetron flow']
            },
            'targetAndCirculatorFlow': {
                'friendly_name': 'Target & Circulator Flow', 
                'unit': 'L/min',
                'machine_name': 'targetAndCirculatorFlow',
                'patterns': ['targetandcirculatorflow', 'target and circulator flow']
            },
            'FanremoteTempStatistics': {
                'friendly_name': 'Room Temperature',
                'unit': '°C', 
                'machine_name': 'FanremoteTempStatistics',
                'patterns': ['fanremotetemp', 'room temperature']
            },
            'FanhumidityStatistics': {
                'friendly_name': 'Room Humidity',
                'unit': '%',
                'machine_name': 'FanhumidityStatistics', 
                'patterns': ['fanhumidity', 'room humidity']
            },
            'sf6GasPressure': {
                'friendly_name': 'SF6 Gas Pressure',
                'unit': 'PSI',
                'machine_name': 'sf6GasPressure',
                'patterns': ['sf6pressure', 'sf6 gas pressure']
            },
            'CoolingpumpHighStatistics': {
                'friendly_name': 'Water Pump Pressure',
                'unit': 'PSI', 
                'machine_name': 'CoolingpumpHighStatistics',
                'patterns': ['coolingpump', 'water pump pressure']
            },
            'CoolingcityWaterTempStatistics': {
                'friendly_name': 'City water flow',
                'unit': 'l/m',
                'machine_name': 'CoolingcityWaterTempStatistics',
                'patterns': ['citywater', 'city water flow']
            },
            'CoolingtargetFlowLowStatistics': {
                'friendly_name': 'Target & Circulator Flow',
                'unit': 'l/m',
                'machine_name': 'CoolingtargetFlowLowStatistics', 
                'patterns': ['targetflow', 'target flow']
            },
            'CoolingmagnetronFlowLowStatistics': {
                'friendly_name': 'Magnetron Flow',
                'unit': 'L/min',
                'machine_name': 'CoolingmagnetronFlowLowStatistics',
                'patterns': ['magnetronflow', 'magnetron flow']
            }
        }
        
        self.parameter_mapping = default_mappings
        
        # Build reverse mapping and pattern cache
        for machine_name, config in default_mappings.items():
            friendly_name = config['friendly_name']
            self.reverse_mapping[friendly_name.lower()] = machine_name
            
            # Add patterns to cache
            for pattern in config['patterns']:
                self.pattern_cache[pattern] = machine_name
        
        print(f"✅ Loaded {len(default_mappings)} default parameter mappings")
    
    def map_parameter_name(self, raw_parameter: str) -> Dict[str, str]:
        """
        Map a raw parameter name to friendly name and unit using mapedname.txt
        
        Args:
            raw_parameter: Raw parameter name from log file
            
        Returns:
            Dict containing friendly_name, unit, machine_name
        """
        if not raw_parameter:
            return {
                'friendly_name': 'Unknown Parameter',
                'unit': '',
                'machine_name': raw_parameter
            }
        
        # Clean the parameter name
        cleaned_param = self._clean_parameter_name(raw_parameter)
        
        # Try exact match first
        if cleaned_param in self.parameter_mapping:
            config = self.parameter_mapping[cleaned_param]
            return {
                'friendly_name': config['friendly_name'],
                'unit': config['unit'], 
                'machine_name': config['machine_name']
            }
        
        # Try pattern matching
        param_lower = cleaned_param.lower()
        param_clean = re.sub(r'[_\s]+', '', param_lower)
        
        # Check pattern cache
        for pattern, machine_name in self.pattern_cache.items():
            if pattern in param_lower or param_clean in pattern:
                if machine_name in self.parameter_mapping:
                    config = self.parameter_mapping[machine_name]
                    return {
                        'friendly_name': config['friendly_name'],
                        'unit': config['unit'],
                        'machine_name': config['machine_name']
                    }
        
        # Check for partial matches in friendly names
        for machine_name, config in self.parameter_mapping.items():
            friendly_lower = config['friendly_name'].lower()
            
            # Check if any words match
            param_words = set(param_lower.split())
            friendly_words = set(friendly_lower.split())
            
            if param_words & friendly_words:  # If there's any intersection
                return {
                    'friendly_name': config['friendly_name'],
                    'unit': config['unit'],
                    'machine_name': config['machine_name']
                }
        
        # Return original if no mapping found
        return {
            'friendly_name': cleaned_param,
            'unit': '',
            'machine_name': cleaned_param
        }
    
    def get_all_parameters(self) -> List[Dict]:
        """Get list of all available parameters with their mappings"""
        return [
            {
                'machine_name': machine_name,
                'friendly_name': config['friendly_name'],
                'unit': config['unit'],
                'patterns': config.get('patterns', [])
            }
            for machine_name, config in self.parameter_mapping.items()
        ]
    
    def is_target_parameter(self, parameter_name: str) -> bool:
        """
        Check if a parameter is one we want to extract based on mapedname.txt
        This addresses the issue of not extracting enough data points.
        """
        if not parameter_name:
            return False
        
        # Clean parameter name
        cleaned = self._clean_parameter_name(parameter_name)
        
        # Check if it's in our mapping
        mapped = self.map_parameter_name(cleaned)
        
        # Consider it a target parameter if:
        # 1. It has a mapping in mapedname.txt
        # 2. Or it contains keywords we care about
        
        if mapped['machine_name'] in self.parameter_mapping:
            return True
        
        # Check for important keywords even if not in mapping
        param_lower = cleaned.lower()
        target_keywords = [
            'flow', 'temp', 'temperature', 'pressure', 'humidity', 'voltage', 
            'current', 'speed', 'fan', 'pump', 'water', 'magnetron', 'target',
            'circulator', 'sf6', 'adc', 'mlc', 'col', 'cooling', 'statistics'
        ]
        
        return any(keyword in param_lower for keyword in target_keywords)
    
    def get_mapping_statistics(self) -> Dict:
        """Get statistics about the parameter mappings"""
        return {
            'total_mappings': len(self.parameter_mapping),
            'pattern_cache_size': len(self.pattern_cache),
            'reverse_mappings': len(self.reverse_mapping),
            'source_file': self.mapedname_file_path,
            'file_exists': os.path.exists(self.mapedname_file_path)
        }