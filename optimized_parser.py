"""
Optimized Parser for HALOGx Application - Performance Enhancement
This module provides high-performance parsing using hardcoded parameters
to eliminate file I/O operations and improve application startup speed.

Developer: gobioeng.com
"""

import pandas as pd
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import time

from hardcoded_parameters import get_hardcoded_mapper

class OptimizedParser:
    """
    High-performance parser optimized for faster data processing
    Uses hardcoded parameter mappings and optimized regex patterns
    """
    
    def __init__(self):
        # Use hardcoded parameter mapper for maximum performance
        self.parameter_mapper = get_hardcoded_mapper()
        
        # Precompiled patterns for different data types
        self.patterns = self._compile_all_patterns()
        
        # Processing statistics
        self.stats = {
            "lines_processed": 0,
            "parameters_extracted": 0,
            "processing_time": 0.0,
            "errors": 0
        }
        
        print("✓ Optimized parser initialized with hardcoded parameters")
    
    def _compile_all_patterns(self) -> Dict[str, re.Pattern]:
        """Compile all regex patterns for maximum performance"""
        return {
            # Optimized datetime patterns
            "datetime_iso": re.compile(
                r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})", re.IGNORECASE
            ),
            "datetime_us": re.compile(
                r"(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2}:\d{2})", re.IGNORECASE
            ),
            
            # High-performance parameter extraction
            "parameter_stats": re.compile(
                r"([a-zA-Z][a-zA-Z0-9_\s\-\.]*[a-zA-Z0-9])"     # Parameter name
                r"[:\s]*(?:Statistics)?[:\s]*"                   # Optional Statistics
                r"(?:count\s*=\s*(\d+)[,\s]*)??"                # count
                r"(?:max\s*=\s*([\d.\-+eE]+)[,\s]*)??"         # max
                r"(?:min\s*=\s*([\d.\-+eE]+)[,\s]*)??"         # min
                r"(?:avg\s*=\s*([\d.\-+eE]+))??"               # avg
                , re.IGNORECASE
            ),
            
            # Alternative parameter patterns
            "parameter_simple": re.compile(
                r"([a-zA-Z][a-zA-Z0-9_\s\-\.]*[a-zA-Z0-9])"     # Parameter name
                r"[:\s]*"                                        # Separator
                r"([\d.\-+eE]+)"                                # Value
                r"\s*([a-zA-Z%°/]*)"                            # Optional unit
                , re.IGNORECASE
            ),
            
            # Serial number and machine ID
            "serial_number": re.compile(r"(?:SN|S/N|Serial)[#\s]*(\d+)", re.IGNORECASE),
            "machine_id": re.compile(r"Machine[:\s]+(\d+)", re.IGNORECASE),
            
            # Log prefix patterns
            "log_statistics": re.compile(
                r"logStatistics\s+(.+)", re.IGNORECASE
            ),
        }
    
    def parse_log_file_optimized(self, file_path: str, chunk_size: int = 5000) -> pd.DataFrame:
        """
        Parse LINAC log file with optimized performance
        Uses hardcoded parameters and efficient processing
        """
        start_time = time.time()
        
        try:
            records = []
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
            
            print(f"📊 Processing {len(lines)} lines with optimized parser...")
            
            # Process lines in chunks for memory efficiency
            for i in range(0, len(lines), chunk_size):
                chunk = lines[i:i + chunk_size]
                chunk_records = self._process_chunk_optimized(chunk)
                records.extend(chunk_records)
                
                if (i // chunk_size) % 10 == 0:  # Progress update every 10 chunks
                    progress = min(100, (i / len(lines)) * 100)
                    print(f"  Progress: {progress:.1f}% - {len(records)} records extracted")
            
            # Convert to DataFrame
            if records:
                df = pd.DataFrame(records)
                
                # Optimize DataFrame types for performance
                df = self._optimize_dataframe_types(df)
                
                processing_time = time.time() - start_time
                self.stats["processing_time"] = processing_time
                self.stats["lines_processed"] = len(lines)
                self.stats["parameters_extracted"] = len(records)
                
                print(f"✓ Optimized parsing completed: {len(records)} records in {processing_time:.2f}s")
                print(f"  Performance: {len(records)/processing_time:.1f} records/sec")
                
                return df
            else:
                print("⚠️ No valid data found in file")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error in optimized parsing: {e}")
            self.stats["errors"] += 1
            return pd.DataFrame()
    
    def _process_chunk_optimized(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Process a chunk of lines with optimized extraction"""
        records = []
        current_datetime = None
        current_serial = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            try:
                # Extract datetime if present
                datetime_match = self._extract_datetime_fast(line)
                if datetime_match:
                    current_datetime = datetime_match
                    continue
                
                # Extract serial number if present
                serial_match = self._extract_serial_fast(line)
                if serial_match:
                    current_serial = serial_match
                    continue
                
                # Extract parameters using hardcoded mapper
                parameters = self.parameter_mapper.extract_parameters_from_line(line)
                
                for param_name, param_data in parameters:
                    if current_datetime and 'avg' in param_data:
                        record = {
                            'datetime': current_datetime,
                            'serial_number': current_serial or 'Unknown',
                            'parameter_type': param_name,
                            'friendly_name': param_data['friendly_name'],
                            'category': param_data['category'],
                            'unit': param_data['unit'],
                            'avg': param_data['avg']
                        }
                        
                        # Add optional fields if present
                        for field in ['count', 'min', 'max']:
                            if field in param_data:
                                record[field] = param_data[field]
                        
                        # Add validation flags
                        for field in ['valid', 'in_range', 'critical']:
                            if field in param_data:
                                record[field] = param_data[field]
                        
                        records.append(record)
                        
            except Exception as e:
                self.stats["errors"] += 1
                continue
        
        return records
    
    def _extract_datetime_fast(self, line: str) -> Optional[datetime]:
        """Fast datetime extraction using precompiled patterns"""
        # Try ISO format first (most common)
        match = self.patterns["datetime_iso"].search(line)
        if match:
            try:
                date_part = match.group(1)
                time_part = match.group(2)
                return datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        
        # Try US format
        match = self.patterns["datetime_us"].search(line)
        if match:
            try:
                date_part = match.group(1)
                time_part = match.group(2)
                return datetime.strptime(f"{date_part} {time_part}", "%m/%d/%Y %H:%M:%S")
            except ValueError:
                pass
        
        return None
    
    def _extract_serial_fast(self, line: str) -> Optional[str]:
        """Fast serial number extraction"""
        match = self.patterns["serial_number"].search(line)
        if match:
            return match.group(1)
        return None
    
    def _optimize_dataframe_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame column types for performance and memory"""
        try:
            # Convert datetime column
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
            
            # Optimize numeric columns
            numeric_columns = ['avg', 'min', 'max', 'count']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Optimize categorical columns for memory efficiency
            categorical_columns = ['parameter_type', 'friendly_name', 'category', 'unit', 'serial_number']
            for col in categorical_columns:
                if col in df.columns:
                    df[col] = df[col].astype('category')
            
            # Optimize boolean columns
            boolean_columns = ['valid', 'in_range', 'critical']
            for col in boolean_columns:
                if col in df.columns:
                    df[col] = df[col].astype('bool')
            
            return df
            
        except Exception as e:
            print(f"⚠️ Warning: DataFrame optimization failed: {e}")
            return df
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics for performance monitoring"""
        return self.stats.copy()
    
    def get_parameter_categories(self) -> List[str]:
        """Get all available parameter categories for UI optimization"""
        return self.parameter_mapper.get_all_categories()
    
    def get_category_parameters(self, category: str) -> List[Dict]:
        """Get parameters for specific category for trend analysis"""
        return self.parameter_mapper.get_category_parameters(category)
    
    def validate_parameter_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate parsed parameter data for quality assurance"""
        if df.empty:
            return {"valid": False, "message": "No data to validate"}
        
        validation_results = {
            "valid": True,
            "total_records": len(df),
            "unique_parameters": df['parameter_type'].nunique() if 'parameter_type' in df.columns else 0,
            "date_range": None,
            "categories": [],
            "warnings": []
        }
        
        # Check date range
        if 'datetime' in df.columns:
            try:
                min_date = df['datetime'].min()
                max_date = df['datetime'].max()
                validation_results["date_range"] = {
                    "start": min_date.isoformat() if pd.notna(min_date) else None,
                    "end": max_date.isoformat() if pd.notna(max_date) else None,
                    "span_days": (max_date - min_date).days if pd.notna(min_date) and pd.notna(max_date) else 0
                }
            except Exception as e:
                validation_results["warnings"].append(f"Date validation error: {e}")
        
        # Check categories
        if 'category' in df.columns:
            validation_results["categories"] = df['category'].unique().tolist()
        
        # Check for critical values
        if 'critical' in df.columns:
            critical_count = df['critical'].sum() if df['critical'].dtype == bool else 0
            if critical_count > 0:
                validation_results["warnings"].append(f"{critical_count} critical values detected")
        
        # Check for out-of-range values
        if 'in_range' in df.columns:
            out_of_range_count = (~df['in_range']).sum() if df['in_range'].dtype == bool else 0
            if out_of_range_count > 0:
                validation_results["warnings"].append(f"{out_of_range_count} values out of expected range")
        
        return validation_results

# Global optimized parser instance
_optimized_parser = None

def get_optimized_parser() -> OptimizedParser:
    """Get global optimized parser instance (singleton pattern)"""
    global _optimized_parser
    if _optimized_parser is None:
        _optimized_parser = OptimizedParser()
    return _optimized_parser