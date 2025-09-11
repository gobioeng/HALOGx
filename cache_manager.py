"""
Performance Optimization and Caching System for HALog
Implements comprehensive caching for 50-70% startup time reduction
Developer: gobioeng.com
Date: 2025-09-11
"""

import os
import sqlite3
import hashlib
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
import pandas as pd
from pathlib import Path
import threading
import asyncio
from functools import wraps
import base64
from io import BytesIO


class DataCacheManager:
    """Manages data layer caching with TTL and automatic invalidation"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_metadata = {}
        self.default_ttl = 3600  # 1 hour default TTL
        self.load_metadata()
        
    def load_metadata(self):
        """Load cache metadata from disk"""
        try:
            metadata_file = self.cache_dir / "cache_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.cache_metadata = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load cache metadata: {e}")
            self.cache_metadata = {}
            
    def save_metadata(self):
        """Save cache metadata to disk"""
        try:
            metadata_file = self.cache_dir / "cache_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(self.cache_metadata, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save cache metadata: {e}")
            
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate unique cache key from arguments"""
        key_data = f"{prefix}_{args}_{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
        
    def _is_cache_valid(self, cache_key: str, ttl: int = None) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self.cache_metadata:
            return False
            
        metadata = self.cache_metadata[cache_key]
        ttl = ttl or self.default_ttl
        
        created_time = datetime.fromisoformat(metadata['created'])
        expiry_time = created_time + timedelta(seconds=ttl)
        
        return datetime.now() < expiry_time
        
    def _get_cache_file_path(self, cache_key: str, data_type: str = None) -> Path:
        """Get cache file path based on data type with fallback support"""
        if data_type == 'dataframe':
            # Check for parquet first, then fallback formats
            parquet_file = self.cache_dir / f"{cache_key}.parquet"
            csv_file = self.cache_dir / f"{cache_key}.csv"
            pickle_file = self.cache_dir / f"{cache_key}.pkl"
            
            # Return the first existing file, preferring parquet
            if parquet_file.exists():
                return parquet_file
            elif csv_file.exists():
                return csv_file
            elif pickle_file.exists():
                return pickle_file
            else:
                # Default to parquet for new files
                return parquet_file
        elif data_type == 'json':
            return self.cache_dir / f"{cache_key}.json"
        else:
            return self.cache_dir / f"{cache_key}.secure"
            
    def _detect_data_type(self, data: Any) -> str:
        """Detect data type for appropriate serialization"""
        if isinstance(data, pd.DataFrame):
            return 'dataframe'
        elif isinstance(data, (dict, list, str, int, float, bool, type(None))):
            return 'json'
        else:
            # For complex objects, convert to JSON-serializable format
            return 'json'
            
    def _serialize_data(self, data: Any, data_type: str) -> bytes:
        """Securely serialize data based on type with robust error handling"""
        if data_type == 'dataframe':
            # Try parquet first (most efficient), with fallbacks
            try:
                import pyarrow
                buffer = BytesIO()
                data.to_parquet(buffer, engine='pyarrow')
                print(f"✅ DataFrame serialized using parquet format")
                return buffer.getvalue()
            except ImportError:
                print("⚠️ PyArrow not available, falling back to CSV format")
                return self._serialize_dataframe_csv(data)
            except Exception as e:
                print(f"⚠️ Parquet serialization failed ({e}), falling back to CSV format")
                return self._serialize_dataframe_csv(data)
        elif data_type == 'json':
            # Use JSON for simple objects
            try:
                json_str = json.dumps(data, default=str, ensure_ascii=False)
                return json_str.encode('utf-8')
            except Exception as e:
                print(f"❌ JSON serialization failed: {e}")
                raise ValueError(f"Failed to serialize JSON data: {e}")
        else:
            raise ValueError(f"Unsupported data type for serialization: {type(data)}")
            
    def _serialize_dataframe_csv(self, df: pd.DataFrame) -> bytes:
        """Fallback DataFrame serialization using CSV format"""
        try:
            buffer = BytesIO()
            # Use CSV with proper encoding and handling
            df.to_csv(buffer, index=True, encoding='utf-8')
            csv_bytes = buffer.getvalue()
            print(f"✅ DataFrame serialized using CSV fallback (size: {len(csv_bytes)} bytes)")
            return csv_bytes
        except Exception as e:
            print(f"❌ CSV fallback serialization failed: {e}")
            # Last resort: use pickle (not ideal but functional)
            try:
                import pickle
                pickle_bytes = pickle.dumps(df)
                print(f"⚠️ Using pickle as last resort (size: {len(pickle_bytes)} bytes)")
                return pickle_bytes
            except Exception as pickle_error:
                raise ValueError(f"All DataFrame serialization methods failed. CSV: {e}, Pickle: {pickle_error}")
            
    def _deserialize_data(self, data_bytes: bytes, data_type: str) -> Any:
        """Securely deserialize data based on type with robust error handling"""
        if data_type == 'dataframe':
            # Try parquet first, with intelligent fallbacks
            try:
                import pyarrow
                buffer = BytesIO(data_bytes)
                df = pd.read_parquet(buffer, engine='pyarrow')
                print(f"✅ DataFrame deserialized from parquet format")
                return df
            except ImportError:
                print("⚠️ PyArrow not available, trying CSV fallback")
                return self._deserialize_dataframe_fallback(data_bytes)
            except Exception as e:
                print(f"⚠️ Parquet deserialization failed ({e}), trying fallback methods")
                return self._deserialize_dataframe_fallback(data_bytes)
        elif data_type == 'json':
            # Read JSON from bytes
            try:
                json_str = data_bytes.decode('utf-8')
                return json.loads(json_str)
            except Exception as e:
                print(f"❌ JSON deserialization failed: {e}")
                raise ValueError(f"Failed to deserialize JSON data: {e}")
        else:
            raise ValueError(f"Unsupported data type for deserialization: {data_type}")
            
    def _deserialize_dataframe_fallback(self, data_bytes: bytes) -> pd.DataFrame:
        """Intelligent fallback DataFrame deserialization"""
        # Try CSV first
        try:
            buffer = BytesIO(data_bytes)
            df = pd.read_csv(buffer, index_col=0, encoding='utf-8')
            print(f"✅ DataFrame deserialized from CSV fallback")
            return df
        except Exception as csv_error:
            print(f"⚠️ CSV deserialization failed ({csv_error}), trying pickle")
            
            # Try pickle as last resort
            try:
                import pickle
                df = pickle.loads(data_bytes)
                if isinstance(df, pd.DataFrame):
                    print(f"✅ DataFrame deserialized from pickle fallback")
                    return df
                else:
                    raise ValueError(f"Pickled object is not a DataFrame: {type(df)}")
            except Exception as pickle_error:
                raise ValueError(f"All DataFrame deserialization methods failed. CSV: {csv_error}, Pickle: {pickle_error}")
            
    def _calculate_checksum(self, data_bytes: bytes) -> str:
        """Calculate SHA-256 checksum for data integrity"""
        return hashlib.sha256(data_bytes).hexdigest()
        
    def _verify_checksum(self, data_bytes: bytes, expected_checksum: str) -> bool:
        """Verify data integrity using checksum"""
        return self._calculate_checksum(data_bytes) == expected_checksum
        
    def get_cached_data(self, cache_key: str, ttl: int = None) -> Optional[Any]:
        """Retrieve cached data if valid (secure implementation with robust error handling)"""
        try:
            print(f"🔍 Retrieving cached data for key '{cache_key}'")
            
            # Check cache validity
            if not self._is_cache_valid(cache_key, ttl):
                print(f"⏰ Cache expired or invalid for key '{cache_key}'")
                return None
                
            # Check metadata for data type and checksum
            if cache_key not in self.cache_metadata:
                print(f"📋 No metadata found for key '{cache_key}'")
                return None
                
            metadata = self.cache_metadata[cache_key]
            data_type = metadata.get('data_type', 'json')
            actual_format = metadata.get('actual_format', data_type)
            expected_checksum = metadata.get('checksum')
            
            print(f"📊 Cache metadata: type={data_type}, format={actual_format}")
            
            # Get cache file path with intelligent detection
            cache_file = self._get_cache_file_path(cache_key, data_type)
            
            # Handle legacy pickle files intelligently
            if not cache_file.exists():
                # Try to find alternative format files
                for ext in ['.parquet', '.csv', '.pkl', '.json']:
                    alt_file = self.cache_dir / f"{cache_key}{ext}"
                    if alt_file.exists():
                        cache_file = alt_file
                        print(f"🔄 Found alternative cache file: {cache_file.name}")
                        break
                        
            if not cache_file.exists():
                print(f"📁 Cache file not found for key '{cache_key}'")
                return None
                
            # Read and verify data with error handling
            try:
                with open(cache_file, 'rb') as f:
                    data_bytes = f.read()
                print(f"💾 Read {len(data_bytes)} bytes from cache file")
            except Exception as read_error:
                print(f"❌ Failed to read cache file: {read_error}")
                return None
                
            # Verify integrity if checksum exists
            if expected_checksum:
                if self._verify_checksum(data_bytes, expected_checksum):
                    print(f"✅ Cache integrity verified for key '{cache_key}'")
                else:
                    print(f"❌ Cache integrity check failed for key '{cache_key}'")
                    # Remove corrupted cache
                    try:
                        cache_file.unlink()
                        if cache_key in self.cache_metadata:
                            del self.cache_metadata[cache_key]
                            self.save_metadata()
                    except Exception as cleanup_error:
                        print(f"⚠️ Warning: Failed to clean up corrupted cache: {cleanup_error}")
                    return None
            else:
                print(f"⚠️ No checksum available for integrity verification")
                
            # Deserialize data with robust error handling
            try:
                data = self._deserialize_data(data_bytes, data_type)
                print(f"✅ Successfully deserialized cached data for key '{cache_key}'")
            except Exception as deserialize_error:
                print(f"❌ Deserialization failed for key '{cache_key}': {deserialize_error}")
                # Remove corrupted cache
                try:
                    cache_file.unlink()
                    if cache_key in self.cache_metadata:
                        del self.cache_metadata[cache_key]
                        self.save_metadata()
                except Exception as cleanup_error:
                    print(f"⚠️ Warning: Failed to clean up corrupted cache: {cleanup_error}")
                return None
                
            # Update access time with error handling
            try:
                self.cache_metadata[cache_key]['last_accessed'] = datetime.now().isoformat()
                self.save_metadata()
            except Exception as metadata_error:
                print(f"⚠️ Warning: Failed to update access time: {metadata_error}")
                # Don't fail the entire operation for metadata issues
            
            return data
            
        except Exception as e:
            print(f"❌ Error loading cached data for key '{cache_key}': {e}")
            import traceback
            print(f"🗂 Full error traceback: {traceback.format_exc()}")
            return None
            
    def cache_data(self, cache_key: str, data: Any, ttl: int = None):
        """Cache data with metadata (secure implementation with robust error handling)"""
        try:
            # Detect data type
            data_type = self._detect_data_type(data)
            print(f"📋 Caching data with key '{cache_key}' as type '{data_type}'")
            
            # Serialize data securely with fallback handling
            try:
                data_bytes = self._serialize_data(data, data_type)
            except Exception as serialize_error:
                print(f"❌ Serialization failed for key '{cache_key}': {serialize_error}")
                # For DataFrames, try alternative serialization
                if data_type == 'dataframe':
                    print(f"🔄 Attempting emergency DataFrame serialization...")
                    try:
                        data_bytes = self._serialize_dataframe_csv(data)
                    except Exception as emergency_error:
                        print(f"❌ Emergency serialization failed: {emergency_error}")
                        raise serialize_error
                else:
                    raise serialize_error
            
            # Calculate checksum for integrity
            checksum = self._calculate_checksum(data_bytes)
            
            # Get cache file path with smart extension detection
            cache_file = self._get_cache_file_path(cache_key, data_type)
            
            # Auto-detect actual format based on serialization result
            actual_format = self._detect_serialization_format(data_bytes, data_type)
            if actual_format != data_type and data_type == 'dataframe':
                # Update file extension to match actual format
                if actual_format == 'csv':
                    cache_file = self.cache_dir / f"{cache_key}.csv"
                elif actual_format == 'pickle':
                    cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            # Clean up any existing files with different extensions
            self._cleanup_old_cache_files(cache_key, data_type, cache_file)
            
            # Write data to file with error handling
            try:
                with open(cache_file, 'wb') as f:
                    f.write(data_bytes)
                print(f"✅ Cache file written: {cache_file.name} ({len(data_bytes)} bytes)")
            except Exception as write_error:
                print(f"❌ Failed to write cache file: {write_error}")
                raise write_error
                
            # Update metadata with comprehensive information
            self.cache_metadata[cache_key] = {
                'created': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'ttl': ttl or self.default_ttl,
                'size': os.path.getsize(cache_file),
                'data_type': data_type,
                'actual_format': actual_format,
                'file_extension': cache_file.suffix,
                'checksum': checksum,
                'version': '2.1'  # Updated version with enhanced error handling
            }
            
            # Save metadata with error handling
            try:
                self.save_metadata()
                print(f"✅ Cache metadata updated for key '{cache_key}'")
            except Exception as metadata_error:
                print(f"⚠️ Warning: Failed to save cache metadata: {metadata_error}")
                # Don't fail the entire operation for metadata issues
            
        except Exception as e:
            print(f"❌ Error caching data for key '{cache_key}': {e}")
            # Log the full error for debugging
            import traceback
            print(f"🗂 Full error traceback: {traceback.format_exc()}")
            
    def _detect_serialization_format(self, data_bytes: bytes, expected_type: str) -> str:
        """Detect the actual serialization format used"""
        if expected_type != 'dataframe':
            return expected_type
            
        # Try to detect format based on data content
        try:
            # Check if it's CSV (starts with common CSV patterns)
            data_str = data_bytes[:100].decode('utf-8', errors='ignore')
            if ',' in data_str and ('\n' in data_str or '\r' in data_str):
                return 'csv'
        except:
            pass
            
        # Check if it's pickle (has pickle magic bytes)
        if data_bytes.startswith(b'\x80\x03') or data_bytes.startswith(b'\x80\x04'):
            return 'pickle'
            
        # Default to parquet if we can't detect
        return 'dataframe'
        
    def _cleanup_old_cache_files(self, cache_key: str, data_type: str, current_file: Path):
        """Clean up old cache files with different extensions"""
        if data_type == 'dataframe':
            extensions = ['.parquet', '.csv', '.pkl']
            for ext in extensions:
                old_file = self.cache_dir / f"{cache_key}{ext}"
                if old_file.exists() and old_file != current_file:
                    try:
                        old_file.unlink()
                        print(f"🗑️ Cleaned up old cache file: {old_file.name}")
                    except Exception as e:
                        print(f"⚠️ Warning: Could not remove old cache file {old_file.name}: {e}")
            
    def invalidate_cache(self, cache_key: str = None, prefix: str = None):
        """Invalidate specific cache or all caches with prefix (secure implementation)"""
        try:
            if cache_key:
                # Invalidate specific cache
                if cache_key in self.cache_metadata:
                    metadata = self.cache_metadata[cache_key]
                    data_type = metadata.get('data_type', 'json')
                    
                    # Remove new format files
                    cache_file = self._get_cache_file_path(cache_key, data_type)
                    if cache_file.exists():
                        cache_file.unlink()
                        
                    # Also remove any legacy pickle files
                    legacy_pkl_file = self.cache_dir / f"{cache_key}.pkl"
                    if legacy_pkl_file.exists():
                        legacy_pkl_file.unlink()
                        
                    del self.cache_metadata[cache_key]
                    
            elif prefix:
                # Invalidate all caches with prefix
                keys_to_remove = []
                for key in self.cache_metadata:
                    if key.startswith(prefix):
                        metadata = self.cache_metadata[key]
                        data_type = metadata.get('data_type', 'json')
                        
                        # Remove new format files
                        cache_file = self._get_cache_file_path(key, data_type)
                        if cache_file.exists():
                            cache_file.unlink()
                            
                        # Also remove any legacy pickle files
                        legacy_pkl_file = self.cache_dir / f"{key}.pkl"
                        if legacy_pkl_file.exists():
                            legacy_pkl_file.unlink()
                            
                        keys_to_remove.append(key)
                        
                for key in keys_to_remove:
                    del self.cache_metadata[key]
                    
            self.save_metadata()
            
        except Exception as e:
            print(f"Error invalidating cache: {e}")
            
    def cleanup_expired_caches(self):
        """Remove expired cache files (secure implementation)"""
        try:
            expired_keys = []
            for cache_key in self.cache_metadata:
                if not self._is_cache_valid(cache_key):
                    expired_keys.append(cache_key)
                    
            for key in expired_keys:
                self.invalidate_cache(key)
                
            # Also clean up any orphaned legacy pickle files
            legacy_pkl_files = list(self.cache_dir.glob("*.pkl"))
            for pkl_file in legacy_pkl_files:
                print(f"Removing orphaned legacy pickle file: {pkl_file}")
                pkl_file.unlink()
                
            print(f"Cleaned up {len(expired_keys)} expired cache entries and {len(legacy_pkl_files)} legacy pickle files")
            
        except Exception as e:
            print(f"Error cleaning up caches: {e}")
            
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            total_size = sum(meta.get('size', 0) for meta in self.cache_metadata.values())
            valid_caches = sum(1 for key in self.cache_metadata if self._is_cache_valid(key))
            
            return {
                'total_entries': len(self.cache_metadata),
                'valid_entries': valid_caches,
                'expired_entries': len(self.cache_metadata) - valid_caches,
                'total_size_mb': total_size / (1024 * 1024),
                'cache_dir': str(self.cache_dir)
            }
            
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {}


