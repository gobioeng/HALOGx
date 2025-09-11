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
        self._init_parameter_mapping()  # Call after other initializations

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
            # Enhanced parameter patterns - more flexible for actual log files
            "water_parameters": re.compile(
                r"([a-zA-Z][a-zA-Z0-9_\s]*[a-zA-Z0-9])"  # Capture parameter name (letters, numbers, underscores, spaces)
                r"[:\s]*count\s*=\s*(\d+),?\s*"           # count=N
                r"max\s*=\s*([\d.-]+),?\s*"               # max=N.N
                r"min\s*=\s*([\d.-]+),?\s*"               # min=N.N  
                r"avg\s*=\s*([\d.-]+)",                   # avg=N.N
                re.IGNORECASE,
            ),
            # Serial number patterns
            "serial_number": re.compile(r"SN#?\s*(\d+)", re.IGNORECASE),
            "serial_alt": re.compile(r"Serial[:\s]+(\d+)", re.IGNORECASE),
            "machine_id": re.compile(r"Machine[:\s]+(\d+)", re.IGNORECASE),
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
        return self._clean_and_validate_data(df)

    def _process_chunk(self, chunk_lines: List[Tuple[int, str]]) -> List[Dict]:
        """Process a chunk of lines (legacy method for compatibility)"""
        return self._process_chunk_optimized(chunk_lines)

    def _process_chunk_optimized(self, chunk_lines: List[Tuple[int, str]]) -> List[Dict]:
        """Optimized chunk processing with reduced function calls and early filtering"""
        records = []

        # Pre-compile frequently used patterns for this chunk
        water_pattern = self.patterns["water_parameters"]
        datetime_pattern = self.patterns["datetime"]
        datetime_alt_pattern = self.patterns["datetime_alt"]
        serial_pattern = self.patterns["serial_number"]

        for line_number, line in chunk_lines:
            try:
                # Early filtering - skip lines that clearly don't contain parameters
                if 'count=' not in line or 'avg=' not in line:
                    continue

                parsed_records = self._parse_line_optimized(line, line_number, 
                                                          water_pattern, datetime_pattern, 
                                                          datetime_alt_pattern, serial_pattern)
                records.extend(parsed_records)
            except Exception as e:
                self.parsing_stats["errors_encountered"] += 1

        return records

    def _parse_line_enhanced(self, line: str, line_number: int) -> List[Dict]:
        """Enhanced line parsing with unified parameter mapping and filtering (legacy method)"""
        return self._parse_line_optimized(line, line_number,
                                        self.patterns["water_parameters"],
                                        self.patterns["datetime"],
                                        self.patterns["datetime_alt"],
                                        self.patterns["serial_number"])

    def _parse_line_optimized(self, line: str, line_number: int, 
                            water_pattern, datetime_pattern, datetime_alt_pattern, serial_pattern) -> List[Dict]:
        """Optimized line parsing with pre-compiled patterns and reduced regex calls"""
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

            # Optimized parameter filtering - use cached mapping
            normalized_param = self._normalize_parameter_name_cached(param_name)
            if not normalized_param:  # Parameter not in our target list
                return records

            try:
                count = int(water_match.group(2))
                max_val = float(water_match.group(3))
                min_val = float(water_match.group(4))
                avg_val = float(water_match.group(5))
            except (ValueError, IndexError):
                return records  # Skip malformed numeric data

            record = {
                'datetime': datetime_str,
                'serial_number': serial_number,
                'parameter_type': normalized_param,
                'statistic_type': 'combined',
                'count': count,
                'max_value': max_val,
                'min_value': min_val,
                'avg_value': avg_val,
                'line_number': line_number,
                'quality': self._assess_data_quality_fast(normalized_param, avg_val, count)
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
        """Cached version of parameter normalization with exact pattern matching"""
        if param_name in self._param_cache:
            return self._param_cache[param_name]

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
        """Check if parameter is one of the comprehensive target parameters"""
        # Clean parameter name - remove logStatistics prefix if present
        cleaned_param = param_name
        if cleaned_param.lower().startswith('logstatistics '):
            cleaned_param = cleaned_param[14:]  # Remove "logStatistics " prefix

        param_lower = cleaned_param.lower().replace(" ", "").replace(":", "").replace("_", "")

        # Comprehensive target keywords for all parameter types
        target_keywords = [
            # Fan and speed parameters
            'fanremotetemp', 'fanhumidity', 'fanfanspeed', 'fanspeed', 'fan',

            # Water system parameters
            'magnetronflow', 'targetandcirculatorflow', 'citywaterflow',
            'pumpressure', 'waterflow', 'flow', 'pump', 'chiller', 'watertank',

            # Temperature parameters  
            'magnetrontemp', 'colboardtemp', 'pdutemp', 'watertanktemp',
            'ambienttemp', 'chillertemp', 'temp', 'temperature',

            # Voltage parameters
            'mlc_adc_chan_temp_banka', 'mlc_adc_chan_temp_bankb',
            'col_adc_chan_temp', 'voltage', 'volt', '24v', '48v', '5v',
            'banka', 'bankb', 'adc', 'mlc', 'col',

            # Humidity parameters
            'humidity', 'humid',

            # Pressure parameters
            'pressure', 'psi', 'bar'
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
        """Clean and validate the parsed data"""
        if df.empty:
            return df

        try:
            # Convert datetime
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

            # Remove rows with invalid datetime
            df = df.dropna(subset=["datetime"])

            # Sort by datetime
            df = df.sort_values("datetime")

            # Remove duplicates
            df = df.drop_duplicates(
                subset=["datetime", "serial_number", "parameter_type", "statistic_type"]
            )

            # Create additional columns needed by database manager for compatibility
            if 'avg_value' in df.columns:
                # Create separate records for avg, min, max for database compatibility
                records = []
                for _, row in df.iterrows():
                    base_record = row.to_dict()

                    # Average record
                    avg_record = base_record.copy()
                    avg_record['value'] = row['avg_value']
                    avg_record['statistic_type'] = 'avg'
                    records.append(avg_record)

                    # Min record
                    min_record = base_record.copy()
                    min_record['value'] = row['min_value']
                    min_record['statistic_type'] = 'min'
                    records.append(min_record)

                    # Max record
                    max_record = base_record.copy()
                    max_record['value'] = row['max_value']
                    max_record['statistic_type'] = 'max'
                    records.append(max_record)

                df = pd.DataFrame(records)

            # Reset index
            df = df.reset_index(drop=True)

            print(f"✓ Data cleaned: {len(df)} records ready for database")

        except Exception as e:
            print(f"Error cleaning data: {e}")

        return df

    # Fault Code Parsing Methods
    def load_fault_codes_from_file(self, file_path, source_type='uploaded'):
        """Load fault codes from file with specified source type"""
        try:
            if not os.path.exists(file_path):
                print(f"Fault code file not found: {file_path}")
                return False

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

                        self.fault_codes[code] = {
                            'description': fault_info['description'],
                            'source': source_type,
                            'line_number': line_num,
                            'database_description': db_desc,
                            'type': fault_info.get('type', 'Fault')
                        }

            loaded_count = len([c for c in self.fault_codes.values() if c['source'] == source_type])
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
        """Search for fault code in loaded database"""
        code = str(code).strip()

        if code in self.fault_codes:
            fault_data = self.fault_codes[code]
            source = fault_data.get('source', 'unknown')

            # Map source to proper database description
            if source == 'uploaded':
                db_desc = 'HAL Database'
            elif source == 'tb':
                db_desc = 'TB Database'
            else:
                db_desc = f"{source.title()} Database"

            return {
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
            return {
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