"""
Startup Performance Manager - HALog Enhancement
Manages startup performance optimization and data processing detection
Company: gobioeng.com
"""

import os
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime


class StartupPerformanceManager:
    """Manages startup performance optimization and prevents unnecessary reprocessing"""
    
    def __init__(self, app_data_dir: str = "data"):
        self.app_data_dir = Path(app_data_dir)
        self.cache_dir = self.app_data_dir / "cache"
        self.performance_cache_file = self.cache_dir / "performance_cache.json"
        self.data_checksums_file = self.cache_dir / "data_checksums.json"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Performance metrics
        self.startup_metrics = {
            "startup_time": 0,
            "data_processing_skipped": False,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        self.app_data_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        
    def calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"Error calculating checksum for {file_path}: {e}")
            return ""
            
    def get_data_checksum(self, data_sources: list) -> str:
        """Calculate combined checksum for multiple data sources"""
        try:
            combined_hash = hashlib.sha256()
            
            for source in data_sources:
                if os.path.exists(source):
                    file_hash = self.calculate_file_checksum(source)
                    combined_hash.update(file_hash.encode())
                    
            return combined_hash.hexdigest()
        except Exception as e:
            print(f"Error calculating combined checksum: {e}")
            return ""
            
    def load_performance_cache(self) -> Dict:
        """Load performance cache from file"""
        try:
            if self.performance_cache_file.exists():
                with open(self.performance_cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load performance cache: {e}")
            
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "processed_data": {},
            "tab_cache": {},
            "last_optimization": None
        }
        
    def save_performance_cache(self, cache_data: Dict):
        """Save performance cache to file"""
        try:
            cache_data["last_updated"] = datetime.now().isoformat()
            with open(self.performance_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save performance cache: {e}")
            
    def load_data_checksums(self) -> Dict:
        """Load data checksums from file"""
        try:
            if self.data_checksums_file.exists():
                with open(self.data_checksums_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load data checksums: {e}")
            
        return {
            "version": "1.0",
            "checksums": {},
            "last_updated": datetime.now().isoformat()
        }
        
    def save_data_checksums(self, checksums: Dict):
        """Save data checksums to file"""
        try:
            data = {
                "version": "1.0",
                "checksums": checksums,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.data_checksums_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save data checksums: {e}")

    def cache_processed_results(self, file_path: str, processed_data: Dict, summary_stats: Dict = None):
        """Cache processed results instead of storing all raw data"""
        try:
            file_key = os.path.basename(file_path)
            checksum = self.calculate_file_checksum(file_path)
            
            cache_data = self.load_performance_cache()
            
            # Store only essential processed data, not raw records
            cache_data["processed_data"][file_key] = {
                "checksum": checksum,
                "processed_at": datetime.now().isoformat(),
                "record_count": processed_data.get("record_count", 0),
                "parameter_summary": processed_data.get("parameter_summary", {}),
                "time_range": processed_data.get("time_range", {}),
                "quality_stats": processed_data.get("quality_stats", {}),
                "summary_stats": summary_stats or {}
            }
            
            self.save_performance_cache(cache_data)
            print(f"✓ Cached processed results for {file_key}")
            
        except Exception as e:
            print(f"Error caching processed results: {e}")
    
    def get_cached_results(self, file_path: str) -> Optional[Dict]:
        """Get cached processed results for a file"""
        try:
            file_key = os.path.basename(file_path)
            current_checksum = self.calculate_file_checksum(file_path)
            
            cache_data = self.load_performance_cache()
            cached_entry = cache_data.get("processed_data", {}).get(file_key)
            
            if cached_entry and cached_entry.get("checksum") == current_checksum:
                self.startup_metrics["cache_hits"] += 1
                return cached_entry
            else:
                self.startup_metrics["cache_misses"] += 1
                return None
                
        except Exception as e:
            print(f"Error getting cached results: {e}")
            self.startup_metrics["cache_misses"] += 1
            return None
    
    def should_skip_processing(self, file_paths: list) -> bool:
        """Check if data processing can be skipped based on file checksums"""
        try:
            current_checksums = {}
            for file_path in file_paths:
                if os.path.exists(file_path):
                    current_checksums[file_path] = self.calculate_file_checksum(file_path)
            
            stored_checksums = self.load_data_checksums()
            
            # Check if all files have the same checksums
            for file_path, checksum in current_checksums.items():
                if stored_checksums.get("checksums", {}).get(file_path) != checksum:
                    return False
                    
            # All files are unchanged
            self.startup_metrics["data_processing_skipped"] = True
            return True
            
        except Exception as e:
            print(f"Error checking file changes: {e}")
            return False
            
    def should_reprocess_data(self, data_sources: list, force_reprocess: bool = False) -> bool:
        """Determine if data needs to be reprocessed"""
        try:
            if force_reprocess:
                return True
                
            # Calculate current data checksum
            current_checksum = self.get_data_checksum(data_sources)
            
            if not current_checksum:
                return True  # Can't verify, so reprocess
                
            # Load stored checksums
            stored_checksums = self.load_data_checksums()
            
            # Check if checksum has changed
            stored_checksum = stored_checksums.get("checksums", {}).get("combined_data", "")
            
            if current_checksum != stored_checksum:
                print("📊 Data changes detected - reprocessing required")
                return True
            else:
                print("✅ No data changes detected - using cached results")
                self.startup_metrics["data_processing_skipped"] = True
                return False
                
        except Exception as e:
            print(f"Error checking reprocess requirement: {e}")
            return True  # Safe default
            
    def mark_data_processed(self, data_sources: list, processing_results: Dict):
        """Mark data as processed and save results"""
        try:
            # Calculate and save checksum
            current_checksum = self.get_data_checksum(data_sources)
            checksums = {"combined_data": current_checksum}
            self.save_data_checksums(checksums)
            
            # Save processing results to cache
            cache_data = self.load_performance_cache()
            cache_data["processed_data"] = {
                "checksum": current_checksum,
                "results": processing_results,
                "processed_at": datetime.now().isoformat()
            }
            self.save_performance_cache(cache_data)
            
            print("✅ Data processing results cached for future startups")
            
        except Exception as e:
            print(f"Error marking data as processed: {e}")
            
    def get_cached_processing_results(self) -> Optional[Dict]:
        """Get cached processing results if available"""
        try:
            cache_data = self.load_performance_cache()
            processed_data = cache_data.get("processed_data", {})
            
            if processed_data and "results" in processed_data:
                self.startup_metrics["cache_hits"] += 1
                return processed_data["results"]
            else:
                self.startup_metrics["cache_misses"] += 1
                return None
                
        except Exception as e:
            print(f"Error getting cached results: {e}")
            self.startup_metrics["cache_misses"] += 1
            return None
            
    def optimize_tab_caching(self, tab_data: Dict[str, Any]):
        """Optimize tab-specific data caching"""
        try:
            cache_data = self.load_performance_cache()
            
            if "tab_cache" not in cache_data:
                cache_data["tab_cache"] = {}
                
            # Update tab cache with timestamp
            for tab_name, data in tab_data.items():
                cache_data["tab_cache"][tab_name] = {
                    "data": data,
                    "cached_at": datetime.now().isoformat(),
                    "cache_key": hashlib.md5(str(data).encode()).hexdigest()[:16]
                }
                
            self.save_performance_cache(cache_data)
            
        except Exception as e:
            print(f"Error optimizing tab caching: {e}")
            
    def get_cached_tab_data(self, tab_name: str, max_age_seconds: int = 300) -> Optional[Any]:
        """Get cached tab data if still valid"""
        try:
            cache_data = self.load_performance_cache()
            tab_cache = cache_data.get("tab_cache", {})
            
            if tab_name in tab_cache:
                cached_item = tab_cache[tab_name]
                cached_at = datetime.fromisoformat(cached_item["cached_at"])
                age_seconds = (datetime.now() - cached_at).total_seconds()
                
                if age_seconds <= max_age_seconds:
                    self.startup_metrics["cache_hits"] += 1
                    return cached_item["data"]
                    
            self.startup_metrics["cache_misses"] += 1
            return None
            
        except Exception as e:
            print(f"Error getting cached tab data: {e}")
            self.startup_metrics["cache_misses"] += 1
            return None
            
    def clear_cache(self, cache_type: str = "all"):
        """Clear specified cache type"""
        try:
            if cache_type in ["all", "performance"]:
                if self.performance_cache_file.exists():
                    self.performance_cache_file.unlink()
                    print("✅ Performance cache cleared")
                    
            if cache_type in ["all", "checksums"]:
                if self.data_checksums_file.exists():
                    self.data_checksums_file.unlink()
                    print("✅ Data checksums cleared")
                    
        except Exception as e:
            print(f"Error clearing cache: {e}")
            
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        return self.startup_metrics.copy()
        
    def record_startup_time(self, startup_time: float):
        """Record application startup time"""
        self.startup_metrics["startup_time"] = startup_time
        
        try:
            cache_data = self.load_performance_cache()
            if "startup_history" not in cache_data:
                cache_data["startup_history"] = []
                
            cache_data["startup_history"].append({
                "startup_time": startup_time,
                "timestamp": datetime.now().isoformat(),
                "data_processing_skipped": self.startup_metrics["data_processing_skipped"]
            })
            
            # Keep only last 10 startup records
            cache_data["startup_history"] = cache_data["startup_history"][-10:]
            
            self.save_performance_cache(cache_data)
            
        except Exception as e:
            print(f"Error recording startup time: {e}")
            
    def get_startup_report(self) -> str:
        """Generate startup performance report"""
        metrics = self.get_performance_metrics()
        
        report = []
        report.append("=" * 50)
        report.append("HALOG STARTUP PERFORMANCE REPORT")
        report.append("=" * 50)
        report.append(f"Startup Time: {metrics['startup_time']:.2f} seconds")
        report.append(f"Data Processing Skipped: {'Yes' if metrics['data_processing_skipped'] else 'No'}")
        report.append(f"Cache Hits: {metrics['cache_hits']}")
        report.append(f"Cache Misses: {metrics['cache_misses']}")
        
        if metrics['cache_hits'] + metrics['cache_misses'] > 0:
            hit_rate = (metrics['cache_hits'] / (metrics['cache_hits'] + metrics['cache_misses'])) * 100
            report.append(f"Cache Hit Rate: {hit_rate:.1f}%")
            
        report.append("=" * 50)
        
        return "\n".join(report)