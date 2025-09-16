"""
Hardcoded Parameters for HALOGx Application - Performance Optimization
This module contains precompiled parameter mappings to eliminate file I/O operations
and improve application startup performance.

Based on mapedname.txt and existing parameter mappings.
Developer: gobioeng.com
"""

import re
from typing import Dict, List, Tuple, Optional

class HardcodedParameterMapper:
    """
    High-performance parameter mapper with precompiled mappings
    Eliminates need for file I/O operations during application startup
    """
    
    def __init__(self):
        # Precompiled regex patterns for maximum performance
        self.compiled_patterns = self._compile_optimized_patterns()
        
        # Hardcoded parameter mappings from mapedname.txt
        self.parameter_mappings = self._get_hardcoded_mappings()
        
        # Reverse mapping for fast lookups
        self.reverse_mapping = self._build_reverse_mapping()
        
        # Pattern cache for frequently accessed parameters
        self.pattern_cache = {}
        
        print(f"✓ Hardcoded parameter mapper initialized with {len(self.parameter_mappings)} parameters")
    
    def _compile_optimized_patterns(self) -> Dict[str, re.Pattern]:
        """Compile all regex patterns once for maximum performance"""
        return {
            # Optimized datetime patterns
            "datetime_primary": re.compile(
                r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})", re.IGNORECASE
            ),
            "datetime_alt": re.compile(
                r"(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2}:\d{2})", re.IGNORECASE
            ),
            
            # High-performance parameter extraction pattern
            "parameter_statistics": re.compile(
                r"([a-zA-Z][a-zA-Z0-9_\s\-\.]*[a-zA-Z0-9])"     # Parameter name
                r"[:\s]*(?:Statistics)?[:\s]*"                   # Optional Statistics keyword
                r"(?:count\s*=\s*(\d+)[,\s]*)??"                # count
                r"(?:max\s*=\s*([\d.\-+eE]+)[,\s]*)??"         # max
                r"(?:min\s*=\s*([\d.\-+eE]+)[,\s]*)??"         # min  
                r"(?:avg\s*=\s*([\d.\-+eE]+))??"               # avg
                , re.IGNORECASE
            ),
            
            # Serial number extraction
            "serial_number": re.compile(r"(?:SN|S/N|Serial)[#\s]*(\d+)", re.IGNORECASE),
            
            # Machine ID extraction
            "machine_id": re.compile(r"Machine[:\s]+(\d+)", re.IGNORECASE),
        }
    
    def _get_hardcoded_mappings(self) -> Dict[str, Dict]:
        """
        Hardcoded parameter mappings for maximum performance
        Based on mapedname.txt and enhanced with optimization data
        """
        return {
            # === WATER SYSTEM PARAMETERS ===
            "magnetronFlow": {
                "friendly_name": "Magnetron Flow",
                "unit": "L/min",
                "patterns": ["magnetronflow", "magnetron flow", "coolingmagnetronflowlowstatistics"],
                "expected_range": (8.0, 18.0),
                "critical_threshold": 6.0,
                "category": "water_system"
            },
            "targetAndCirculatorFlow": {
                "friendly_name": "Target & Circulator Flow", 
                "unit": "L/min",
                "patterns": ["targetandcirculatorflow", "target and circulator flow", "coolingtargetflowlowstatistics"],
                "expected_range": (6.0, 12.0),
                "critical_threshold": 4.0,
                "category": "water_system"
            },
            "CoolingcityWaterTempStatistics": {
                "friendly_name": "City water flow",
                "unit": "l/m",
                "patterns": ["coolingcitywatereupstatistics", "city water flow", "citywatertempstatistics"],
                "expected_range": (8.0, 18.0),
                "critical_threshold": 6.0,
                "category": "water_system"
            },
            "CoolingtargetFlowLowStatistics": {
                "friendly_name": "Target & Circulator Flow",
                "unit": "l/m", 
                "patterns": ["coolingtargetflowlowstatistics", "target flow low", "targetflowlow"],
                "expected_range": (6.0, 12.0),
                "critical_threshold": 4.0,
                "category": "water_system"
            },
            "CoolingmagnetronFlowLowStatistics": {
                "friendly_name": "Magnetron Flow",
                "unit": "L/min",
                "patterns": ["coolingmagnetronflowlowstatistics", "magnetron flow low", "magnetronflowlow"],
                "expected_range": (8.0, 18.0),
                "critical_threshold": 6.0,
                "category": "water_system"
            },
            
            # === TEMPERATURE PARAMETERS ===
            "magnetronTemp": {
                "friendly_name": "Magnetron Temperature",
                "unit": "°C",
                "patterns": ["magnetrontemp", "magnetron temperature", "magnetron temp"],
                "expected_range": (20.0, 45.0),
                "critical_threshold": 50.0,
                "category": "temperature"
            },
            "targetAndCirculatorTemp": {
                "friendly_name": "Target & Circulator Temperature",
                "unit": "°C", 
                "patterns": ["targetandcirculatortemp", "target and circulator temperature", "target temp"],
                "expected_range": (20.0, 40.0),
                "critical_threshold": 45.0,
                "category": "temperature"
            },
            "FanremoteTempStatistics": {
                "friendly_name": "Temp Room",
                "unit": "°C",
                "patterns": ["fanremotetempstatistics", "fan remote temp", "remote temperature"],
                "expected_range": (18.0, 28.0),
                "critical_threshold": 35.0,
                "category": "temperature"
            },
            
            # === MLC VOLTAGE PARAMETERS ===
            "MLC_ADC_CHAN_TEMP_BANKA_STAT": {
                "friendly_name": "MLC Temperature Bank A",
                "unit": "°C",
                "patterns": ["mlc_adc_chan_temp_banka_stat", "mlc temp bank a", "mlctemperaturebanka"],
                "expected_range": (20.0, 50.0),
                "critical_threshold": 60.0,
                "category": "mlc_temperature"
            },
            "MLC_ADC_CHAN_TEMP_BANKB_STAT": {
                "friendly_name": "MLC Temperature Bank B", 
                "unit": "°C",
                "patterns": ["mlc_adc_chan_temp_bankb_stat", "mlc temp bank b", "mlctemperaturebankb"],
                "expected_range": (20.0, 50.0),
                "critical_threshold": 60.0,
                "category": "mlc_temperature"
            },
            "MLC_ADC_CHAN_PROXIMAL_10V_BANKA_MON_STAT": {
                "friendly_name": "MLC Proximal 10V Bank A",
                "unit": "V",
                "patterns": ["mlc_adc_chan_proximal_10v_banka_mon_stat", "mlc proximal 10v bank a"],
                "expected_range": (9.5, 10.5),
                "critical_threshold": 9.0,
                "category": "mlc_voltage"
            },
            "MLC_ADC_CHAN_PROXIMAL_10V_BANKB_MON_STAT": {
                "friendly_name": "MLC Proximal 10V Bank B",
                "unit": "V", 
                "patterns": ["mlc_adc_chan_proximal_10v_bankb_mon_stat", "mlc proximal 10v bank b"],
                "expected_range": (9.5, 10.5),
                "critical_threshold": 9.0,
                "category": "mlc_voltage"
            },
            "MLC_ADC_CHAN_DISTAL_10V_BANKA_MON_STAT": {
                "friendly_name": "MLC Distal 10V Bank A",
                "unit": "V",
                "patterns": ["mlc_adc_chan_distal_10v_banka_mon_stat", "mlc distal 10v bank a"],
                "expected_range": (9.5, 10.5),
                "critical_threshold": 9.0,
                "category": "mlc_voltage"
            },
            "MLC_ADC_CHAN_DISTAL_10V_BANKB_MON_STAT": {
                "friendly_name": "MLC Distal 10V Bank B",
                "unit": "V",
                "patterns": ["mlc_adc_chan_distal_10v_bankb_mon_stat", "mlc distal 10v bank b"],
                "expected_range": (9.5, 10.5),
                "critical_threshold": 9.0,
                "category": "mlc_voltage"
            },
            "MLC_ADC_CHAN_24V_BANKA_MON_STAT": {
                "friendly_name": "MLC 24V Bank A",
                "unit": "V",
                "patterns": ["mlc_adc_chan_24v_banka_mon_stat", "mlc 24v bank a", "mlc24vbanka"],
                "expected_range": (23.0, 25.0),
                "critical_threshold": 22.0,
                "category": "mlc_voltage"
            },
            "MLC_ADC_CHAN_24V_BANKB_MON_STAT": {
                "friendly_name": "MLC 24V Bank B",
                "unit": "V",
                "patterns": ["mlc_adc_chan_24v_bankb_mon_stat", "mlc 24v bank b", "mlc24vbankb"],
                "expected_range": (23.0, 25.0),
                "critical_threshold": 22.0,
                "category": "mlc_voltage"
            },
            "MLC_ADC_CHAN_P12VA_BANKA_MON_STAT": {
                "friendly_name": "MLC +12V Analog Bank A",
                "unit": "V",
                "patterns": ["mlc_adc_chan_p12va_banka_mon_stat", "mlc +12v analog bank a"],
                "expected_range": (11.5, 12.5),
                "critical_threshold": 11.0,
                "category": "mlc_voltage"
            },
            "MLC_ADC_CHAN_P12VA_BANKB_MON_STAT": {
                "friendly_name": "MLC +12V Analog Bank B",
                "unit": "V",
                "patterns": ["mlc_adc_chan_p12va_bankb_mon_stat", "mlc +12v analog bank b"],
                "expected_range": (11.5, 12.5),
                "critical_threshold": 11.0,
                "category": "mlc_voltage"
            },
            "MLC_ADC_CHAN_M11V_BANKA_MON_STAT": {
                "friendly_name": "MLC -11V Bank A",
                "unit": "V",
                "patterns": ["mlc_adc_chan_m11v_banka_mon_stat", "mlc -11v bank a"],
                "expected_range": (-11.5, -10.5),
                "critical_threshold": -10.0,
                "category": "mlc_voltage"
            },
            "MLC_ADC_CHAN_M11V_BANKB_MON_STAT": {
                "friendly_name": "MLC -11V Bank B",
                "unit": "V",
                "patterns": ["mlc_adc_chan_m11v_bankb_mon_stat", "mlc -11v bank b"],
                "expected_range": (-11.5, -10.5),
                "critical_threshold": -10.0,
                "category": "mlc_voltage"
            },
            
            # === COL BOARD PARAMETERS ===
            "COL_BOARD_TEMP_MON_STAT": {
                "friendly_name": "COL Board Temperature",
                "unit": "°C",
                "patterns": ["col_board_temp_mon_stat", "col board temperature", "colboardtemp"],
                "expected_range": (20.0, 50.0),
                "critical_threshold": 60.0,
                "category": "col_temperature"
            },
            
            # === POWER SUPPLY PARAMETERS ===
            "flowSensorPower12V": {
                "friendly_name": "Flow Sensor Power",
                "unit": "V",
                "patterns": ["flowsensorpower12v", "flow sensor power", "flowsensorpower"],
                "expected_range": (11.5, 12.5),
                "critical_threshold": 11.0,
                "category": "power_supply"
            },
            "sf6SensorPower12V": {
                "friendly_name": "SF6 Sensor Power",
                "unit": "V",
                "patterns": ["sf6sensorpower12v", "sf6 sensor power", "sf6sensorpower"],
                "expected_range": (11.5, 12.5),
                "critical_threshold": 11.0,
                "category": "power_supply"
            },
            
            # === PRESSURE PARAMETERS ===
            "sf6GasPressure": {
                "friendly_name": "SF6 Gas Pressure",
                "unit": "PSI",
                "patterns": ["sf6gaspressure", "sf6 gas pressure", "sf6pressure"],
                "expected_range": (40.0, 60.0),
                "critical_threshold": 30.0,
                "category": "pressure"
            },
            "CoolingpumpHighStatistics": {
                "friendly_name": "Water Pump Pressure",
                "unit": "PSI",
                "patterns": ["coolingpumphighstatistics", "cooling pump high", "pumppressure"],
                "expected_range": (30.0, 50.0),
                "critical_threshold": 25.0,
                "category": "pressure"
            },
            
            # === FAN SPEED PARAMETERS ===
            "FanfanSpeed1Statistics": {
                "friendly_name": "Speed FAN 1",
                "unit": "RPM",
                "patterns": ["fanfanspeed1statistics", "fan speed 1", "fanspeed1"],
                "expected_range": (1500.0, 3000.0),
                "critical_threshold": 1000.0,
                "category": "fan_speed"
            },
            "FanfanSpeed2Statistics": {
                "friendly_name": "Speed FAN 2",
                "unit": "RPM",
                "patterns": ["fanfanspeed2statistics", "fan speed 2", "fanspeed2"],
                "expected_range": (1500.0, 3000.0),
                "critical_threshold": 1000.0,
                "category": "fan_speed"
            },
            "FanfanSpeed3Statistics": {
                "friendly_name": "Speed FAN 3",
                "unit": "RPM",
                "patterns": ["fanfanspeed3statistics", "fan speed 3", "fanspeed3"],
                "expected_range": (1500.0, 3000.0),
                "critical_threshold": 1000.0,
                "category": "fan_speed"
            },
            "FanfanSpeed4Statistics": {
                "friendly_name": "Speed FAN 4",
                "unit": "RPM",
                "patterns": ["fanfanspeed4statistics", "fan speed 4", "fanspeed4"],
                "expected_range": (1500.0, 3000.0),
                "critical_threshold": 1000.0,
                "category": "fan_speed"
            },
            
            # === HUMIDITY PARAMETERS ===
            "FanhumidityStatistics": {
                "friendly_name": "Room Humidity",
                "unit": "%",
                "patterns": ["fanhumiditystatistics", "fan humidity", "humidity"],
                "expected_range": (30.0, 70.0),
                "critical_threshold": 80.0,
                "category": "humidity"
            }
        }
    
    def _build_reverse_mapping(self) -> Dict[str, str]:
        """Build reverse mapping for fast parameter lookups"""
        reverse_map = {}
        
        for param_key, param_data in self.parameter_mappings.items():
            # Map friendly name to parameter key
            friendly_name = param_data["friendly_name"].lower()
            reverse_map[friendly_name] = param_key
            
            # Map all patterns to parameter key
            for pattern in param_data["patterns"]:
                reverse_map[pattern.lower()] = param_key
        
        return reverse_map
    
    def get_parameter_info(self, parameter_name: str) -> Optional[Dict]:
        """Fast parameter lookup by name or pattern"""
        # Check cache first
        if parameter_name in self.pattern_cache:
            cached_key = self.pattern_cache[parameter_name]
            return self.parameter_mappings.get(cached_key)
        
        # Normalize input
        normalized_name = parameter_name.lower().strip()
        
        # Direct lookup in reverse mapping
        if normalized_name in self.reverse_mapping:
            param_key = self.reverse_mapping[normalized_name]
            self.pattern_cache[parameter_name] = param_key
            return self.parameter_mappings[param_key]
        
        # Fuzzy matching for partial matches
        for param_key, param_data in self.parameter_mappings.items():
            for pattern in param_data["patterns"]:
                if pattern in normalized_name or normalized_name in pattern:
                    self.pattern_cache[parameter_name] = param_key
                    return param_data
        
        return None
    
    def get_category_parameters(self, category: str) -> List[Dict]:
        """Get all parameters for a specific category"""
        return [
            {"key": key, **data} 
            for key, data in self.parameter_mappings.items() 
            if data.get("category") == category
        ]
    
    def get_all_categories(self) -> List[str]:
        """Get all available parameter categories"""
        categories = set()
        for param_data in self.parameter_mappings.values():
            if "category" in param_data:
                categories.add(param_data["category"])
        return sorted(list(categories))
    
    def validate_parameter_value(self, parameter_name: str, value: float) -> Dict[str, bool]:
        """Validate parameter value against expected ranges"""
        param_info = self.get_parameter_info(parameter_name)
        if not param_info:
            return {"valid": False, "in_range": False, "critical": False}
        
        expected_range = param_info.get("expected_range")
        critical_threshold = param_info.get("critical_threshold")
        
        result = {"valid": True}
        
        if expected_range:
            result["in_range"] = expected_range[0] <= value <= expected_range[1]
        else:
            result["in_range"] = True
        
        if critical_threshold is not None:
            if isinstance(critical_threshold, (list, tuple)):
                result["critical"] = value < critical_threshold[0] or value > critical_threshold[1]
            else:
                result["critical"] = value < critical_threshold
        else:
            result["critical"] = False
        
        return result
    
    def extract_parameters_from_line(self, line: str) -> List[Tuple[str, Dict]]:
        """
        Fast parameter extraction from log line using precompiled patterns
        Returns list of (parameter_name, parsed_data) tuples
        """
        results = []
        
        # Use precompiled pattern for performance
        pattern = self.compiled_patterns["parameter_statistics"]
        matches = pattern.finditer(line)
        
        for match in matches:
            param_name = match.group(1)
            if not param_name:
                continue
            
            # Get parameter info
            param_info = self.get_parameter_info(param_name)
            if not param_info:
                continue
            
            # Extract statistics values
            count = match.group(2)
            max_val = match.group(3)
            min_val = match.group(4) 
            avg_val = match.group(5)
            
            # Convert to numbers
            parsed_data = {
                "parameter_name": param_name,
                "friendly_name": param_info["friendly_name"],
                "unit": param_info["unit"],
                "category": param_info["category"]
            }
            
            try:
                if count:
                    parsed_data["count"] = int(count)
                if max_val:
                    parsed_data["max"] = float(max_val)
                if min_val:
                    parsed_data["min"] = float(min_val)
                if avg_val:
                    parsed_data["avg"] = float(avg_val)
                    
                    # Validate value
                    validation = self.validate_parameter_value(param_name, float(avg_val))
                    parsed_data.update(validation)
            except (ValueError, TypeError):
                continue
            
            results.append((param_name, parsed_data))
        
        return results

# Global instance for fast access
hardcoded_mapper = HardcodedParameterMapper()

def get_hardcoded_mapper() -> HardcodedParameterMapper:
    """Get the global hardcoded parameter mapper instance"""
    return hardcoded_mapper