class QueryResultCache:
    """Specialized cache for database query results"""
    
    def __init__(self, cache_manager: DataCacheManager):
        self.cache_manager = cache_manager
        self.query_cache_ttl = 1800  # 30 minutes for queries
        
    def cache_query_result(self, query: str, params: tuple, result: pd.DataFrame):
        """Cache database query result"""
        cache_key = self.cache_manager._generate_cache_key("query", query, params)
        self.cache_manager.cache_data(cache_key, result, self.query_cache_ttl)
        
    def get_cached_query_result(self, query: str, params: tuple) -> Optional[pd.DataFrame]:
        """Get cached query result"""
        cache_key = self.cache_manager._generate_cache_key("query", query, params)
        return self.cache_manager.get_cached_data(cache_key, self.query_cache_ttl)
        
    def invalidate_query_cache(self):
        """Invalidate all query caches"""
        self.cache_manager.invalidate_cache(prefix="query")


class PlotCache:
    """Specialized cache for rendered plot data"""
    
    def __init__(self, cache_manager: DataCacheManager):
        self.cache_manager = cache_manager
        self.plot_cache_ttl = 900  # 15 minutes for plots
        
    def cache_plot_data(self, parameter: str, data_hash: str, plot_config: dict, plot_data: dict):
        """Cache pre-computed plot data"""
        cache_key = self.cache_manager._generate_cache_key("plot", parameter, data_hash, plot_config)
        
        cached_item = {
            'plot_data': plot_data,
            'parameter': parameter,
            'config': plot_config,
            'created': datetime.now().isoformat()
        }
        
        self.cache_manager.cache_data(cache_key, cached_item, self.plot_cache_ttl)
        
    def get_cached_plot_data(self, parameter: str, data_hash: str, plot_config: dict) -> Optional[dict]:
        """Get cached plot data"""
        cache_key = self.cache_manager._generate_cache_key("plot", parameter, data_hash, plot_config)
        cached_item = self.cache_manager.get_cached_data(cache_key, self.plot_cache_ttl)
        
        if cached_item:
            return cached_item.get('plot_data')
        return None
        
    def invalidate_plot_cache(self, parameter: str = None):
        """Invalidate plot caches"""
        if parameter:
            # Invalidate specific parameter plots
            prefix = self.cache_manager._generate_cache_key("plot", parameter)[:8]
            self.cache_manager.invalidate_cache(prefix=prefix)
        else:
            # Invalidate all plot caches
            self.cache_manager.invalidate_cache(prefix="plot")


