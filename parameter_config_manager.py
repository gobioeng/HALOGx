"""
Parameter Configuration Manager for HALog Application
Dynamic parameter mapping system with hot-reload capability

Developer: HALog Enhancement Team
Company: gobioeng.com
"""

import os
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import threading
from datetime import datetime


class ParameterConfigManager:
    """
    Advanced parameter configuration manager for dynamic mapping management.
    
    Features:
    - Dynamic loading from mappedname_V3.txt
    - Hot-reload capability for parameter mapping updates  
    - Parameter validation and error checking
    - Threshold range inference for unmapped parameters
    - Thread-safe configuration updates
    - File monitoring for automatic reload
    """
    
    def __init__(self, config_file_path: str = None):
        self.config_file_path = config_file_path or self._find_default_config_file()
        self.parameter_mapping = {}
        self.file_last_modified = 0
        self.auto_reload_enabled = False
        self._reload_lock = threading.Lock()
        self._file_monitor_thread = None
        
        # Load initial configuration
        self.load_parameter_mapping()
        
    def _find_default_config_file(self) -> str:
        """Find the default parameter mapping file"""
        # Try multiple possible locations
        possible_paths = [
            "data/mappedname_V3.txt",
            "mappedname_V3.txt", 
            "../data/mappedname_V3.txt",
            os.path.join(os.path.dirname(__file__), "data", "mappedname_V3.txt"),
            os.path.join(os.path.dirname(__file__), "mappedname_V3.txt")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
                
        # If none found, create default path
        default_path = os.path.join(os.path.dirname(__file__), "data", "mappedname_V3.txt")
        return default_path
        
    def load_parameter_mapping(self) -> bool:
        """
        Load parameter mapping from configuration file.
        Returns True if successful, False otherwise.
        """
        try:
            if not os.path.exists(self.config_file_path):
                print(f"⚠️ Parameter config file not found: {self.config_file_path}")
                self._create_fallback_mapping()
                return False
                
            # Check file modification time
            current_mtime = os.path.getmtime(self.config_file_path)
            if current_mtime <= self.file_last_modified:
                return True  # No changes
                
            with self._reload_lock:
                print(f"📖 Loading parameter mapping from: {self.config_file_path}")
                
                new_mapping = {}
                
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            # Skip empty lines and headers
                            line = line.strip()
                            if not line or line.startswith('-') or 'Machine Log Name' in line:
                                continue
                                
                            # Parse line: machine_name | display_name | unit
                            if '|' in line:
                                parts = [part.strip() for part in line.split('|')]
                                if len(parts) >= 3:
                                    machine_name = parts[0]
                                    display_name = parts[1]
                                    unit = parts[2]
                                    
                                    # Clean up names
                                    machine_name = self._clean_parameter_name(machine_name)
                                    
                                    if machine_name and display_name:
                                        config = self._create_parameter_config(
                                            machine_name, display_name, unit
                                        )
                                        new_mapping[machine_name] = config
                                        
                        except Exception as e:
                            print(f"⚠️ Error parsing line {line_num}: {e}")
                            continue
                
                # Update mapping atomically
                self.parameter_mapping = new_mapping
                self.file_last_modified = current_mtime
                
                print(f"✅ Loaded {len(self.parameter_mapping)} parameter mappings")
                return True
                
        except Exception as e:
            print(f"❌ Error loading parameter mapping: {e}")
            self._create_fallback_mapping()
            return False
            
    def _clean_parameter_name(self, name: str) -> str:
        """Clean and normalize parameter name"""
        if not name:
            return ""
            
        # Remove extra whitespace
        name = name.strip()
        
        # Remove trailing colons
        if name.endswith('::'):
            name = name[:-2]
        elif name.endswith(':'):
            name = name[:-1]
            
        return name
        
    def _create_parameter_config(self, machine_name: str, display_name: str, unit: str) -> Dict[str, Any]:
        """Create parameter configuration with inferred thresholds"""
        
        # Create regex patterns for matching variations
        patterns = self._generate_patterns(machine_name)
        
        # Infer threshold ranges based on parameter type and unit
        expected_range, critical_range = self._infer_threshold_ranges(display_name, unit)
        
        return {
            "patterns": patterns,
            "unit": unit,
            "description": display_name,
            "expected_range": expected_range,
            "critical_range": critical_range,
            "parameter_type": self._classify_parameter_type(display_name, unit)
        }
        
    def _generate_patterns(self, machine_name: str) -> List[str]:
        """Generate regex patterns for parameter matching"""
        patterns = [machine_name]  # Exact match first
        
        # Add variations
        # Camel case version
        camel_case = re.sub(r'[_\s]+', '', machine_name)
        if camel_case != machine_name:
            patterns.append(camel_case)
            
        # Snake case version  
        snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', machine_name).lower()
        if snake_case != machine_name:
            patterns.append(snake_case)
            
        # Space separated version
        space_separated = re.sub(r'[_]+', ' ', machine_name)
        if space_separated != machine_name:
            patterns.append(space_separated)
            
        # Add common variations
        if 'Statistics' in machine_name:
            base_name = machine_name.replace('Statistics', '')
            patterns.extend([base_name, base_name + 'Stats', base_name + 'Stat'])
            
        return patterns
        
    def _classify_parameter_type(self, display_name: str, unit: str) -> str:
        """Classify parameter into major categories"""
        display_lower = display_name.lower()
        unit_lower = unit.lower()
        
        if 'flow' in display_lower or 'l/min' in unit_lower:
            return 'flow'
        elif 'temp' in display_lower or '°c' in unit_lower or 'celsius' in unit_lower:
            return 'temperature'
        elif 'voltage' in display_lower or 'v' == unit_lower.strip():
            return 'voltage'
        elif 'pressure' in display_lower or 'psi' in unit_lower:
            return 'pressure'  
        elif 'humidity' in display_lower or '%' in unit_lower or 'relative' in unit_lower:
            return 'humidity'
        elif 'speed' in display_lower or 'rpm' in unit_lower:
            return 'fan_speed'
        elif 'drift' in display_lower or 'mm' in unit_lower:
            return 'motion'
        else:
            return 'general'
            
    def _infer_threshold_ranges(self, display_name: str, unit: str) -> Tuple[Optional[Tuple[float, float]], Optional[Tuple[float, float]]]:
        """Infer reasonable threshold ranges based on parameter type"""
        param_type = self._classify_parameter_type(display_name, unit)
        
        # Define reasonable ranges for different parameter types
        threshold_defaults = {
            'flow': {
                'expected': (5, 20),
                'critical': (2, 25)
            },
            'temperature': {
                'expected': (15, 85), 
                'critical': (5, 100)
            },
            'voltage': {
                'expected': (-50, 50),  # Wide range for different voltage types
                'critical': (-60, 60)
            },
            'pressure': {
                'expected': (10, 50),
                'critical': (5, 80)
            },
            'humidity': {
                'expected': (30, 70),
                'critical': (10, 90)
            },
            'fan_speed': {
                'expected': (1000, 5000),
                'critical': (500, 8000)
            },
            'motion': {
                'expected': (-2, 2),
                'critical': (-5, 5)
            }
        }
        
        if param_type in threshold_defaults:
            defaults = threshold_defaults[param_type]
            return defaults['expected'], defaults['critical']
        else:
            # No reasonable defaults for unknown types
            return None, None
            
    def _create_fallback_mapping(self):
        """Create basic fallback mapping if config file is unavailable"""
        print("📝 Creating fallback parameter mapping...")
        
        self.parameter_mapping = {
            # Core water system parameters
            "magnetronFlow": {
                "patterns": ["magnetron flow", "magnetronFlow", "CoolingmagnetronFlowLowStatistics"],
                "unit": "L/min",
                "description": "Magnetron Flow",
                "expected_range": (8, 18),
                "critical_range": (6, 20),
                "parameter_type": "flow"
            },
            "targetAndCirculatorFlow": {
                "patterns": ["target and circulator flow", "targetAndCirculatorFlow", "CoolingtargetFlowLowStatistics"],
                "unit": "L/min", 
                "description": "Target & Circulator Flow",
                "expected_range": (6, 12),
                "critical_range": (4, 15),
                "parameter_type": "flow"
            },
            "magnetronTemp": {
                "patterns": ["magnetron temp", "magnetronTemp", "magnetron temperature"],
                "unit": "°C",
                "description": "Magnetron Temperature", 
                "expected_range": (20, 80),
                "critical_range": (10, 100),
                "parameter_type": "temperature"
            },
            "targetAndCirculatorTemp": {
                "patterns": ["target and circulator temp", "targetAndCirculatorTemp", "target temperature"],
                "unit": "°C",
                "description": "Target & Circulator Temperature",
                "expected_range": (20, 80),
                "critical_range": (10, 100),
                "parameter_type": "temperature"
            }
        }
        
    def get_parameter_config(self, parameter_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific parameter"""
        return self.parameter_mapping.get(parameter_name)
        
    def get_all_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get all parameter configurations"""
        return self.parameter_mapping.copy()
        
    def get_parameters_by_type(self, param_type: str) -> Dict[str, Dict[str, Any]]:
        """Get all parameters of a specific type"""
        return {
            name: config for name, config in self.parameter_mapping.items()
            if config.get('parameter_type') == param_type
        }
        
    def find_parameter_by_pattern(self, log_parameter_name: str) -> Optional[str]:
        """Find mapped parameter name by matching patterns"""
        log_param_lower = log_parameter_name.lower()
        
        for param_name, config in self.parameter_mapping.items():
            patterns = config.get('patterns', [])
            
            for pattern in patterns:
                if pattern.lower() == log_param_lower:
                    return param_name
                    
                # Try partial matching for complex names
                if pattern.lower() in log_param_lower or log_param_lower in pattern.lower():
                    return param_name
                    
        return None
        
    def enable_auto_reload(self, check_interval: float = 1.0):
        """Enable automatic reloading when config file changes"""
        if self.auto_reload_enabled:
            return
            
        self.auto_reload_enabled = True
        self._file_monitor_thread = threading.Thread(
            target=self._monitor_config_file, 
            args=(check_interval,),
            daemon=True
        )
        self._file_monitor_thread.start()
        print(f"🔄 Auto-reload enabled for {self.config_file_path}")
        
    def disable_auto_reload(self):
        """Disable automatic reloading"""
        self.auto_reload_enabled = False
        if self._file_monitor_thread:
            self._file_monitor_thread.join(timeout=1.0)
        print("⏹️ Auto-reload disabled")
        
    def _monitor_config_file(self, check_interval: float):
        """Monitor config file for changes in background thread"""
        while self.auto_reload_enabled:
            try:
                if os.path.exists(self.config_file_path):
                    current_mtime = os.path.getmtime(self.config_file_path)
                    if current_mtime > self.file_last_modified:
                        print(f"🔄 Config file changed, reloading...")
                        self.load_parameter_mapping()
                        
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"⚠️ Error monitoring config file: {e}")
                time.sleep(check_interval * 5)  # Longer delay on error
                
    def reload_config(self) -> bool:
        """Manually reload configuration from file"""
        print("🔄 Manually reloading parameter configuration...")
        return self.load_parameter_mapping()
        
    def validate_parameter_mapping(self) -> Tuple[List[str], List[str]]:
        """
        Validate the current parameter mapping.
        Returns (warnings, errors) lists.
        """
        warnings = []
        errors = []
        
        for param_name, config in self.parameter_mapping.items():
            # Check required fields
            required_fields = ['patterns', 'unit', 'description']
            for field in required_fields:
                if field not in config:
                    errors.append(f"Parameter '{param_name}' missing required field: {field}")
                    
            # Check patterns
            patterns = config.get('patterns', [])
            if not patterns:
                errors.append(f"Parameter '{param_name}' has no patterns defined")
            elif not isinstance(patterns, list):
                errors.append(f"Parameter '{param_name}' patterns must be a list")
                
            # Check threshold ranges
            expected_range = config.get('expected_range')
            critical_range = config.get('critical_range')
            
            if expected_range and len(expected_range) == 2:
                if expected_range[0] >= expected_range[1]:
                    warnings.append(f"Parameter '{param_name}' expected range invalid: {expected_range}")
                    
            if critical_range and len(critical_range) == 2:
                if critical_range[0] >= critical_range[1]:
                    warnings.append(f"Parameter '{param_name}' critical range invalid: {critical_range}")
                    
        return warnings, errors
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the parameter mapping"""
        if not self.parameter_mapping:
            return {"total_parameters": 0}
            
        types = {}
        for config in self.parameter_mapping.values():
            param_type = config.get('parameter_type', 'unknown')
            types[param_type] = types.get(param_type, 0) + 1
            
        return {
            "total_parameters": len(self.parameter_mapping),
            "parameters_by_type": types,
            "config_file": self.config_file_path,
            "file_last_modified": datetime.fromtimestamp(self.file_last_modified).isoformat() if self.file_last_modified else None,
            "auto_reload_enabled": self.auto_reload_enabled
        }
        
    def export_mapping_to_file(self, output_path: str) -> bool:
        """Export current mapping to a file for backup/sharing"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# HALog Parameter Mapping Export\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write("# Format: Machine Log Name | User-Friendly Name | Unit\n")
                f.write("-" * 70 + "\n")
                
                for param_name, config in sorted(self.parameter_mapping.items()):
                    description = config.get('description', param_name)
                    unit = config.get('unit', '')
                    f.write(f"{param_name} | {description} | {unit}\n")
                    
            print(f"✅ Parameter mapping exported to: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting parameter mapping: {e}")
            return False


# Global instance for easy access
_global_parameter_manager = None

def get_parameter_manager() -> ParameterConfigManager:
    """Get the global parameter manager instance"""
    global _global_parameter_manager
    if _global_parameter_manager is None:
        _global_parameter_manager = ParameterConfigManager()
    return _global_parameter_manager