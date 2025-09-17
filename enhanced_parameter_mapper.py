"""
Enhanced Parameter Mapper for HALog Application
Uses mapedname.txt file to properly map log parameters to user-friendly names
Addresses the parameter parsing issues mentioned in the problem statement.

Developer: HALog Enhancement Team
Company: gobioeng.com
"""

import os
import re
from typing import Dict, List, Tuple, Optional, Set
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
        
        # Strict allowlist for parameter filtering
        self.parameter_allowlist: Set[str] = set()
        self.merged_parameters: Dict[str, List[str]] = {}
        
        # Load parameter mappings from mapedname.txt
        self._load_parameter_mappings()
        self._setup_parameter_merging()
        self._create_parameter_allowlist()
    
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
                    config['category'] = 'Water System'
                    config['tab'] = 'Flow'
                    config['priority'] = 1  # High priority for merging
                print(f"📊 Merged parameter '{unified_name}' configured with sources: {source_params}")
    
    def _create_parameter_allowlist(self):
        """Create strict allowlist from mapedname.txt for parameter filtering"""
        self.parameter_allowlist = set()
        
        # Add all machine names from mappings
        for machine_name in self.parameter_mapping.keys():
            self.parameter_allowlist.add(machine_name)
            self.parameter_allowlist.add(machine_name.lower())
            
            # Add variations for better matching
            variations = [
                machine_name.replace('_', ''),
                machine_name.replace(' ', ''),
                machine_name.replace('-', ''),
                re.sub(r'[_\s\-]+', '', machine_name.lower())
            ]
            self.parameter_allowlist.update(variations)
        
        # Add patterns from mapping configurations
        for config in self.parameter_mapping.values():
            for pattern in config.get('patterns', []):
                self.parameter_allowlist.add(pattern)
                self.parameter_allowlist.add(pattern.lower())
        
        print(f"🔒 Created parameter allowlist with {len(self.parameter_allowlist)} entries for strict filtering")
    
    def is_parameter_allowed(self, parameter_name: str) -> bool:
        """
        Strict parameter filtering - only allow parameters from mapedname.txt
        This implements the core requirement for strict parameter filtering.
        """
        if not parameter_name:
            return False
        
        # Clean parameter name for comparison
        cleaned = self._clean_parameter_name(parameter_name)
        param_variations = [
            parameter_name,
            parameter_name.lower(), 
            cleaned,
            cleaned.lower(),
            re.sub(r'[_\s\-]+', '', parameter_name.lower()),
            re.sub(r'[_\s\-]+', '', cleaned.lower())
        ]
        
        # Check against allowlist
        return any(variation in self.parameter_allowlist for variation in param_variations)
    
    def get_merged_parameter_sources(self, unified_name: str) -> List[str]:
        """Get list of source parameters for a merged parameter"""
        return self.merged_parameters.get(unified_name, [unified_name])
    
    def should_merge_parameter(self, parameter_name: str) -> Tuple[bool, str, List[str]]:
        """
        Check if parameter should be merged and return merge info
        Returns: (should_merge, unified_name, source_parameters)
        """
        for unified_name, source_params in self.merged_parameters.items():
            if parameter_name in source_params:
                return True, unified_name, source_params
        return False, parameter_name, [parameter_name]
    
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
        
    def map_parameter_name(self, raw_parameter: str) -> Dict[str, str]:
        """
        Map a raw parameter name to friendly name and unit using mapedname.txt
        Enhanced with better fuzzy matching for improved parameter recognition.
        
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
        
        # Enhanced pattern matching with multiple strategies
        param_lower = cleaned_param.lower()
        param_clean = re.sub(r'[_\s\-]+', '', param_lower)
        
        # Strategy 1: Check direct pattern cache matches
        for pattern, machine_name in self.pattern_cache.items():
            pattern_clean = re.sub(r'[_\s\-]+', '', pattern.lower())
            if (pattern_clean in param_clean or 
                param_clean in pattern_clean or
                pattern in param_lower):
                if machine_name in self.parameter_mapping:
                    config = self.parameter_mapping[machine_name]
                    return {
                        'friendly_name': config['friendly_name'],
                        'unit': config['unit'],
                        'machine_name': config['machine_name']
                    }
        
        # Strategy 2: Enhanced substring matching with scoring
        best_match = None
        best_score = 0
        
        for machine_name, config in self.parameter_mapping.items():
            machine_lower = machine_name.lower()
            machine_clean = re.sub(r'[_\s\-]+', '', machine_lower)
            friendly_lower = config['friendly_name'].lower()
            friendly_clean = re.sub(r'[_\s\-]+', '', friendly_lower)
            
            # Calculate match score based on multiple criteria
            score = 0
            
            # Exact substring matches get highest score
            if machine_clean in param_clean or param_clean in machine_clean:
                score += 10
            if friendly_clean in param_clean or param_clean in friendly_clean:
                score += 8
            
            # Word-based matching
            param_words = set(param_lower.split())
            machine_words = set(machine_lower.split())
            friendly_words = set(friendly_lower.split())
            
            # Count common words
            machine_common = len(param_words & machine_words)
            friendly_common = len(param_words & friendly_words)
            
            if machine_common > 0:
                score += machine_common * 3
            if friendly_common > 0:
                score += friendly_common * 2
            
            # Check for keyword matches (temperature, flow, etc.)
            important_keywords = ['temp', 'temperature', 'flow', 'pressure', 'voltage', 'humid']
            for keyword in important_keywords:
                if keyword in param_lower and keyword in machine_lower:
                    score += 5
                if keyword in param_lower and keyword in friendly_lower:
                    score += 4
            
            # Pattern matches from additional patterns
            for pattern in config.get('patterns', []):
                pattern_clean = re.sub(r'[_\s\-]+', '', pattern.lower())
                if pattern_clean in param_clean or param_clean in pattern_clean:
                    score += 6
            
            # Track best match
            if score > best_score:
                best_score = score
                best_match = config
        
        # Return best match if score is high enough
        if best_match and best_score >= 3:  # Minimum threshold for matching
            return {
                'friendly_name': best_match['friendly_name'],
                'unit': best_match['unit'],
                'machine_name': best_match['machine_name']
            }
        
        # Strategy 3: Fallback - return original parameter with attempted unit detection
        detected_unit = self._detect_unit_from_name(param_lower)
        
        return {
            'friendly_name': cleaned_param,
            'unit': detected_unit,
            'machine_name': cleaned_param
        }
    
    def _detect_unit_from_name(self, param_name: str) -> str:
        """Detect likely unit from parameter name"""
        param_lower = param_name.lower()
        
        # Common unit patterns in parameter names
        if any(word in param_lower for word in ['temp', 'temperature', 'thermal']):
            return '°C'
        elif any(word in param_lower for word in ['flow', 'rate']):
            return 'L/min'
        elif any(word in param_lower for word in ['pressure', 'psi']):
            return 'PSI'
        elif any(word in param_lower for word in ['voltage', 'volt']):
            return 'V'
        elif any(word in param_lower for word in ['current', 'amp']):
            return 'A'
        elif any(word in param_lower for word in ['humid', 'moisture']):
            return '%'
        elif any(word in param_lower for word in ['speed', 'rpm']):
            return 'RPM'
        elif any(word in param_lower for word in ['count', 'number']):
            return 'count'
        elif any(word in param_lower for word in ['time', 'duration']):
            return 's'
        else:
            return ''
    
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
        Check if a parameter should be processed based on strict allowlist from mapedname.txt
        This replaces the old keyword-based matching with strict filtering.
        """
        if not parameter_name:
            return False
        
        # Use strict allowlist filtering - only parameters from mapedname.txt
        return self.is_parameter_allowed(parameter_name)
    
    def get_mapping_statistics(self) -> Dict:
        """Get statistics about the parameter mappings"""
        return {
            'total_mappings': len(self.parameter_mapping),
            'pattern_cache_size': len(self.pattern_cache),
            'reverse_mappings': len(self.reverse_mapping),
            'allowlist_size': len(self.parameter_allowlist),
            'merged_parameter_groups': len(self.merged_parameters),
            'source_file': self.mapedname_file_path,
            'file_exists': os.path.exists(self.mapedname_file_path)
        }