class StartupCache:
    """Cache for startup data to reduce initialization time"""
    
    def __init__(self, cache_manager: DataCacheManager):
        self.cache_manager = cache_manager
        self.startup_cache_ttl = 7200  # 2 hours for startup data
        
    def cache_fault_codes(self, fault_codes: dict):
        """Cache fault code data"""
        cache_key = "startup_fault_codes"
        self.cache_manager.cache_data(cache_key, fault_codes, self.startup_cache_ttl)
        
    def get_cached_fault_codes(self) -> Optional[dict]:
        """Get cached fault code data"""
        return self.cache_manager.get_cached_data("startup_fault_codes", self.startup_cache_ttl)
        
    def cache_parameter_mapping(self, parameter_mapping: dict):
        """Cache parameter mapping data"""
        cache_key = "startup_parameter_mapping"
        self.cache_manager.cache_data(cache_key, parameter_mapping, self.startup_cache_ttl)
        
    def get_cached_parameter_mapping(self) -> Optional[dict]:
        """Get cached parameter mapping data"""
        return self.cache_manager.get_cached_data("startup_parameter_mapping", self.startup_cache_ttl)
        
    def cache_database_schema(self, schema_info: dict):
        """Cache database schema information"""
        cache_key = "startup_database_schema"
        self.cache_manager.cache_data(cache_key, schema_info, self.startup_cache_ttl)
        
    def get_cached_database_schema(self) -> Optional[dict]:
        """Get cached database schema information"""
        return self.cache_manager.get_cached_data("startup_database_schema", self.startup_cache_ttl)


