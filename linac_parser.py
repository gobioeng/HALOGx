
import pandas as pd
import numpy as np
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import traceback


class LinacLogParser:
    """Enhanced LINAC log parser with comprehensive pattern matching"""
    
    def __init__(self):
        self.stats = {
            'lines_processed': 0,
            'records_created': 0,
            'errors': 0,
            'processing_time': 0
        }
        self._compile_patterns()
        self._init_parameter_mapping()
    
    def _compile_patterns(self):
        """Compile comprehensive regex patterns for different log formats"""
        self.patterns = {
            # DateTime patterns
            'datetime': re.compile(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})'),
            'datetime_alt': re.compile(r'(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2}:\d{2})'),
            
            # Serial and machine patterns
            'serial': re.compile(r'(?:SN|S/N|Serial)[#\s]*(\d+)', re.IGNORECASE),
            'machine_id': re.compile(r'Machine[#\s]*(\d+)', re.IGNORECASE),
            
            # Water system parameters
            'water_parameters': re.compile(
                r'('
                r'cooling\s*pump\s*high\s*statistics|CoolingpumpHighStatistics|pumpPressure|'
                r'magnetron\s*flow|magnetronFlow|CoolingmagnetronFlowLowStatistics|'
                r'target\s*(?:and\s*)?circulator\s*flow|targetAndCirculatorFlow|'
                r'cooling\s*city\s*water\s*flow\s*statistics|CoolingcityWaterFlowLowStatistics|cityWaterFlow|'
                r'[a-zA-Z][\w\s]*\w'
                r')'
                r'[:\s]*count\s*=\s*(\d+)(?:,|\s)*'
                r'max\s*=\s*([\d\.-]+)(?:,|\s)*'
                r'min\s*=\s*([\d\.-]+)(?:,|\s)*'
                r'avg\s*=\s*([\d\.-]+)',
                re.IGNORECASE
            ),
            
            # Voltage parameters
            'voltage_parameters': re.compile(
                r'(MLC\s*Bank\s*[AB]\s*24V|COL\s*48V|[a-zA-Z][\w\s]*voltage[\w\s]*)'
                r'[:\s]*count\s*=\s*(\d+)(?:,|\s)*'
                r'max\s*=\s*([\d\.-]+)(?:,|\s)*'
                r'min\s*=\s*([\d\.-]+)(?:,|\s)*'
                r'avg\s*=\s*([\d\.-]+)',
                re.IGNORECASE
            ),
            
            # Temperature parameters
            'temperature_parameters': re.compile(
                r'(Temp\s*Room|Temp\s*PDU|Temp\s*COL\s*Board|Temp\s*Magnetron|[a-zA-Z][\w\s]*temp[\w\s]*)'
                r'[:\s]*count\s*=\s*(\d+)(?:,|\s)*'
                r'max\s*=\s*([\d\.-]+)(?:,|\s)*'
                r'min\s*=\s*([\d\.-]+)(?:,|\s)*'
                r'avg\s*=\s*([\d\.-]+)',
                re.IGNORECASE
            ),
            
            # Fan speed parameters
            'fan_parameters': re.compile(
                r'(Speed\s*FAN\s*[1-4]|[a-zA-Z][\w\s]*fan[\w\s]*speed[\w\s]*)'
                r'[:\s]*count\s*=\s*(\d+)(?:,|\s)*'
                r'max\s*=\s*([\d\.-]+)(?:,|\s)*'
                r'min\s*=\s*([\d\.-]+)(?:,|\s)*'
                r'avg\s*=\s*([\d\.-]+)',
                re.IGNORECASE
            ),
            
            # Humidity parameters
            'humidity_parameters': re.compile(
                r'(Room\s*Humidity|[a-zA-Z][\w\s]*humidity[\w\s]*)'
                r'[:\s]*count\s*=\s*(\d+)(?:,|\s)*'
                r'max\s*=\s*([\d\.-]+)(?:,|\s)*'
                r'min\s*=\s*([\d\.-]+)(?:,|\s)*'
                r'avg\s*=\s*([\d\.-]+)',
                re.IGNORECASE
            )
        }
    
    def _init_parameter_mapping(self):
        """Initialize comprehensive parameter mapping"""
        self.parameter_mapping = {
            # Water System Parameters
            'pumpPressure': {
                'patterns': ['cooling pump high statistics', 'coolingpumphighstatistics', 'pumppressure'],
                'unified_name': 'Cooling Pump Pressure',
                'unit': 'PSI',
                'description': 'Cooling Pump Pressure',
                'range': (150, 250),
                'category': 'water'
            },
            'magnetronFlow': {
                'patterns': ['magnetron flow', 'magnetronflow', 'coolingmagnetronflowlowstatistics'],
                'unified_name': 'Mag Flow',
                'unit': 'L/min',
                'description': 'Magnetron Cooling Flow',
                'range': (3, 10),
                'category': 'water'
            },
            'targetAndCirculatorFlow': {
                'patterns': ['target and circulator flow', 'targetandcirculatorflow'],
                'unified_name': 'Flow Target',
                'unit': 'L/min',
                'description': 'Target and Circulator Flow',
                'range': (2, 5),
                'category': 'water'
            },
            'cityWaterFlow': {
                'patterns': ['cooling city water flow statistics', 'cityWaterFlow', 'chiller water'],
                'unified_name': 'Flow Chiller Water',
                'unit': 'L/min',
                'description': 'City/Chiller Water Flow',
                'range': (8, 18),
                'category': 'water'
            },
            
            # Voltage Parameters
            'mlcBankA24V': {
                'patterns': ['mlc bank a 24v', 'mlcbanka24v'],
                'unified_name': 'MLC Bank A 24V',
                'unit': 'V',
                'description': 'MLC Bank A 24V Supply',
                'range': (22, 26),
                'category': 'voltage'
            },
            'mlcBankB24V': {
                'patterns': ['mlc bank b 24v', 'mlcbankb24v'],
                'unified_name': 'MLC Bank B 24V',
                'unit': 'V',
                'description': 'MLC Bank B 24V Supply',
                'range': (22, 26),
                'category': 'voltage'
            },
            'col48V': {
                'patterns': ['col 48v', 'col48v'],
                'unified_name': 'COL 48V',
                'unit': 'V',
                'description': 'Collimator 48V Supply',
                'range': (46, 50),
                'category': 'voltage'
            },
            
            # Temperature Parameters
            'tempRoom': {
                'patterns': ['temp room', 'temproom', 'room temperature'],
                'unified_name': 'Temp Room',
                'unit': '°C',
                'description': 'Room Temperature',
                'range': (18, 25),
                'category': 'temperature'
            },
            'tempPDU': {
                'patterns': ['temp pdu', 'temppdu', 'pdu temperature'],
                'unified_name': 'Temp PDU',
                'unit': '°C',
                'description': 'PDU Temperature',
                'range': (20, 40),
                'category': 'temperature'
            },
            'tempCOLBoard': {
                'patterns': ['temp col board', 'tempcolboard', 'collimator board temperature'],
                'unified_name': 'Temp COL Board',
                'unit': '°C',
                'description': 'Collimator Board Temperature',
                'range': (25, 45),
                'category': 'temperature'
            },
            'tempMagnetron': {
                'patterns': ['temp magnetron', 'tempmagnetron', 'magnetron temperature'],
                'unified_name': 'Temp Magnetron',
                'unit': '°C',
                'description': 'Magnetron Temperature',
                'range': (30, 60),
                'category': 'temperature'
            },
            
            # Fan Speed Parameters
            'speedFan1': {
                'patterns': ['speed fan 1', 'speedfan1', 'fan 1 speed'],
                'unified_name': 'Speed FAN 1',
                'unit': 'RPM',
                'description': 'Fan 1 Speed',
                'range': (1000, 3000),
                'category': 'fan'
            },
            'speedFan2': {
                'patterns': ['speed fan 2', 'speedfan2', 'fan 2 speed'],
                'unified_name': 'Speed FAN 2',
                'unit': 'RPM',
                'description': 'Fan 2 Speed',
                'range': (1000, 3000),
                'category': 'fan'
            },
            'speedFan3': {
                'patterns': ['speed fan 3', 'speedfan3', 'fan 3 speed'],
                'unified_name': 'Speed FAN 3',
                'unit': 'RPM',
                'description': 'Fan 3 Speed',
                'range': (1000, 3000),
                'category': 'fan'
            },
            'speedFan4': {
                'patterns': ['speed fan 4', 'speedfan4', 'fan 4 speed'],
                'unified_name': 'Speed FAN 4',
                'unit': 'RPM',
                'description': 'Fan 4 Speed',
                'range': (1000, 3000),
                'category': 'fan'
            },
            
            # Humidity Parameters
            'roomHumidity': {
                'patterns': ['room humidity', 'roomhumidity', 'humidity'],
                'unified_name': 'Room Humidity',
                'unit': '%RH',
                'description': 'Room Humidity',
                'range': (30, 70),
                'category': 'humidity'
            }
        }
        
        # Create reverse mapping for quick lookup
        self.pattern_to_unified = {}
        for unified_key, config in self.parameter_mapping.items():
            for pattern in config['patterns']:
                self.pattern_to_unified[pattern.lower().replace(' ', '')] = unified_key
    
    def parse_file(self, file_path: str, progress_callback=None, cancel_callback=None) -> List[Dict]:
        """Parse LINAC log file with enhanced pattern recognition"""
        import time
        start_time = time.time()
        
        records = []
        self.stats = {'lines_processed': 0, 'records_created': 0, 'errors': 0, 'processing_time': 0}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            batch_size = max(100, total_lines // 100)
            
            for line_num, line in enumerate(lines, 1):
                if cancel_callback and cancel_callback():
                    break
                
                try:
                    line_records = self._parse_line(line.strip(), line_num)
                    if line_records:
                        records.extend(line_records)
                        self.stats['records_created'] += len(line_records)
                
                except Exception as e:
                    self.stats['errors'] += 1
                    if self.stats['errors'] <= 10:
                        print(f"Line {line_num} parse error: {e}")
                
                self.stats['lines_processed'] += 1
                
                # Progress updates
                if line_num % batch_size == 0 and progress_callback:
                    progress = (line_num / total_lines) * 100
                    progress_callback(int(progress), f"Processing line {line_num:,} of {total_lines:,}")
            
            self.stats['processing_time'] = time.time() - start_time
            print(f"Parsing complete: {self.stats['records_created']} records from {self.stats['lines_processed']} lines")
            
            return records
            
        except Exception as e:
            print(f"File parsing error: {e}")
            traceback.print_exc()
            return []
    
    def _parse_line(self, line: str, line_number: int) -> List[Dict]:
        """Parse individual line with comprehensive pattern matching"""
        if not line or len(line.strip()) < 10:
            return []
        
        records = []
        
        # Extract datetime
        timestamp = self._extract_datetime(line)
        if not timestamp:
            return []
        
        # Extract serial number
        serial = self._extract_serial(line)
        
        # Try all parameter pattern types
        pattern_types = ['water_parameters', 'voltage_parameters', 'temperature_parameters', 
                        'fan_parameters', 'humidity_parameters']
        
        for pattern_type in pattern_types:
            matches = self.patterns[pattern_type].finditer(line)
            
            for match in matches:
                try:
                    param_raw = match.group(1).strip()
                    count = int(match.group(2))
                    max_val = float(match.group(3))
                    min_val = float(match.group(4))
                    avg_val = float(match.group(5))
                    
                    # Map to unified parameter
                    param_clean = param_raw.lower().replace(' ', '').replace(':', '')
                    unified_key = self.pattern_to_unified.get(param_clean)
                    
                    if unified_key:
                        config = self.parameter_mapping[unified_key]
                        unified_name = config['unified_name']
                    else:
                        unified_name = param_raw
                        config = {
                            'unit': '',
                            'description': param_raw,
                            'range': (0, float('inf')),
                            'category': 'other'
                        }
                    
                    # Validate values
                    if self._validate_values(max_val, min_val, avg_val, config.get('range', (0, float('inf')))):
                        # Create records for each statistic
                        for stat_type, value in [('avg', avg_val), ('min', min_val), ('max', max_val)]:
                            records.append({
                                'datetime': timestamp,
                                'serial_number': serial,
                                'parameter_type': unified_name,
                                'statistic_type': stat_type,
                                'value': value,
                                'count': count,
                                'unit': config['unit'],
                                'description': config['description'],
                                'category': config.get('category', 'other'),
                                'data_quality': self._assess_quality(value, count, config.get('range')),
                                'raw_parameter': param_raw,
                                'line_number': line_number
                            })
                
                except (ValueError, IndexError) as e:
                    self.stats['errors'] += 1
        
        return records
    
    def _extract_datetime(self, line: str) -> Optional[str]:
        """Extract datetime with multiple format support"""
        # Primary pattern
        match = self.patterns['datetime'].search(line)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        
        # Alternative pattern
        match = self.patterns['datetime_alt'].search(line)
        if match:
            try:
                date_obj = datetime.strptime(match.group(1), '%m/%d/%Y')
                return f"{date_obj.strftime('%Y-%m-%d')} {match.group(2)}"
            except ValueError:
                pass
        
        return None
    
    def _extract_serial(self, line: str) -> str:
        """Extract serial number with multiple patterns"""
        for pattern_name in ['serial', 'machine_id']:
            match = self.patterns[pattern_name].search(line)
            if match:
                return f"SN#{match.group(1)}"
        return "Unknown"
    
    def _validate_values(self, max_val: float, min_val: float, avg_val: float, 
                        value_range: Tuple[float, float]) -> bool:
        """Validate parameter values with enhanced logic"""
        # Basic logical validation
        if not (min_val <= avg_val <= max_val):
            return False
        
        # Range validation with tolerance
        if value_range:
            range_min, range_max = value_range
            tolerance = (range_max - range_min) * 2.0  # 200% tolerance
            
            extended_min = range_min - tolerance
            extended_max = range_max + tolerance
            
            return (extended_min <= min_val <= extended_max and 
                    extended_min <= max_val <= extended_max)
        
        return True
    
    def _assess_quality(self, value: float, count: int, value_range: Optional[Tuple[float, float]]) -> str:
        """Assess data quality based on value and count"""
        if value_range:
            range_min, range_max = value_range
            if range_min <= value <= range_max:
                return 'excellent' if count > 100 else 'good' if count > 50 else 'fair'
            else:
                return 'poor'
        
        # Default quality assessment
        return 'good' if count > 50 else 'fair'
    
    def get_parameter_categories(self) -> Dict[str, List[str]]:
        """Get parameters grouped by category"""
        categories = {}
        for config in self.parameter_mapping.values():
            category = config.get('category', 'other')
            unified_name = config['unified_name']
            
            if category not in categories:
                categories[category] = []
            
            if unified_name not in categories[category]:
                categories[category].append(unified_name)
        
        return categories
