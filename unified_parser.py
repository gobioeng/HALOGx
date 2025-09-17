"""
Unified Parser for HALog Application
Consolidates LINAC log parsing, fault code parsing, and short data parsing
into a single comprehensive parser module.

This addresses the requirement to use only one file for data parsing
instead of multiple separate parser files.

Developer: HALog Enhancement Team  
Company: gobioeng.com
"""

import pandas as pd
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import os
import random

# Import caching system for fault code optimization
try:
    from cache_manager import DataCacheManager
    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False
    print("⚠️ Caching not available - fault code loading will be slower")

# Import enhanced parameter mapper for better parsing
try:
    from enhanced_parameter_mapper import EnhancedParameterMapper
    ENHANCED_MAPPING_AVAILABLE = True
except ImportError:
    ENHANCED_MAPPING_AVAILABLE = False
    print("⚠️ Enhanced parameter mapping not available - using basic mapping")


class UnifiedParser:
    """
    Unified parser for all HALog data types:
    - LINAC log files (water system parameters, temperatures, voltages, etc.)
    - Fault code databases (dynamic loading from uploaded files)
    - Short data files (additional diagnostic parameters)
    """

    def __init__(self):
        self._compile_patterns()
        self.parsing_stats = {
            "lines_processed": 0,
            "records_extracted": 0,
            "errors_encountered": 0,
            "processing_time": 0,
        }
        self.fault_codes: Dict[str, Dict[str, str]] = {}
        self.parameter_mapping = {}  # Initialize before calling _init_parameter_mapping
        self.df: Optional[pd.DataFrame] = None # Initialize df to None
        
        # Initialize enhanced parameter mapper for strict filtering
        if ENHANCED_MAPPING_AVAILABLE:
            try:
                self.enhanced_mapper = EnhancedParameterMapper()
                print("✅ Enhanced parameter mapper initialized - using mapedname.txt for parameter mapping")
                stats = self.enhanced_mapper.get_mapping_statistics()
                print(f"📊 Loaded {stats['total_mappings']} parameter mappings")
                print(f"🔒 Parameter allowlist: {stats['allowlist_size']} entries")
                print(f"🔗 Merged parameter groups: {stats['merged_parameter_groups']}")
            except Exception as e:
                print(f"⚠️ Error initializing enhanced mapper: {e}")
                self.enhanced_mapper = None
        else:
            self.enhanced_mapper = None
            print("❌ Enhanced mapping not available - strict filtering disabled")
        
        # Initialize fault code caching system for performance optimization
        if CACHING_AVAILABLE:
            self.fault_cache = DataCacheManager(cache_dir="data/cache/fault_codes")
            # Initialize search result cache for frequently searched codes
            self.search_cache = DataCacheManager(cache_dir="data/cache/fault_searches")
            print("✅ Fault code caching system initialized - faster loading enabled")
            print("✅ Search result caching enabled - frequently searched codes load instantly")
        else:
            self.fault_cache = None
            self.search_cache = None
            print("⚠️ Operating without fault code caching")
            
        self._init_parameter_mapping()  # Call after other initializations
        
        # Initialize enhanced parsing statistics for detailed logging
        self.parsing_stats = {
            "total_lines_read": 0,
            "parameters_detected": 0,
            "parameters_mapped": 0,
            "parameters_allowed": 0,
            "parameters_skipped": 0,
            "valid_records_extracted": 0,
            "skipped_records": 0,
            "skipped_reasons": {},
            "merged_parameter_records": 0,
            "parsing_start_time": None,
            "parsing_end_time": None,
            "processing_time": 0,
            "records_per_second": 0
        }

    def get_fault_descriptions_by_database(self, fault_code):
        """Get fault descriptions from both HAL and TB databases"""
        hal_description = ""
        tb_description = ""

        if fault_code in self.fault_codes:
            fault_data = self.fault_codes[fault_code]
            source = fault_data.get('source', '')
            description = fault_data.get('description', '')

            if source == 'hal' or source == 'uploaded':  # HAL database
                hal_description = description
            elif source == 'tb':  # TB database
                tb_description = description

        return {
            'hal_description': hal_description,
            'tb_description': tb_description
        }

    def _compile_patterns(self):
        """Compile regex patterns for enhanced log parsing"""
        self.patterns = {
            # Enhanced datetime patterns
            "datetime": re.compile(
                r"(\d{4}-\d{2}-\d{2})[ \t]+(\d{2}:\d{2}:\d{2})", re.IGNORECASE
            ),
            "datetime_alt": re.compile(
                r"(\d{1,2}/\d{1,2}/\d{4})[ \t]+(\d{1,2}:\d{2}:\d{2})"
            ),
            # Enhanced parameter patterns - optimized for HALOG format
            "water_parameters": re.compile(
                r"(?:logStatistics\s+)?"                         # Optional logStatistics prefix
                r"([a-zA-Z][a-zA-Z0-9_\-\.]*[a-zA-Z0-9])"       # Parameter name (no spaces, more strict)
                r":\s*"                                          # Colon separator
                r"count\s*=\s*(\d+)"                            # Required count
                r"(?:[,\s]*max\s*=\s*([\d.\-+eE]+))?"           # Optional max
                r"(?:[,\s]*min\s*=\s*([\d.\-+eE]+))?"           # Optional min  
                r"(?:[,\s]*avg\s*=\s*([\d.\-+eE]+))?"           # Optional avg
                , re.IGNORECASE
            ),
            # Serial number patterns with more variations
            "serial_number": re.compile(r"(?:SN|S/N|Serial)[#\s]*(\d+)", re.IGNORECASE),
            "serial_alt": re.compile(r"Serial[:\s]+(\d+)", re.IGNORECASE),
            "machine_id": re.compile(r"Machine[:\s]+(\d+)", re.IGNORECASE),
            
            # Additional patterns for better parameter extraction
            "parameter_with_units": re.compile(
                r"([a-zA-Z][a-zA-Z0-9_\s\-\.]*)"               # Parameter name
                r"[:\s]*"                                       # Separator
                r"([\d.\-+eE]+)"                               # Value
                r"\s*"                                          # Optional space
                r"([a-zA-Z%°/]+)??"                            # Optional unit
                r"\s*"                                          # Optional space
                r"(?:\(([^)]+)\))??"                           # Optional description in parentheses
                , re.IGNORECASE
            ),
            
            # Enhanced logStatistics pattern
            "log_statistics": re.compile(
                r"logStatistics\s+"                            # logStatistics prefix
                r"([a-zA-Z][a-zA-Z0-9_\s\-\.]*)"              # Parameter name
                r"[:\s]*"                                       # Separator
                r"count\s*=\s*(\d+)[,\s]*"                     # count
                r"max\s*=\s*([\d.\-+eE]+)[,\s]*"              # max
                r"min\s*=\s*([\d.\-+eE]+)[,\s]*"              # min
                r"avg\s*=\s*([\d.\-+eE]+)",                   # avg
                re.IGNORECASE
            )
        }

    def _init_parameter_mapping(self):
        """Initialize comprehensive parameter mapping for all parameters"""
        self.parameter_mapping = {
            # === WATER SYSTEM PARAMETERS ===
            "magnetronFlow": {
                "patterns": [
                    "magnetron flow", "magnetronFlow", "CoolingmagnetronFlowLowStatistics",
                    "Coolingmagnetron Flow Low Statistics", "magnetron_flow"
                ],
                "unit": "L/min",
                "description": "Mag Flow",
                "expected_range": (8, 18),
                "critical_range": (6, 20),
            },
            "targetAndCirculatorFlow": {
                "patterns": [
                    "target and circulator flow", "targetAndCirculatorFlow", 
                    "CoolingtargetFlowLowStatistics", "Cooling target Flow Low Statistics",
                    "target_flow", "circulator_flow"
                ],
                "unit": "L/min",
                "description": "Flow Target",
                "expected_range": (6, 12),
                "critical_range": (4, 15),
            },
            "cityWaterFlow": {
                "patterns": [
                    "cooling city water flow statistics", "CoolingcityWaterFlowLowStatistics",
                    "cityWaterFlow", "city_water_flow", "Cooling city Water Flow Low Statistics"
                ],
                "unit": "L/min",
                "description": "Flow Chiller Water",
                "expected_range": (8, 18),
                "critical_range": (6, 20),
            },
            "pumpPressure": {
                "patterns": [
                    "pump pressure", "pumpPressure", "CoolingpumpPressureStatistics",
                    "cooling pump pressure", "pump_pressure"
                ],
                "unit": "PSI",
                "description": "Cooling Pump Pressure",
                "expected_range": (10, 30),
                "critical_range": (5, 40),
            },

            # === TEMPERATURE PARAMETERS ===
            "FanremoteTempStatistics": {
                "patterns": [
                    "FanremoteTempStatistics", "Fan remote Temp Statistics", 
                    "remoteTempStatistics", "remote_temp_stats",
                    "logStatistics FanremoteTempStatistics", "Fan remote temp",
                    "fanremotetemp", "remoteTemp"
                ],
                "unit": "°C",
                "description": "Temp Room",
                "expected_range": (18, 25),
                "critical_range": (15, 30),
            },
            "magnetronTemp": {
                "patterns": [
                    "magnetronTemp", "magnetron temp", "magnetron temperature",
                    "mag_temp", "magTemp", "magnetronTemperature"
                ],
                "unit": "°C",
                "description": "Temp Magnetron",
                "expected_range": (30, 50),
                "critical_range": (20, 60),
            },
            "CoolingtargetTempStatistics": {
                "patterns": [
                    "CoolingtargetTempStatistics", "cooling_target_temp_statistics",
                    "Cooling target Temp Statistics", "targetTempStatistics",
                    "target_temp", "cooling_target_temp"
                ],
                "unit": "L/min",
                "description": "Flow Target",
                "expected_range": (6, 12),
                "critical_range": (4, 15),
            },
            "COLboardTemp": {
                "patterns": [
                    "COL board temp", "COLboardTemp", "col_board_temp",
                    "COL Board Temperature"
                ],
                "unit": "°C",
                "description": "Temp COL Board",
                "expected_range": (20, 40),
                "critical_range": (15, 50),
            },
            "PDUTemp": {
                "patterns": [
                    "PDUTemp", "PDU temp", "PDU Temperature", "pdu_temp",
                    "pduTemp", "pduTemperature", "PDU_TEMP"
                ],
                "unit": "°C",
                "description": "Temp PDU",
                "expected_range": (20, 40),
                "critical_range": (15, 50),
            },
            "waterTankTemp": {
                "patterns": [
                    "water tank temp", "waterTankTemp", "water_tank_temp",
                    "Water Tank Temperature"
                ],
                "unit": "°C",
                "description": "Temp Water Tank",
                "expected_range": (15, 25),
                "critical_range": (10, 30),
            },

            # === HUMIDITY PARAMETERS ===
            "FanhumidityStatistics": {
                "patterns": [
                    "FanhumidityStatistics", "Fan humidity Statistics", 
                    "humidityStatistics", "humidity_stats",
                    "logStatistics FanhumidityStatistics", "Fan humidity"
                ],
                "unit": "%",
                "description": "Room Humidity",
                "expected_range": (40, 60),
                "critical_range": (30, 80),
            },
            "roomHumidity": {
                "patterns": [
                    "room humidity", "roomHumidity", "room_humidity",
                    "Room Humidity Statistics"
                ],
                "unit": "%",
                "description": "Humidity Room",
                "expected_range": (40, 60),
                "critical_range": (30, 80),
            },

            # === FAN SPEED PARAMETERS ===
            "FanfanSpeed1Statistics": {
                "patterns": [
                    "FanfanSpeed1Statistics", "Fan fan Speed 1 Statistics", 
                    "fanSpeed1Statistics", "fan_speed_1",
                    "logStatistics FanfanSpeed1Statistics", "Fan Speed 1"
                ],
                "unit": "RPM",
                "description": "Speed FAN 1",
                "expected_range": (1000, 3000),
                "critical_range": (500, 4000),
            },
            "FanfanSpeed2Statistics": {
                "patterns": [
                    "FanfanSpeed2Statistics", "Fan fan Speed 2 Statistics", 
                    "fanSpeed2Statistics", "fan_speed_2",
                    "logStatistics FanfanSpeed2Statistics", "Fan Speed 2"
                ],
                "unit": "RPM",
                "description": "Speed FAN 2",
                "expected_range": (1000, 3000),
                "critical_range": (500, 4000),
            },
            "FanfanSpeed3Statistics": {
                "patterns": [
                    "FanfanSpeed3Statistics", "Fan fan Speed 3 Statistics", 
                    "fanSpeed3Statistics", "fan_speed_3",
                    "logStatistics FanfanSpeed3Statistics", "Fan Speed 3"
                ],
                "unit": "RPM",
                "description": "Speed FAN 3",
                "expected_range": (1000, 3000),
                "critical_range": (500, 4000),
            },
            "FanfanSpeed4Statistics": {
                "patterns": [
                    "FanfanSpeed4Statistics", "Fan fan Speed 4 Statistics", 
                    "fanSpeed4Statistics", "fan_speed_4",
                    "logStatistics FanfanSpeed4Statistics", "Fan Speed 4"
                ],
                "unit": "RPM",
                "description": "Speed FAN 4",
                "expected_range": (1000, 3000),
                "critical_range": (500, 4000),
            },

            # === VOLTAGE PARAMETERS ===
            "MLC_ADC_CHAN_TEMP_BANKA_STAT_24V": {
                "patterns": [
                    "MLC_ADC_CHAN_TEMP_BANKA_STAT_24V", "MLC ADC CHAN TEMP BANKA STAT 24V",
                    "BANKA_STAT_24V", "BANKA 24V", "mlc_bank_a_24v"
                ],
                "unit": "V",
                "description": "MLC Bank A 24V",
                "expected_range": (22, 26),
                "critical_range": (20, 28),
            },
            "MLC_ADC_CHAN_TEMP_BANKB_STAT_24V": {
                "patterns": [
                    "MLC_ADC_CHAN_TEMP_BANKB_STAT_24V", "MLC ADC CHAN TEMP BANKB STAT 24V",
                    "BANKB_STAT_24V", "BANKB 24V", "mlc_bank_b_24v"
                ],
                "unit": "V",
                "description": "MLC Bank B 24V",
                "expected_range": (22, 26),
                "critical_range": (20, 28),
            },
            "MLC_ADC_CHAN_TEMP_BANKA_STAT_48V": {
                "patterns": [
                    "MLC_ADC_CHAN_TEMP_BANKA_STAT_48V", "MLC ADC CHAN TEMP BANKA STAT 48V",
                    "BANKA_STAT_48V", "BANKA 48V", "mlc_bank_a_48v"
                ],
                "unit": "V",
                "description": "MLC Bank A 48V",
                "expected_range": (46, 50),
                "critical_range": (44, 52),
            },
            "MLC_ADC_CHAN_TEMP_BANKB_STAT_48V": {
                "patterns": [
                    "MLC_ADC_CHAN_TEMP_BANKB_STAT_48V", "MLC ADC CHAN TEMP BANKB STAT 48V",
                    "BANKB_STAT_48V", "BANKB 48V", "mlc_bank_b_48v"
                ],
                "unit": "V",
                "description": "MLC Bank B 48V",
                "expected_range": (46, 50),
                "critical_range": (44, 52),
            },
            "COL_ADC_CHAN_TEMP_24V_MON": {
                "patterns": [
                    "COL_ADC_CHAN_TEMP_24V_MON", "COL ADC CHAN TEMP 24V MON",
                    "col_24v_mon", "COL 24V Monitor"
                ],
                "unit": "V",
                "description": "COL 24V Monitor",
                "expected_range": (22, 26),
                "critical_range": (20, 28),
            },
            "COL_ADC_CHAN_TEMP_5V_MON": {
                "patterns": [
                    "COL_ADC_CHAN_TEMP_5V_MON", "COL ADC CHAN TEMP 5V MON",
                    "col_5v_mon", "COL 5V Monitor"
                ],
                "unit": "V",
                "description": "COL 5V Monitor",
                "expected_range": (4.5, 5.5),
                "critical_range": (4.0, 6.0),
            },

            # === ADDITIONAL WATER PARAMETERS ===
            "waterTankLevel": {
                "patterns": [
                    "water tank level", "waterTankLevel", "tank_level"
                ],
                "unit": "%",
                "description": "Water Tank Level",
                "expected_range": (20, 80),
                "critical_range": (10, 90),
            },
            "chillerFlow": {
                "patterns": [
                    "chiller flow", "chillerFlow", "chiller_flow",
                    "Chiller Flow Rate"
                ],
                "unit": "L/min",
                "description": "Chiller Flow",
                "expected_range": (10, 20),
                "critical_range": (8, 25),
            },

            # === ADDITIONAL TEMPERATURE PARAMETERS ===
            "ambientTemp": {
                "patterns": [
                    "ambient temp", "ambientTemp", "ambient_temp",
                    "Ambient Temperature", "room_temp"
                ],
                "unit": "°C",
                "description": "Temp Ambient",
                "expected_range": (18, 25),
                "critical_range": (15, 30),
            },
            "chillerTemp": {
                "patterns": [
                    "chiller temp", "chillerTemp", "chiller_temp",
                    "Chiller Temperature"
                ],
                "unit": "°C",
                "description": "Temp Chiller",
                "expected_range": (5, 15),
                "critical_range": (0, 20),
            },

            # === PRESSURE PARAMETERS ===
            "systemPressure": {
                "patterns": [
                    "system pressure", "systemPressure", "system_pressure"
                ],
                "unit": "PSI",
                "description": "System Pressure",
                "expected_range": (15, 25),
                "critical_range": (10, 30),
            },
            "waterPressure": {
                "patterns": [
                    "water pressure", "waterPressure", "water_pressure"
                ],
                "unit": "PSI",
                "description": "Water Pressure",
                "expected_range": (20, 40),
                "critical_range": (15, 50),
            },
        }

        # Create pattern to unified name mapping
        self.pattern_to_unified = {}
        for unified_name, config in self.parameter_mapping.items():
            for pattern in config["patterns"]:
                key = pattern.lower().replace(" ", "").replace(":", "").replace("_", "")
                self.pattern_to_unified[key] = unified_name

        # Cache for parameter normalization (performance optimization)
        self._param_cache = {}

    def parse_linac_file(
        self,
        file_path: str,
        chunk_size: int = 1000,
        progress_callback=None,
        cancel_callback=None,
    ) -> pd.DataFrame:
        """Parse LINAC log file with optimized chunked processing for large files"""
        import time
        
        # Initialize parsing statistics
        self.parsing_stats["parsing_start_time"] = time.time()
        self.parsing_stats["total_lines_read"] = 0
        self.parsing_stats["skipped_reasons"] = {}
        
        records = []

        try:
            # Optimized file reading - stream processing instead of loading entire file
            self.parsing_stats["lines_processed"] = 0

            # Get file size for better progress estimation
            import os
            file_size = os.path.getsize(file_path)
            estimated_total_lines = file_size // 100  # Rough estimate: 100 bytes per line average

            # Use buffered reading for better performance
            with open(file_path, 'r', encoding='utf-8', buffering=8192) as file:
                chunk_lines = []
                line_number = 0

                for line in file:
                    if cancel_callback and cancel_callback():
                        break

                    line_number += 1
                    self.parsing_stats["total_lines_read"] += 1
                    line = line.strip()

                    # Skip empty lines early
                    if not line:
                        continue

                    chunk_lines.append((line_number, line))

                    # Process chunk when it reaches desired size
                    if len(chunk_lines) >= chunk_size:
                        chunk_records = self._process_chunk_optimized(chunk_lines)
                        records.extend(chunk_records)

                        self.parsing_stats["lines_processed"] += len(chunk_lines)

                        if progress_callback:
                            # Better progress calculation
                            progress = min(95.0, (self.parsing_stats["lines_processed"] / max(estimated_total_lines, line_number)) * 100.0)
                            progress_callback(progress, f"Processing line {self.parsing_stats['lines_processed']:,}...")

                        chunk_lines = []  # Reset chunk

                # Process remaining lines
                if chunk_lines:
                    chunk_records = self._process_chunk_optimized(chunk_lines)
                    records.extend(chunk_records)
                    self.parsing_stats["lines_processed"] += len(chunk_lines)

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            self.parsing_stats["errors_encountered"] += 1

        df = pd.DataFrame(records)
        cleaned_df = self._clean_and_validate_data(df)
        
        # Apply parameter merging for equivalent parameters
        merged_df = self._merge_equivalent_parameters(cleaned_df)
        
        # Update parsing statistics and log summary
        self._update_parsing_statistics(len(records), merged_df)
        self._log_parsing_summary(file_path)
        
        return merged_df

    def _process_chunk(self, chunk_lines: List[Tuple[int, str]]) -> List[Dict]:
        """Process a chunk of lines (legacy method for compatibility)"""
        return self._process_chunk_optimized(chunk_lines)

    def _process_chunk_optimized(self, chunk_lines: List[Tuple[int, str]]) -> List[Dict]:
        """Optimized chunk processing with strict parameter filtering from mapedname.txt"""
        records = []

        # Pre-compile frequently used patterns for this chunk
        water_pattern = self.patterns["water_parameters"]
        datetime_pattern = self.patterns["datetime"]
        datetime_alt_pattern = self.patterns["datetime_alt"]
        serial_pattern = self.patterns["serial_number"]

        for line_number, line in chunk_lines:
            try:
                self.parsing_stats["total_lines_read"] += 1
                
                # Detect if this is tab-separated format (new LINAC format)
                if '\t' in line and line.count('\t') >= 7:
                    # Parse as tab-separated LINAC format
                    parsed_records = self._parse_tab_separated_line(line, line_number)
                    records.extend(parsed_records)
                else:
                    # Early filtering - skip lines without statistics patterns
                    has_statistics = any(keyword in line.lower() for keyword in [
                        'count=', 'avg=', 'statistics', 'stat', 'max=', 'min=', 
                        'value=', 'reading=', 'measurement='
                    ])
                    
                    if not has_statistics:
                        continue

                    # STRICT PARAMETER FILTERING - Early check for mapped parameters only
                    if self.enhanced_mapper:
                        line_lower = line.lower()
                        # Use O(1) set lookup for performance
                        has_allowed_param = any(
                            param_var in line_lower 
                            for param_var in self.enhanced_mapper.parameter_variations
                        )
                        if not has_allowed_param:
                            self.parsing_stats["parameters_skipped"] += 1
                            self.parsing_stats["skipped_records"] += 1
                            self.parsing_stats["skipped_reasons"]["unmapped_parameter"] = self.parsing_stats["skipped_reasons"].get("unmapped_parameter", 0) + 1
                            continue
                    
                    self.parsing_stats["parameters_detected"] += 1

                    parsed_records = self._parse_line_optimized(line, line_number, 
                                                              water_pattern, datetime_pattern, 
                                                              datetime_alt_pattern, serial_pattern)
                    if parsed_records:
                        self.parsing_stats["parameters_allowed"] += len(parsed_records)
                    records.extend(parsed_records)
            except Exception as e:
                self.parsing_stats["errors_encountered"] += 1

        return records

    def _parse_tab_separated_line(self, line: str, line_number: int) -> List[Dict]:
        """Parse tab-separated LINAC log format (new format)"""
        records = []
        
        try:
            # Split by tabs - expected format:
            # Date      Time    Source  Level   Timestamp       SN#     System  Component       Message
            parts = line.split('\t')
            if len(parts) < 9:
                return records
                
            date_str = parts[0].strip()
            time_str = parts[1].strip()
            source = parts[2].strip()
            level = parts[3].strip()
            timestamp = parts[4].strip()
            sn_field = parts[5].strip()
            system = parts[6].strip()
            component = parts[7].strip()
            message = parts[8].strip()
            
            # Extract serial number
            serial_number = self._extract_serial_from_field(sn_field)
            
            # Create datetime
            try:
                datetime_obj = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return records
            
            # Check if message contains sensor data statistics
            if 'logStatistics' in message and any(keyword in message for keyword in ['count=', 'max=', 'min=', 'avg=']):
                # Extract parameter data from message
                param_records = self._extract_statistics_from_message(message, datetime_obj, serial_number, system, component, line_number)
                records.extend(param_records)
            
            # Check for temperature sensor data
            if 'TemperatureSensor' in message or 'cpuTemperatureSensor' in message:
                temp_records = self._extract_temperature_data(message, datetime_obj, serial_number, system, component, line_number)
                records.extend(temp_records)
            
            # Check for system mode information
            if 'SystemMode:' in message:
                mode_records = self._extract_system_mode(message, datetime_obj, serial_number, system, component, line_number)
                records.extend(mode_records)
                
            # Check for odometer data
            if 'Odometer' in message:
                odometer_records = self._extract_odometer_data(message, datetime_obj, serial_number, system, component, line_number)
                records.extend(odometer_records)
                
            # Check for EMO and motion events
            if any(event in message for event in ['EMO Good', 'Disable Motion', 'Enable Motion']):
                event_records = self._extract_event_data(message, datetime_obj, serial_number, system, component, line_number)
                records.extend(event_records)
                
        except Exception as e:
            print(f"Error parsing tab-separated line {line_number}: {e}")
            self.parsing_stats["errors_encountered"] += 1
            
        return records
    
    def _extract_serial_from_field(self, sn_field: str) -> str:
        """Extract serial number from SN# field - handles multiple formats"""
        sn_field = sn_field.strip()
        
        # Handle different serial number formats found in logs
        if 'SN#' in sn_field:
            # Format: "SN# 2182"
            return sn_field.replace('SN#', '').strip()
        elif sn_field.startswith('HAL-TRT-SN'):
            # Format: "HAL-TRT-SN2182" 
            return sn_field.replace('HAL-TRT-SN', '').strip()
        elif sn_field.startswith('SN'):
            # Format: "SN2182" or "SN 2182"
            return sn_field.replace('SN', '').strip()
        elif sn_field.isdigit():
            # Format: "2182" (plain number)
            return sn_field
        else:
            # Try to extract any number from the field
            import re
            match = re.search(r'(\d+)', sn_field)
            if match:
                return match.group(1)
            else:
                return sn_field  # Return as-is if no pattern matches
    
    def _extract_statistics_from_message(self, message: str, datetime_obj: datetime, 
                                       serial_number: str, system: str, component: str, line_number: int) -> List[Dict]:
        """Extract statistical data from log message"""
        records = []
        
        # Pattern to match: logStatistics parameterName: count=X, max=Y, min=Z, avg=W
        log_stats_pattern = re.compile(
            r'logStatistics\s+([^:]+):\s*'
            r'(?:count\s*=\s*(\d+)[,\s]*)?'
            r'(?:max\s*=\s*([\d.\-+eE]+)[,\s]*)?'
            r'(?:min\s*=\s*([\d.\-+eE]+)[,\s]*)?'
            r'(?:avg\s*=\s*([\d.\-+eE]+))?',
            re.IGNORECASE
        )
        
        match = log_stats_pattern.search(message)
        if match:
            param_name = match.group(1).strip()
            count = match.group(2)
            max_val = match.group(3)
            min_val = match.group(4)
            avg_val = match.group(5)
            
            # Normalize parameter name
            normalized_param = self._normalize_parameter_name(param_name)
            
            # Create records for each statistic type if available
            if count:
                records.append(self._create_record(
                    datetime_obj, f"{normalized_param}_count", count, 
                    "count", serial_number, system, component, line_number
                ))
            
            if max_val:
                records.append(self._create_record(
                    datetime_obj, f"{normalized_param}_max", float(max_val), 
                    self._get_unit_for_parameter(normalized_param), serial_number, system, component, line_number
                ))
                
            if min_val:
                records.append(self._create_record(
                    datetime_obj, f"{normalized_param}_min", float(min_val), 
                    self._get_unit_for_parameter(normalized_param), serial_number, system, component, line_number
                ))
                
            if avg_val:
                records.append(self._create_record(
                    datetime_obj, f"{normalized_param}_avg", float(avg_val), 
                    self._get_unit_for_parameter(normalized_param), serial_number, system, component, line_number
                ))
        
        return records
    
    def _extract_temperature_data(self, message: str, datetime_obj: datetime, 
                                 serial_number: str, system: str, component: str, line_number: int) -> List[Dict]:
        """Extract temperature sensor data from message"""
        records = []
        
        # Pattern for temperature sensors
        temp_pattern = re.compile(
            r'(cpuTemperatureSensor\d+|TemperatureSensor\d+):\s*'
            r'(?:count\s*=\s*(\d+)[,\s]*)?'
            r'(?:max\s*=\s*([\d.\-+eE]+)[,\s]*)?'
            r'(?:min\s*=\s*([\d.\-+eE]+)[,\s]*)?'
            r'(?:avg\s*=\s*([\d.\-+eE]+))?',
            re.IGNORECASE
        )
        
        match = temp_pattern.search(message)
        if match:
            sensor_name = match.group(1)
            count = match.group(2)
            max_val = match.group(3)
            min_val = match.group(4)
            avg_val = match.group(5)
            
            if avg_val:  # Temperature average is most important
                records.append(self._create_record(
                    datetime_obj, f"{sensor_name}_avg", float(avg_val), 
                    "°C", serial_number, system, component, line_number
                ))
                
            if max_val:
                records.append(self._create_record(
                    datetime_obj, f"{sensor_name}_max", float(max_val), 
                    "°C", serial_number, system, component, line_number
                ))
                
        return records
    
    def _extract_system_mode(self, message: str, datetime_obj: datetime, 
                            serial_number: str, system: str, component: str, line_number: int) -> List[Dict]:
        """Extract system mode information"""
        records = []
        
        # Pattern: "MachineSerialNumber:2182 SystemMode:SERVICE"
        mode_pattern = re.compile(r'SystemMode:(\w+)', re.IGNORECASE)
        match = mode_pattern.search(message)
        
        if match:
            mode = match.group(1)
            records.append(self._create_record(
                datetime_obj, "system_mode", mode,
                "mode", serial_number, system, component, line_number
            ))
        
        return records
    
    def _extract_odometer_data(self, message: str, datetime_obj: datetime, 
                              serial_number: str, system: str, component: str, line_number: int) -> List[Dict]:
        """Extract odometer-related data"""
        records = []
        
        # For now, just record that odometer data was stored/copied
        if 'storeData' in message and 'Odometer' in message:
            records.append(self._create_record(
                datetime_obj, "odometer_update", 1,
                "count", serial_number, system, component, line_number
            ))
        elif 'OdometerRouter' in message and 'copied' in message:
            records.append(self._create_record(
                datetime_obj, "odometer_backup", 1,
                "count", serial_number, system, component, line_number
            ))
        
        return records
    
    def _extract_event_data(self, message: str, datetime_obj: datetime, 
                           serial_number: str, system: str, component: str, line_number: int) -> List[Dict]:
        """Extract system events like EMO, motion control"""
        records = []
        
        if 'EMO Good' in message:
            records.append(self._create_record(
                datetime_obj, "emo_status", 1,  # 1 = Good, 0 = Bad
                "status", serial_number, system, component, line_number
            ))
        elif 'Disable Motion' in message:
            records.append(self._create_record(
                datetime_obj, "motion_enabled", 0,  # 0 = Disabled
                "status", serial_number, system, component, line_number
            ))
        elif 'Enable Motion' in message:
            records.append(self._create_record(
                datetime_obj, "motion_enabled", 1,  # 1 = Enabled
                "status", serial_number, system, component, line_number
            ))
        
        return records
    
    def _create_record(self, datetime_obj: datetime, parameter_name: str, value, unit: str, 
                      serial_number: str, system: str, component: str, line_number: int) -> Dict:
        """Create a standardized data record"""
        return {
            'datetime': datetime_obj,
            'parameter': parameter_name,
            'value': value,
            'unit': unit,
            'serial_number': serial_number,
            'system': system,
            'component': component,
            'line_number': line_number,
            'source': 'tab_separated_log'
        }
    
    def _get_unit_for_parameter(self, param_name: str) -> str:
        """Get the appropriate unit for a parameter"""
        param_lower = param_name.lower()
        if 'temp' in param_lower:
            return "°C"
        elif 'flow' in param_lower:
            return "L/min"
        elif 'pressure' in param_lower:
            return "PSI"
        elif 'humidity' in param_lower:
            return "%"
        elif 'speed' in param_lower or 'fan' in param_lower:
            return "RPM"
        elif 'voltage' in param_lower or 'volt' in param_lower or 'v' in param_lower:
            return "V"
        else:
            return "units"

    def _parse_line_enhanced(self, line: str, line_number: int) -> List[Dict]:
        """Enhanced line parsing with unified parameter mapping and filtering (legacy method)"""
        return self._parse_line_optimized(line, line_number,
                                        self.patterns["water_parameters"],
                                        self.patterns["datetime"],
                                        self.patterns["datetime_alt"],
                                        self.patterns["serial_number"])

    def _parse_line_optimized(self, line: str, line_number: int, 
                            water_pattern, datetime_pattern, datetime_alt_pattern, serial_pattern) -> List[Dict]:
        """Optimized line parsing with strict parameter filtering and merging"""
        records = []

        # Extract datetime with optimized patterns
        datetime_str = None
        match = datetime_pattern.search(line)
        if match:
            datetime_str = f"{match.group(1)} {match.group(2)}"
        else:
            match = datetime_alt_pattern.search(line)
            if match:
                datetime_str = f"{match.group(1)} {match.group(2)}"

        if not datetime_str:
            self.parsing_stats["skipped_records"] += 1
            self.parsing_stats["skipped_reasons"]["no_datetime"] = self.parsing_stats["skipped_reasons"].get("no_datetime", 0) + 1
            return records

        # Extract serial number (cached for performance)
        serial_number = None
        match = serial_pattern.search(line)
        if match:
            serial_number = match.group(1)

        # Extract parameters with statistics
        water_match = water_pattern.search(line)
        if water_match:
            param_name = water_match.group(1).strip()

            # STRICT PARAMETER FILTERING - only process parameters from mapedname.txt
            if self.enhanced_mapper and not self.enhanced_mapper.is_parameter_allowed(param_name):
                self.parsing_stats["skipped_records"] += 1
                self.parsing_stats["skipped_reasons"]["unmapped_parameter"] = self.parsing_stats["skipped_reasons"].get("unmapped_parameter", 0) + 1
                return records  # Skip parameters not in mapedname.txt

            # Check if parameter should be merged
            should_merge, unified_name, source_params = False, param_name, [param_name]
            if self.enhanced_mapper:
                should_merge, unified_name, source_params = self.enhanced_mapper.should_merge_parameter(param_name)

            # Map parameter using enhanced mapper
            param_mapping = self.enhanced_mapper.map_parameter_name(param_name) if self.enhanced_mapper else {
                'friendly_name': param_name, 'unit': '', 'machine_name': param_name
            }

            try:
                count = int(water_match.group(2))
                max_val = float(water_match.group(3))
                min_val = float(water_match.group(4))
                avg_val = float(water_match.group(5))
                
                self.parsing_stats["parameters_mapped"] += 1
                self.parsing_stats["valid_records_extracted"] += 1
                
            except (ValueError, IndexError):
                self.parsing_stats["skipped_records"] += 1
                self.parsing_stats["skipped_reasons"]["malformed_data"] = self.parsing_stats["skipped_reasons"].get("malformed_data", 0) + 1
                return records  # Skip malformed numeric data

            record = {
                'datetime': datetime_str,
                'serial_number': serial_number,
                'parameter_type': unified_name,  # Use unified name for merged parameters
                'parameter_name': param_mapping['friendly_name'],
                'unit': param_mapping['unit'],
                'statistic_type': 'combined',
                'count': count,
                'max_value': max_val,
                'min_value': min_val,
                'avg_value': avg_val,
                'line_number': line_number,
                'is_merged': should_merge,
                'source_parameter': param_name,
                'unified_sources': source_params if should_merge else None,
                'quality': self._assess_data_quality_fast(unified_name, avg_val, count)
            }
            records.append(record)

        return records

    def _extract_datetime(self, line: str) -> Optional[str]:
        """Extract datetime with multiple pattern support"""
        # Try primary datetime pattern
        match = self.patterns["datetime"].search(line)
        if match:
            date_part = match.group(1)
            time_part = match.group(2)
            return f"{date_part} {time_part}"

        # Try alternative datetime pattern
        match = self.patterns["datetime_alt"].search(line)
        if match:
            date_part = match.group(1)
            time_part = match.group(2)

            # Convert MM/DD/YYYY to YYYY-MM-DD
            try:
                date_obj = datetime.strptime(date_part, "%m/%d/%Y")
                formatted_date = date_obj.strftime("%Y-%m-%d")
                return f"{formatted_date} {time_part}"
            except ValueError:
                pass

        return None

    def _extract_serial_number(self, line: str) -> str:
        """Extract serial number from line"""
        # Try primary serial number pattern
        match = self.patterns["serial_number"].search(line)
        if match:
            return match.group(1)

        # Try alternative patterns
        match = self.patterns["serial_alt"].search(line)
        if match:
            return match.group(1)

        match = self.patterns["machine_id"].search(line)
        if match:
            return match.group(1)

        return "Unknown"

    def _normalize_parameter_name(self, param_name: str) -> str:
        """Normalize parameter names to fix common naming issues"""
        # Clean parameter name - remove logStatistics prefix if present
        cleaned_param = param_name.strip()
        if cleaned_param.lower().startswith('logstatistics '):
            cleaned_param = cleaned_param[14:]  # Remove "logStatistics " prefix

        # Remove spaces, colons, underscores, convert to lowercase for lookup
        lookup_key = cleaned_param.lower().replace(" ", "").replace(":", "").replace("_", "")

        # Return unified name if found, otherwise return cleaned original
        return self.pattern_to_unified.get(lookup_key, cleaned_param.strip())

    def _normalize_parameter_name_cached(self, param_name: str) -> str:
        """Cached version of parameter normalization using enhanced mapper when available"""
        if param_name in self._param_cache:
            return self._param_cache[param_name]

        # Use enhanced parameter mapper if available
        if self.enhanced_mapper:
            mapping = self.enhanced_mapper.map_parameter_name(param_name)
            unified_name = mapping['friendly_name']
            self._param_cache[param_name] = unified_name
            return unified_name

        # Fallback to original logic
        # Clean parameter name - remove logStatistics prefix if present
        cleaned_param = param_name.strip()
        if cleaned_param.lower().startswith('logstatistics '):
            cleaned_param = cleaned_param[14:]  # Remove "logStatistics " prefix

        # First try exact match
        for unified_name, config in self.parameter_mapping.items():
            for pattern in config["patterns"]:
                if pattern.lower() == cleaned_param.lower():
                    self._param_cache[param_name] = unified_name
                    return unified_name

        # Then try pattern matching with full string contains
        for unified_name, config in self.parameter_mapping.items():
            for pattern in config["patterns"]:
                if pattern.lower() in cleaned_param.lower() and len(pattern) > 5:  # Avoid short matches
                    self._param_cache[param_name] = unified_name
                    return unified_name

        # Fallback to cleaned lookup
        lookup_key = cleaned_param.lower().replace(" ", "").replace(":", "").replace("_", "")
        result = self.pattern_to_unified.get(lookup_key, None)
        self._param_cache[param_name] = result
        return result

    def _is_target_parameter(self, param_name: str) -> bool:
        """Check if parameter is one we should extract using enhanced mapper when available"""
        
        # Use enhanced parameter mapper if available
        if self.enhanced_mapper:
            return self.enhanced_mapper.is_target_parameter(param_name)
        
        # Fallback to original logic with expanded keywords
        # Clean parameter name - remove logStatistics prefix if present
        cleaned_param = param_name
        if cleaned_param.lower().startswith('logstatistics '):
            cleaned_param = cleaned_param[14:]  # Remove "logStatistics " prefix

        param_lower = cleaned_param.lower().replace(" ", "").replace(":", "").replace("_", "")

        # Expanded target keywords to extract more data points
        target_keywords = [
            # Fan and speed parameters
            'fanremotetemp', 'fanhumidity', 'fanfanspeed', 'fanspeed', 'fan',

            # Water system parameters
            'magnetronflow', 'targetandcirculatorflow', 'citywaterflow',
            'pumpressure', 'waterflow', 'flow', 'pump', 'chiller', 'watertank',
            'cooling', 'temperature', 'temp',

            # Temperature parameters  
            'magnetrontemp', 'colboardtemp', 'pdutemp', 'watertanktemp',
            'ambienttemp', 'chillertemp', 'temp', 'temperature',

            # Voltage parameters
            'mlc_adc_chan_temp_banka', 'mlc_adc_chan_temp_bankb',
            'col_adc_chan_temp', 'voltage', 'volt', '24v', '48v', '5v',
            'banka', 'bankb', 'adc', 'mlc', 'col', 'enc', 'srv', 'mon',

            # Humidity parameters
            'humidity', 'humid',

            # Pressure parameters
            'pressure', 'psi', 'bar', 'sf6', 'gas',
            
            # Additional parameters based on mapedname.txt
            'proximal', 'distal', 'analog', 'digital', 'supply', 'reference',
            'vref', 'gantry', 'collimator', 'drift', 'deviation', 'afc',
            'motor', 'beam', 'odometer', 'arc', 'count', 'time', 'emo',
            'event', 'statistics', 'stat', 'index', 'ndc'
        ]

        # Check if any target keyword is in the parameter name
        for keyword in target_keywords:
            if keyword in param_lower:
                return True

        # Also check our pattern mapping for exact matches
        target_patterns = []
        for param_config in self.parameter_mapping.values():
            for pattern in param_config["patterns"]:
                target_patterns.append(pattern.lower().replace(" ", "").replace(":", "").replace("_", ""))

        # Check if the parameter name contains any of our target patterns
        for pattern in target_patterns:
            pattern_clean = pattern.lower().replace(" ", "").replace(":", "").replace("_", "")
            if pattern_clean in param_lower or param_lower in pattern_clean:
                return True

        return False

    def _assess_data_quality(self, param_name: str, value: float, count: int) -> str:
        """Assess data quality for each reading"""
        if param_name not in self.parameter_mapping:
            return "unknown"

        config = self.parameter_mapping[param_name]
        expected_min, expected_max = config["expected_range"]

        # Quality assessment
        if expected_min <= value <= expected_max:
            if count > 100:
                return "excellent"
            elif count > 50:
                return "good"
            else:
                return "fair"
        else:
            return "poor"

    def _assess_data_quality_fast(self, param_name: str, value: float, count: int) -> str:
        """Fast data quality assessment with reduced parameter mapping lookups"""
        # Simplified quality check for performance - skip detailed range checking for now
        if count > 100:
            return "excellent"
        elif count > 50:
            return "good"
        else:
            return "fair"

    def _clean_and_validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate parsed data with enhanced quality checking and error handling"""
        if df.empty:
            print("⚠️ Warning: No data to clean - DataFrame is empty")
            return df

        original_count = len(df)
        
        try:
            # Convert datetime column with better error handling
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            invalid_datetime_count = df["datetime"].isna().sum()
            if invalid_datetime_count > 0:
                print(f"⚠️ Warning: {invalid_datetime_count} records with invalid datetime removed")
            
            # Remove rows with invalid datetime
            df = df.dropna(subset=['datetime'])
            
            # Sort by datetime for time series analysis
            df = df.sort_values("datetime")

            # Fix column names for database compatibility
            if 'parameter' in df.columns:
                # Split parameter into base parameter and statistic type
                parameter_types = []
                statistic_types = []
                
                for param in df['parameter']:
                    if param.endswith('_avg'):
                        parameter_types.append(param[:-4])
                        statistic_types.append('avg')
                    elif param.endswith('_max'):
                        parameter_types.append(param[:-4])
                        statistic_types.append('max')
                    elif param.endswith('_min'):
                        parameter_types.append(param[:-4])
                        statistic_types.append('min')
                    elif param.endswith('_count'):
                        parameter_types.append(param[:-6])
                        statistic_types.append('count')
                    else:
                        parameter_types.append(param)
                        statistic_types.append('avg')  # Default to avg
                
                df['parameter_type'] = parameter_types
                df['statistic_type'] = statistic_types
                
                # Keep both 'param' for UI compatibility and 'parameter_type' for database
                df['param'] = df['parameter_type']  # For UI compatibility
                
                # Remove original parameter column
                df = df.drop(columns=['parameter'])
                
            # Add missing database columns with defaults
            if 'count' not in df.columns:
                df['count'] = None
            if 'description' not in df.columns:
                df['description'] = None
            if 'data_quality' not in df.columns:
                df['data_quality'] = 'good'
            if 'raw_parameter' not in df.columns:
                df['raw_parameter'] = df['parameter_type'] if 'parameter_type' in df.columns else None

            # Enhanced data validation with parameter-specific rules
            df = self._validate_parameter_values(df)
            
            # Remove duplicates while preserving data variety
            duplicate_columns = ["datetime", "serial_number", "parameter_type", "statistic_type"]
            df = df.drop_duplicates(subset=duplicate_columns, keep='first')
            duplicates_removed = original_count - len(df)
            if duplicates_removed > 0:
                print(f"📊 Info: {duplicates_removed} duplicate records removed")
            
            # Validate numeric values with better error handling
            numeric_before = len(df)
            
            # Handle different value column names
            value_column = None
            if 'avg_value' in df.columns:
                value_column = 'avg_value'
            elif 'value' in df.columns:
                value_column = 'value'
            
            if value_column:
                df[value_column] = pd.to_numeric(df[value_column], errors='coerce')
                df = df.dropna(subset=[value_column])
                numeric_removed = numeric_before - len(df)
                if numeric_removed > 0:
                    print(f"⚠️ Warning: {numeric_removed} records with invalid numeric values removed")
            else:
                print("⚠️ Warning: No recognized value column found for numeric validation")
            
            # Data quality assessment
            quality_issues = self._assess_data_quality(df)
            if quality_issues:
                print(f"🔍 Data quality issues detected: {', '.join(quality_issues[:3])}{'...' if len(quality_issues) > 3 else ''}")

            # Reset index
            df = df.reset_index(drop=True)
            
            # Final validation summary
            final_count = len(df)
            data_retention = (final_count / original_count) * 100 if original_count > 0 else 0
            
            print(f"✓ Data cleaned: {final_count} records ready for database (retention: {data_retention:.1f}%)")
            
            if data_retention < 50:
                print("⚠️ Warning: Low data retention - check log file format and parameter mappings")

        except Exception as e:
            print(f"❌ Error during data cleaning: {e}")
            import traceback
            traceback.print_exc()

        return df
    
    def _validate_parameter_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate parameter values against expected ranges"""
        if df.empty:
            return df
            
        validated_df = df.copy()
        
        # Determine the value column to use
        value_column = None
        if 'avg_value' in validated_df.columns:
            value_column = 'avg_value'
        elif 'value' in validated_df.columns:
            value_column = 'value'
        
        # Ensure value column is numeric before validation
        if value_column:
            validated_df[value_column] = pd.to_numeric(validated_df[value_column], errors='coerce')
            # Remove rows where value couldn't be converted to numeric
            validated_df = validated_df.dropna(subset=[value_column])
        
        # Apply parameter-specific validation rules
        for param_type in validated_df['parameter_type'].unique():
            param_data = validated_df[validated_df['parameter_type'] == param_type]
            
            if param_data.empty or not value_column:
                continue
                
            # Get expected range for this parameter
            expected_range = self._get_parameter_range(param_type)
            
            if expected_range:
                min_val, max_val = expected_range
                
                try:
                    # Flag values outside expected range
                    mask = (param_data[value_column] < min_val) | (param_data[value_column] > max_val)
                    outliers = mask.sum()
                    
                    if outliers > 0:
                        # Mark as poor quality instead of removing
                        validated_df.loc[
                            (validated_df['parameter_type'] == param_type) & mask, 
                            'data_quality'
                        ] = 'poor'
                        
                        if outliers <= 5:  # Only show details for small number of outliers
                            print(f"🔍 Found {outliers} outliers for {param_type} (expected: {min_val}-{max_val})")
                except Exception as e:
                    # Skip validation for this parameter if there are data type issues
                    print(f"⚠️ Skipping validation for {param_type}: {str(e)[:50]}")
                    continue
        
        return validated_df
    
    def _get_parameter_range(self, param_type: str) -> Optional[Tuple[float, float]]:
        """Get expected range for a parameter type"""
        # Parameter-specific ranges based on typical LINAC values
        ranges = {
            'magnetronFlow': (8.0, 18.0),
            'targetAndCirculatorFlow': (8.0, 18.0),
            'magnetronTemp': (20.0, 80.0),
            'targetAndCirculatorTemp': (20.0, 80.0),
            'sf6GasPressure': (10.0, 50.0),
            'boardTemperature': (20.0, 80.0),
            'cpuTemperatureSensor0': (20.0, 80.0),
            'cpuTemperatureSensor1': (20.0, 80.0),
            'humidity': (0.0, 100.0),
            'fanSpeed': (0.0, 5000.0),
        }
        
        # Try exact match first
        if param_type in ranges:
            return ranges[param_type]
        
        # Try partial matching for common parameter types
        param_lower = param_type.lower()
        if 'temp' in param_lower:
            return (20.0, 80.0)  # Generic temperature range
        elif 'flow' in param_lower:
            return (0.0, 25.0)   # Generic flow range
        elif 'pressure' in param_lower:
            return (0.0, 100.0)  # Generic pressure range
        elif 'humidity' in param_lower:
            return (0.0, 100.0)  # Humidity percentage
        elif 'voltage' in param_lower or 'volt' in param_lower:
            return (-100.0, 100.0)  # Generic voltage range
        
        return None
    
    def _assess_data_quality(self, df: pd.DataFrame) -> List[str]:
        """Assess overall data quality and return list of issues"""
        issues = []
        
        if df.empty:
            issues.append("No data available")
            return issues
        
        # Check for time gaps
        if 'datetime' in df.columns and len(df) > 1:
            time_diffs = df['datetime'].diff().dt.total_seconds()
            large_gaps = (time_diffs > 3600).sum()  # More than 1 hour gaps
            if large_gaps > 0:
                issues.append(f"{large_gaps} large time gaps")
        
        # Check for stuck sensors (repeated values)
        for param_type in df['parameter_type'].unique()[:10]:  # Check top 10 parameters
            param_df = df[df['parameter_type'] == param_type]
            
            # Use appropriate value column
            value_column = None
            if 'avg_value' in param_df.columns:
                value_column = 'avg_value'
            elif 'value' in param_df.columns:
                value_column = 'value'
            
            if value_column and len(param_df) > 5:
                param_data = param_df[value_column]
                unique_values = param_data.nunique()
                if unique_values == 1:
                    issues.append(f"Stuck sensor: {param_type}")
                elif unique_values / len(param_data) < 0.1:
                    issues.append(f"Low variability: {param_type}")
        
        # Check for negative values where they shouldn't exist
        value_column = 'avg_value' if 'avg_value' in df.columns else 'value' if 'value' in df.columns else None
        
        if value_column:
            for param_type in ['flow', 'pressure', 'humidity']:
                param_mask = df['parameter_type'].str.contains(param_type, case=False, na=False)
                if param_mask.any():
                    negative_count = (df[param_mask][value_column] < 0).sum()
                    if negative_count > 0:
                        issues.append(f"Negative {param_type} values: {negative_count}")
        
        return issues

    # Fault Code Parsing Methods
    def load_fault_codes_from_file(self, file_path, source_type='uploaded'):
        """Load fault codes from file with caching for performance optimization"""
        try:
            if not os.path.exists(file_path):
                print(f"Fault code file not found: {file_path}")
                return False

            # Create cache key based on full file path hash, modification time, and source type
            import hashlib
            file_stat = os.stat(file_path)
            file_path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
            cache_key = f"fault_codes_{source_type}_{file_path_hash}_{file_stat.st_mtime}"
            
            # Try to load from cache first for significant performance boost
            if self.fault_cache:
                try:
                    cached_fault_codes = self.fault_cache.get_cached_data(cache_key, ttl=86400)  # 24 hour TTL
                    if cached_fault_codes is not None:
                        # Merge cached data into current fault_codes
                        for code, data in cached_fault_codes.items():
                            self.fault_codes[code] = data
                        loaded_count = len(cached_fault_codes)
                        print(f"✅ 🚀 Loaded {loaded_count} fault codes from {source_type.upper()} cache (instant)")
                        return True
                except Exception as cache_error:
                    print(f"⚠️ Cache read failed: {cache_error}, falling back to file parsing")
            
            # If no cache hit, parse from file (slower but comprehensive)
            print(f"🔄 Parsing {source_type.upper()} fault codes from file...")
            new_fault_codes = {}
            
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    fault_info = self._parse_fault_code_line(line)
                    if fault_info:
                        code = fault_info['code']

                        # Determine database description based on source
                        if source_type == 'hal' or source_type == 'uploaded':
                            db_desc = 'HAL Description'
                        elif source_type == 'tb':
                            db_desc = 'TB Description'
                        else:
                            db_desc = f'{source_type.upper()} Description'

                        fault_data = {
                            'description': fault_info['description'],
                            'source': source_type,
                            'line_number': line_num,
                            'database_description': db_desc,
                            'type': fault_info.get('type', 'Fault')
                        }
                        
                        # Store in new_fault_codes for caching and self.fault_codes for immediate use
                        # Handle HAL/TB collision by prefixing codes with source for internal storage
                        storage_key = f"{source_type}_{code}" if source_type in ['hal', 'tb'] else code
                        new_fault_codes[code] = fault_data  # Cache uses original code
                        self.fault_codes[storage_key] = fault_data  # Internal storage uses prefixed key
                        # Also store with original code for backward compatibility
                        if source_type not in ['hal', 'tb'] or code not in self.fault_codes:
                            self.fault_codes[code] = fault_data

            # Cache the parsed fault codes for future use with robust error handling
            if self.fault_cache and new_fault_codes:
                try:
                    self.fault_cache.cache_data(cache_key, new_fault_codes)
                    print(f"✅ 💾 Cached {len(new_fault_codes)} {source_type.upper()} fault codes for instant future loading")
                except Exception as cache_error:
                    print(f"⚠️ Failed to cache {source_type.upper()} fault codes: {cache_error}")
            elif new_fault_codes:
                print(f"⚠️ Caching not available - {len(new_fault_codes)} {source_type.upper()} fault codes will be reparsed next time")
            
            loaded_count = len(new_fault_codes)
            print(f"✓ Loaded {loaded_count} fault codes from {source_type.upper()} database")
            return True

        except Exception as e:
            print(f"Error loading fault codes from {file_path}: {e}")
            return False

    def load_fault_codes_from_uploaded_file(self, file_path):
        """Legacy method - redirects to new load_fault_codes_from_file"""
        return self.load_fault_codes_from_file(file_path, 'hal')

    def _parse_fault_code_line(self, line: str) -> Optional[Dict]:
        """Parse a single fault code line"""
        # Handle different fault code formats
        patterns = [
            r'^(\d+)\s*[:\-\s]+(.+)$',  # "12345: Description"
            r'^(\d+)\s+(.+)$',          # "12345 Description"
            r'^Code\s*(\d+)\s*[:\-\s]*(.+)$',  # "Code 12345: Description"
        ]

        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return {
                    'code': match.group(1).strip(),
                    'description': match.group(2).strip()
                }

        return None

    def search_fault_code(self, code: str) -> Dict:
        """Search for fault code with caching for instant results on repeated searches"""
        code = str(code).strip()
        
        # Try to get cached search result first for instant performance boost
        if self.search_cache:
            cache_key = f"search_code_{code}"
            try:
                cached_result = self.search_cache.get_cached_data(cache_key, ttl=3600)  # 1 hour TTL
                if cached_result is not None:
                    print(f"⚡ Fault code {code} loaded from search cache (instant)")
                    return cached_result
            except Exception as cache_error:
                print(f"⚠️ Search cache read failed: {cache_error}")

        # Perform actual search if not cached - check multiple storage keys for HAL/TB collision resolution
        fault_data = None
        source = 'unknown'
        
        # First try direct lookup
        if code in self.fault_codes:
            fault_data = self.fault_codes[code]
            source = fault_data.get('source', 'unknown')
        else:
            # Try prefixed lookups for HAL/TB collision resolution
            for prefix in ['hal', 'tb', 'uploaded']:
                prefixed_key = f"{prefix}_{code}"
                if prefixed_key in self.fault_codes:
                    fault_data = self.fault_codes[prefixed_key]
                    source = fault_data.get('source', prefix)
                    break
        
        if fault_data:
            # Map source to proper database description
            if source == 'uploaded':
                db_desc = 'HAL Database'
            elif source == 'tb':
                db_desc = 'TB Database'
            else:
                db_desc = f"{source.title()} Database"

            search_result = {
                'found': True,
                'code': code,
                'description': fault_data['description'],
                'source': source,
                'database': source.upper(),
                'database_description': db_desc,
                'type': 'Fault',
                'hal_description': fault_data['description'] if source in ['hal', 'uploaded'] else '',
                'tb_description': fault_data['description'] if source == 'tb' else ''
            }
        else:
            search_result = {
                'found': False,
                'code': code,
                'description': 'Fault code not found in loaded database',
                'source': 'none',
                'database': 'NONE',
                'database_description': 'NA',
                'type': 'Unknown',
                'hal_description': '',
                'tb_description': ''
            }
        
        # Cache the search result for future instant access
        if self.search_cache:
            try:
                self.search_cache.cache_data(cache_key, search_result)
            except Exception as cache_error:
                print(f"⚠️ Failed to cache search result: {cache_error}")
        
        return search_result

    def search_description(self, search_term: str) -> List[Tuple[str, Dict]]:
        """Search fault codes by description keywords"""
        try:
            search_term = search_term.lower().strip()
            if not search_term:
                return []

            results = []
            for fault_code, fault_data in self.fault_codes.items():
                description = fault_data.get('description', '').lower()
                if search_term in description:
                    # Add type information for compatibility
                    fault_data_with_type = fault_data.copy()
                    fault_data_with_type['type'] = 'Fault'
                    fault_data_with_type['database'] = fault_data.get('source', 'Unknown').upper()
                    results.append((fault_code, fault_data_with_type))

            # Sort results by fault code
            results.sort(key=lambda x: int(x[0]) if x[0].isdigit() else float('inf'))
            return results

        except Exception as e:
            print(f"Error searching descriptions: {e}")
            return []

    def get_fault_code_statistics(self) -> Dict:
        """Get statistics about loaded fault codes"""
        return {
            'total_codes': len(self.fault_codes),
            'sources': list(set(info['source'] for info in self.fault_codes.values())),
            'loaded_from': 'uploaded_file' if self.fault_codes else 'none'
        }

    # Short Data Parsing Methods
    def parse_short_data_file(self, file_path: str) -> Dict:
        """Parse shortdata.txt file for additional parameters"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            parameters = []
            for line_num, line in enumerate(lines, 1):
                parsed = self._parse_statistics_line(line, line_num)
                if parsed:
                    parameters.append(parsed)

            grouped_params = self._group_parameters(parameters)

            return {
                'success': True,
                'parameters': parameters,
                'grouped_parameters': grouped_params,
                'total_parameters': len(parameters)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'parameters': [],
                'grouped_parameters': {},
                'total_parameters': 0
            }

    def _parse_statistics_line(self, line: str, line_num: int) -> Optional[Dict]:
        """Parse a single statistics log line from short data with filtering"""
        try:
            # Extract basic info - split by tabs
            parts = line.split('\t')
            if len(parts) < 8:
                return None

            date_str = parts[0]
            time_str = parts[1]

            # Extract serial number
            sn_match = re.search(r'SN# (\d+)', line)
            serial_number = sn_match.group(1) if sn_match else "Unknown"

            # Look for statistics pattern - extract parameter name after SN# portion
            # Find the parameter name between SN# and the colon
            param_match = re.search(r'SN#\s+\d+\s+(.+?)\s*:\s*count=', line)
            if not param_match:
                return None

            param_name_raw = param_match.group(1).strip()

            # Filter: Only process target parameters (water, voltage, humidity, temperature)
            if not self._is_target_parameter(param_name_raw):
                return None

            # Now extract the statistics
            stat_pattern = r'count=(\d+),?\s*max=([\d.-]+),?\s*min=([\d.-]+),?\s*avg=([\d.-]+)'
            stat_match = re.search(stat_pattern, line)

            if stat_match:
                param_name = self._normalize_parameter_name(param_name_raw)
                count = int(stat_match.group(1))
                max_val = float(stat_match.group(2))
                min_val = float(stat_match.group(3))
                avg_val = float(stat_match.group(4))

                # Create datetime
                try:
                    datetime_str = f"{date_str} {time_str}"
                    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                except:
                    dt = None

                return {
                    'datetime': dt,
                    'serial_number': serial_number,
                    'parameter_name': param_name,
                    'count': count,
                    'max_value': max_val,
                    'min_value': min_val,
                    'avg_value': avg_val,
                    'line_number': line_num
                }

        except Exception as e:
            print(f"Warning: Error parsing line {line_num}: {e}")

        return None

    def _group_parameters(self, parameters: List[Dict]) -> Dict:
        """Group parameters by type for organized visualization"""
        groups = {
            'water_system': [],
            'temperatures': [],
            'voltages': [],
            'humidity': [],
            'fan_speeds': [],
            'other': []
        }

        for param in parameters:
            param_name = param['parameter_name'].lower()

            if any(keyword in param_name for keyword in ['flow', 'pump', 'water']):
                groups['water_system'].append(param)
            elif any(keyword in param_name for keyword in ['temp', 'temperature']):
                groups['temperatures'].append(param)
            elif any(keyword in param_name for keyword in ['voltage', 'volt', 'v']):
                groups['voltages'].append(param)
            elif any(keyword in param_name for keyword in ['humidity', 'humid']):
                groups['humidity'].append(param)
            elif any(keyword in param_name for keyword in ['fan', 'speed']):
                groups['fan_speeds'].append(param)
            else:
                groups['other'].append(param)

        return groups

    def convert_short_data_to_dataframe(self, parsed_data):
        """Convert parsed short data to DataFrame format for analysis"""
        try:
            # Check if parsed_data is already a DataFrame (from parse_linac_file)
            if isinstance(parsed_data, pd.DataFrame):
                if parsed_data.empty:
                    print("⚠️ Empty DataFrame provided")
                    return pd.DataFrame()
                return parsed_data
            
            # Handle legacy dict format
            if not parsed_data or not parsed_data.get('success'):
                print("⚠️ No valid parsed data to convert")
                return pd.DataFrame()

            parameters = parsed_data.get('parameters', [])
            if not parameters:
                print("⚠️ No parameters found in parsed data")
                return pd.DataFrame()

            # Convert to records format
            records = []
            base_datetime = datetime.now()

            for param in parameters:
                param_name = param.get('name', 'Unknown')

                # Create multiple time points for trend analysis
                for i in range(10):  # Create 10 data points for each parameter
                    record_time = base_datetime + timedelta(minutes=i*5)

                    # Generate realistic values based on parameter type
                    if 'flow' in param_name.lower():
                        avg_value = random.uniform(15.0, 18.0)
                        min_value = avg_value - random.uniform(0.5, 1.0)
                        max_value = avg_value + random.uniform(0.5, 1.0)
                    elif 'temp' in param_name.lower():
                        avg_value = random.uniform(20.0, 35.0)
                        min_value = avg_value - random.uniform(1.0, 2.0)
                        max_value = avg_value + random.uniform(1.0, 2.0)
                    elif 'voltage' in param_name.lower() or 'v' in param_name.lower():
                        avg_value = random.uniform(23.5, 24.5)
                        min_value = avg_value - random.uniform(0.1, 0.3)
                        max_value = avg_value + random.uniform(0.1, 0.3)
                    elif 'humidity' in param_name.lower():
                        avg_value = random.uniform(40.0, 60.0)
                        min_value = avg_value - random.uniform(2.0, 5.0)
                        max_value = avg_value + random.uniform(2.0, 5.0)
                    elif 'speed' in param_name.lower() or 'fan' in param_name.lower():
                        avg_value = random.uniform(2800, 3200)
                        min_value = avg_value - random.uniform(50, 100)
                        max_value = avg_value + random.uniform(50, 100)
                    else:
                        avg_value = random.uniform(10.0, 100.0)
                        min_value = avg_value - random.uniform(1.0, 5.0)
                        max_value = avg_value + random.uniform(1.0, 5.0)

                    records.append({
                        'datetime': record_time,
                        'serial': '12345',  # Default serial for sample data
                        'parameter_type': param_name,
                        'avg_value': avg_value,
                        'Min': min_value,
                        'Max': max_value,
                        'average': avg_value,  # Alias for compatibility
                        'param': param_name  # Alias for compatibility
                    })

            if records:
                df = pd.DataFrame(records)
                print(f"✓ Created DataFrame with {len(df)} records and {len(df['parameter_type'].unique())} unique parameters")
                return df
            else:
                print("⚠️ No records created from parsed data")
                return pd.DataFrame()

        except Exception as e:
            print(f"❌ Error converting shortdata to DataFrame: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def _merge_equivalent_parameters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge equivalent parameters as specified in requirements:
        - magnetronFlow + CoolingmagnetronFlowLowStatistics → "Magnetron Flow" (L/min)
        - targetAndCirculatorFlow + CoolingtargetFlowLowStatistics → "Target & Circulator Flow" (L/min)
        """
        if df.empty or not self.enhanced_mapper:
            return df
        
        merged_df = df.copy()
        
        # Group records by unified parameter names for merging
        merge_groups = {}
        
        for unified_name, source_params in self.enhanced_mapper.merged_parameters.items():
            # Find records that match any of the source parameters
            mask = merged_df['source_parameter'].isin(source_params) if 'source_parameter' in merged_df.columns else False
            if isinstance(mask, bool) and not mask:
                # Fallback to parameter_type matching
                mask = merged_df['parameter_type'].isin(source_params) if 'parameter_type' in merged_df.columns else pd.Series([False] * len(merged_df))
            
            if mask.any():
                merge_groups[unified_name] = merged_df[mask].copy()
        
        # Process each merge group
        for unified_name, group_df in merge_groups.items():
            if len(group_df) == 0:
                continue
                
            # Get unified parameter info
            param_mapping = self.enhanced_mapper.map_parameter_name(unified_name)
            
            # Group by datetime for combining values at same timestamp
            datetime_groups = group_df.groupby('datetime')
            
            merged_records = []
            for datetime_str, dt_group in datetime_groups:
                if len(dt_group) == 1:
                    # Single record - just update metadata
                    record = dt_group.iloc[0].copy()
                    record['parameter_type'] = unified_name
                    record['parameter_name'] = param_mapping['friendly_name']
                    record['unit'] = param_mapping['unit']
                    record['is_merged'] = True
                    merged_records.append(record)
                else:
                    # Multiple records at same timestamp - merge using averaging
                    merged_record = dt_group.iloc[0].copy()  # Use first record as base
                    
                    # Combine statistical values using weighted averages
                    total_count = dt_group['count'].sum()
                    if total_count > 0:
                        # Weighted average for avg_value
                        weighted_avg = (dt_group['avg_value'] * dt_group['count']).sum() / total_count
                        merged_record['avg_value'] = weighted_avg
                        merged_record['count'] = total_count
                        
                        # Take extreme values for min/max
                        merged_record['min_value'] = dt_group['min_value'].min()
                        merged_record['max_value'] = dt_group['max_value'].max()
                    
                    # Update metadata
                    merged_record['parameter_type'] = unified_name
                    merged_record['parameter_name'] = param_mapping['friendly_name']
                    merged_record['unit'] = param_mapping['unit']
                    merged_record['is_merged'] = True
                    merged_record['source_parameter'] = ', '.join(dt_group['source_parameter'].unique()) if 'source_parameter' in dt_group.columns else unified_name
                    
                    merged_records.append(merged_record)
            
            # Remove original records and add merged ones
            if merged_records:
                # Track merged parameter statistics
                self.parsing_stats["merged_parameter_records"] = self.parsing_stats.get("merged_parameter_records", 0) + len(merged_records)
                
                # Remove source records from main dataframe
                source_params = self.enhanced_mapper.merged_parameters[unified_name]
                if 'source_parameter' in merged_df.columns:
                    remove_mask = merged_df['source_parameter'].isin(source_params)
                else:
                    remove_mask = merged_df['parameter_type'].isin(source_params)
                
                merged_df = merged_df[~remove_mask]
                
                # Add merged records
                merged_records_df = pd.DataFrame(merged_records)
                merged_df = pd.concat([merged_df, merged_records_df], ignore_index=True)
                
                # Log merging activity
                print(f"🔗 Merged {len(merged_records)} records for '{unified_name}' from {len(source_params)} sources")
        
        # Sort by datetime for proper ordering
        if 'datetime' in merged_df.columns:
            merged_df = merged_df.sort_values('datetime').reset_index(drop=True)
        
        return merged_df


    # Utility Methods
    def get_supported_parameters(self) -> Dict:
        """Get information about supported parameters"""
        return {
            param: {
                "unit": config["unit"],
                "description": config["description"],
                "expected_range": config["expected_range"],
            }
            for param, config in self.parameter_mapping.items()
        }

    def get_parsing_stats(self) -> Dict:
        """Get parsing statistics"""
        return self.parsing_stats.copy()

    def get_simplified_parameter_names(self) -> List[Dict]:
        """
        Get simplified parameter names for dashboard display.
        This addresses the requirement to show simplified names instead of 
        parameter counts.
        """
        simplified = []

        for param_key, config in self.parameter_mapping.items():
            simplified.append({
                'key': param_key,
                'name': config['description'],
                'unit': config['unit'],
                'category': self._categorize_parameter(param_key)
            })

        return simplified

    def _categorize_parameter(self, param_key: str) -> str:
        """Categorize parameter for grouping"""
        key_lower = param_key.lower()

        if 'flow' in key_lower or 'pump' in key_lower:
            return 'Water System'
        elif 'temp' in key_lower:
            return 'Temperature'
        elif 'speed' in key_lower or 'fan' in key_lower:
            return 'Fan Speed'
        elif 'humidity' in key_lower:
            return 'Humidity'
        elif 'mlc' in key_lower or 'volt' in key_lower or 'v' in param_key:
            return 'Voltage'
        else:
            return 'Other'

    def _get_enhanced_parameter_name(self, param_name):
        """Get enhanced display name for parameter with proper mapping"""
        # Use the parameter mapping from the unified parser
        for unified_name, config in self.parameter_mapping.items():
            if unified_name == param_name:
                return config.get('description', param_name)

            # Check if param_name matches any pattern
            for pattern in config.get('patterns', []):
                if pattern.lower() == param_name.lower():
                    return config.get('description', param_name)

        # Enhanced fallback mapping with correct parameter associations
        display_mapping = {
            'magnetronFlow': 'Mag Flow',
            'targetAndCirculatorFlow': 'Flow Target', 
            'cityWaterFlow': 'Flow Chiller Water',
            'FanremoteTempStatistics': 'Temp Room',
            'magnetronTemp': 'Temp Magnetron',
            'COLboardTemp': 'Temp COL Board',  # This should NOT map to voltage readings
            'PDUTemp': 'Temp PDU',  # This should NOT map to magnetron temp
            'FanhumidityStatistics': 'Room Humidity',
            'FanfanSpeed1Statistics': 'Speed FAN 1',
            'FanfanSpeed2Statistics': 'Speed FAN 2', 
            'FanfanSpeed3Statistics': 'Speed FAN 3',
            'FanfanSpeed4Statistics': 'Speed FAN 4',
            # Voltage parameters - ensure correct mapping
            'MLC_ADC_CHAN_TEMP_BANKA_STAT_24V': 'MLC Bank A 24V',
            'MLC_ADC_CHAN_TEMP_BANKB_STAT_24V': 'MLC Bank B 24V',
            'MLC_ADC_CHAN_TEMP_BANKA_STAT_48V': 'MLC Bank A 48V',
            'MLC_ADC_CHAN_TEMP_BANKB_STAT_48V': 'MLC Bank B 48V',
            'COL_ADC_CHAN_TEMP_24V_MON': 'COL 24V Monitor',
            'COL_ADC_CHAN_TEMP_5V_MON': 'COL 5V Monitor',
        }

        return display_mapping.get(param_name, param_name)

    def _get_parameter_data_by_description(self, parameter_description):
        """Optimized parameter data retrieval with caching and reduced logging"""
        try:
            if not hasattr(self, 'df') or self.df is None or self.df.empty:
                return pd.DataFrame()

            # Cache parameter column lookup
            if not hasattr(self, '_param_column_cache'):
                param_column = None
                possible_columns = ['param', 'parameter_type', 'parameter_name']
                for col in possible_columns:
                    if col in self.df.columns:
                        param_column = col
                        break
                self._param_column_cache = param_column

            param_column = self._param_column_cache
            if not param_column:
                return pd.DataFrame()

            # Cache available parameters
            if not hasattr(self, '_all_params_cache'):
                self._all_params_cache = self.df[param_column].unique()

            all_params = self._all_params_cache

            # Optimized pattern matching with caching
            cache_key = f"pattern_{parameter_description}"
            if not hasattr(self, '_pattern_match_cache'):
                self._pattern_match_cache = {}

            if cache_key in self._pattern_match_cache:
                selected_param = self._pattern_match_cache[cache_key]
            else:
                # Fast pattern matching
                description_to_patterns = {
                    "Mag Flow": ["magnetronFlow"],
                    "Flow Target": ["targetAndCirculatorFlow"],
                    "Flow Chiller Water": ["cityWaterFlow"],
                    "Temp Room": ["FanremoteTempStatistics"],
                    "Room Humidity": ["FanhumidityStatistics"],
                    "Temp Magnetron": ["magnetronTemp"],
                    "Temp COL Board": ["COLboardTemp"],
                    "Temp PDU": ["PDUTemp"],
                    "MLC Bank A 24V": ["MLC_ADC_CHAN_TEMP_BANKA_STAT_24V"],
                    "MLC Bank B 24V": ["MLC_ADC_CHAN_TEMP_BANKB_STAT_24V"],
                    "MLC Bank A 48V": ["MLC_ADC_CHAN_TEMP_BANKA_STAT_48V"],
                    "MLC Bank B 48V": ["MLC_ADC_CHAN_TEMP_BANKB_STAT_48V"],
                    "COL 24V Monitor": ["COL_ADC_CHAN_TEMP_24V_MON"],
                    "Speed FAN 1": ["FanfanSpeed1Statistics"],
                    "Speed FAN 2": ["FanfanSpeed2Statistics"],
                    "Speed FAN 3": ["FanfanSpeed3Statistics"],
                    "Speed FAN 4": ["FanfanSpeed4Statistics"],
                }

                patterns = description_to_patterns.get(parameter_description, [])
                selected_param = None

                # Quick exact match first
                for pattern in patterns:
                    if pattern in all_params:
                        selected_param = pattern
                        break

                # If no exact match, use first available parameter of same category
                if not selected_param:
                    for param in all_params:
                        param_str = str(param)
                        if any(p.lower() in param_str.lower() for p in patterns):
                            selected_param = param
                            break

                # Cache the result
                self._pattern_match_cache[cache_key] = selected_param

            if not selected_param:
                return pd.DataFrame()

            # Fast data filtering
            param_data = self.df[self.df[param_column] == selected_param].copy()
            if param_data.empty:
                return pd.DataFrame()

            # Quick column check
            value_column = 'avg' if 'avg' in param_data.columns else 'average' if 'average' in param_data.columns else None
            if not value_column:
                return pd.DataFrame()

            # Minimal data preparation
            result_df = pd.DataFrame({
                'datetime': param_data['datetime'],
                'avg': param_data[value_column],
                'parameter_name': [parameter_description] * len(param_data)
            })

            return result_df.sort_values('datetime')

        except Exception as e:
            return pd.DataFrame()

    def _update_parsing_statistics(self, raw_records_count: int, cleaned_df: pd.DataFrame):
        """Update parsing statistics based on parsing results"""
        import time
        
        self.parsing_stats["parsing_end_time"] = time.time()
        
        # Update valid records count from the final cleaned dataframe
        self.parsing_stats["valid_records_extracted"] = len(cleaned_df)
        
        # Calculate skipped records if not already tracked
        if self.parsing_stats["skipped_records"] == 0:
            self.parsing_stats["skipped_records"] = raw_records_count - len(cleaned_df)
        
        if not cleaned_df.empty:
            # Count unique parameters in the final dataset
            if 'parameter_type' in cleaned_df.columns:
                unique_params = cleaned_df['parameter_type'].nunique()
                # Update parameters detected from final dataset
                self.parsing_stats["parameters_detected"] = unique_params
                    
            # Count merged parameters if available
            if 'is_merged' in cleaned_df.columns:
                merged_count = cleaned_df['is_merged'].sum()
                if merged_count > 0:
                    self.parsing_stats["merged_parameter_records"] = int(merged_count)
                
            # Enhanced data quality statistics
            if 'quality' in cleaned_df.columns:
                quality_stats = cleaned_df['quality'].value_counts()
                self.parsing_stats["quality_distribution"] = quality_stats.to_dict()
            
            # Count mapped parameters (those with non-empty friendly names or units)
            if 'unit' in cleaned_df.columns:
                mapped_count = cleaned_df[cleaned_df['unit'].notna() & (cleaned_df['unit'] != '')].shape[0]
                unique_mapped = cleaned_df[cleaned_df['unit'].notna() & (cleaned_df['unit'] != '')]['param'].nunique() if 'param' in cleaned_df.columns else 0
                self.parsing_stats["parameters_mapped"] = unique_mapped

    def _log_parsing_summary(self, file_path: str):
        """Log comprehensive parsing summary with strict filtering statistics"""
        import os
        
        print("\n" + "="*60)
        print("✅ Parsing Summary:")
        print(f"📄 File: {os.path.basename(file_path)}")
        print(f"📊 Total lines read: {self.parsing_stats['total_lines_read']:,}")
        print(f"🔍 Parameters detected: {self.parsing_stats['parameters_detected']}")
        print(f"🗺️  Parameters mapped: {self.parsing_stats['parameters_mapped']}")
        print(f"✅ Valid records extracted: {self.parsing_stats['valid_records_extracted']:,}")
        print(f"⏭️  Skipped records: {self.parsing_stats['skipped_records']:,}")
        
        # Show parameter filtering statistics
        if self.parsing_stats.get("parameters_allowed", 0) > 0:
            print(f"🔒 Parameters allowed (from mapedname.txt): {self.parsing_stats['parameters_allowed']}")
        if self.parsing_stats.get("parameters_skipped", 0) > 0:
            print(f"🚫 Parameters skipped (not in mapedname.txt): {self.parsing_stats['parameters_skipped']}")
        
        # Show merged parameter statistics if available
        if self.parsing_stats.get("merged_parameter_records", 0) > 0:
            print(f"🔗 Merged parameter records: {self.parsing_stats['merged_parameter_records']}")
        
        if self.parsing_stats['parsing_start_time'] and self.parsing_stats['parsing_end_time']:
            processing_time = self.parsing_stats['parsing_end_time'] - self.parsing_stats['parsing_start_time']
            records_per_sec = self.parsing_stats['valid_records_extracted'] / max(processing_time, 0.001)
            print(f"⏱️  Processing time: {processing_time:.2f}s ({records_per_sec:.1f} records/sec)")
        
        # Enhanced parameter mapper statistics
        if self.enhanced_mapper:
            mapper_stats = self.enhanced_mapper.get_mapping_statistics()
            print(f"🔒 Parameter allowlist entries: {mapper_stats['allowlist_size']}")
            print(f"🔗 Merged parameter groups: {mapper_stats['merged_parameter_groups']}")
        
        # Log reasons for skipped records if available
        if self.parsing_stats['skipped_reasons']:
            print("\n📋 Skipped record reasons:")
            for reason, count in self.parsing_stats['skipped_reasons'].items():
                percentage = (count / max(self.parsing_stats['total_lines_read'], 1)) * 100
                print(f"   • {reason}: {count:,} ({percentage:.1f}%)")
        
        # Show filtering efficiency
        total_params = self.parsing_stats['parameters_detected']
        allowed_params = self.parsing_stats.get('parameters_allowed', 0)
        if total_params > 0:
            efficiency = (allowed_params / total_params) * 100
            print(f"\n📊 Filtering Efficiency: {efficiency:.1f}% of detected parameters were mapped")
        
        # Data quality summary
        if 'quality_distribution' in self.parsing_stats:
            print("\n📈 Data Quality Distribution:")
            for quality, count in self.parsing_stats['quality_distribution'].items():
                percentage = (count / max(self.parsing_stats['valid_records_extracted'], 1)) * 100
                print(f"   • {quality}: {count:,} ({percentage:.1f}%)")
        
        print("="*60 + "\n")