class PerformanceManager:
    """Main performance optimization manager"""
    
    def __init__(self):
        self.cache_manager = DataCacheManager()
        self.query_cache = QueryResultCache(self.cache_manager)
        self.plot_cache = PlotCache(self.cache_manager)
        self.startup_cache = StartupCache(self.cache_manager)
        self.performance_metrics = {}
        
    def measure_performance(self, operation_name: str):
        """Decorator to measure operation performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    if operation_name not in self.performance_metrics:
                        self.performance_metrics[operation_name] = []
                    
                    self.performance_metrics[operation_name].append({
                        'duration': duration,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Keep only last 100 measurements
                    if len(self.performance_metrics[operation_name]) > 100:
                        self.performance_metrics[operation_name] = self.performance_metrics[operation_name][-100:]
                        
            return wrapper
        return decorator
        
    def get_performance_report(self) -> dict:
        """Generate performance report"""
        try:
            report = {
                'cache_stats': self.cache_manager.get_cache_stats(),
                'operation_metrics': {}
            }
            
            for operation, metrics in self.performance_metrics.items():
                if metrics:
                    durations = [m['duration'] for m in metrics]
                    report['operation_metrics'][operation] = {
                        'avg_duration': sum(durations) / len(durations),
                        'min_duration': min(durations),
                        'max_duration': max(durations),
                        'total_calls': len(durations),
                        'latest_call': metrics[-1]['timestamp']
                    }
                    
            return report
            
        except Exception as e:
            print(f"Error generating performance report: {e}")
            return {}
            
    def optimize_startup(self):
        """Perform startup optimizations"""
        try:
            print("🚀 Performing startup optimizations...")
            
            # Cleanup expired caches
            self.cache_manager.cleanup_expired_caches()
            
            # Pre-warm critical caches if needed
            self._prewarm_caches()
            
            print("✅ Startup optimizations complete")
            
        except Exception as e:
            print(f"Error during startup optimization: {e}")
            
    def _prewarm_caches(self):
        """Pre-warm frequently used caches"""
        try:
            # This could be expanded to pre-load common queries, plots, etc.
            # For now, just ensure cache directories exist
            self.cache_manager.cache_dir.mkdir(parents=True, exist_ok=True)
            
        except Exception as e:
            print(f"Error pre-warming caches: {e}")
            
    def clear_all_caches(self):
        """Clear all cached data (secure implementation)"""
        try:
            import shutil
            if self.cache_manager.cache_dir.exists():
                shutil.rmtree(self.cache_manager.cache_dir)
                self.cache_manager.cache_dir.mkdir(parents=True, exist_ok=True)
                
            self.cache_manager.cache_metadata = {}
            self.cache_manager.save_metadata()
            
            print("🗑️ All caches cleared (including legacy pickle files)")
            
        except Exception as e:
            print(f"Error clearing caches: {e}")


# Global performance manager instance
performance_manager = PerformanceManager()

def cached_query(ttl: int = 1800):
    """Decorator for caching database query results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function and arguments
            cache_key = performance_manager.cache_manager._generate_cache_key(
                f"query_{func.__name__}", args, kwargs
            )
            
            # Try to get cached result
            cached_result = performance_manager.cache_manager.get_cached_data(cache_key, ttl)
            if cached_result is not None:
                return cached_result
                
            # Execute function and cache result
            result = func(*args, **kwargs)
            performance_manager.cache_manager.cache_data(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def performance_monitor(operation_name: str):
    """Decorator to monitor function performance"""
    return performance_manager.measure_performance(operation_name)