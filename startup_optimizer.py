"""
Startup Performance Manager with Hardcoded Optimizations
Provides enhanced startup performance with precompiled components

Developer: gobioeng.com
"""

import time
import os
from typing import Dict, Any, Optional

class StartupPerformanceOptimizer:
    """
    Optimized startup manager with hardcoded components for maximum performance
    Eliminates unnecessary file I/O and initialization overhead
    """
    
    def __init__(self):
        self.startup_time = time.time()
        self.optimization_enabled = True
        self.precompiled_ready = False
        
        # Performance metrics
        self.metrics = {
            "parameter_mapper_time": 0.0,
            "parser_init_time": 0.0,
            "ui_setup_time": 0.0,
            "database_init_time": 0.0,
            "total_startup_time": 0.0
        }
        
        print("🚀 Startup performance optimizer initialized")
    
    def precompile_components(self):
        """Precompile all components for faster startup"""
        start_time = time.time()
        
        try:
            # Precompile hardcoded parameter mapper
            from hardcoded_parameters import get_hardcoded_mapper
            mapper_start = time.time()
            self.hardcoded_mapper = get_hardcoded_mapper()
            self.metrics["parameter_mapper_time"] = time.time() - mapper_start
            
            # Precompile optimized parser
            from optimized_parser import get_optimized_parser
            parser_start = time.time()
            self.optimized_parser = get_optimized_parser()
            self.metrics["parser_init_time"] = time.time() - parser_start
            
            self.precompiled_ready = True
            total_precompile_time = time.time() - start_time
            
            print(f"✓ Components precompiled in {total_precompile_time:.4f}s")
            print(f"  - Parameter mapper: {self.metrics['parameter_mapper_time']:.4f}s")
            print(f"  - Optimized parser: {self.metrics['parser_init_time']:.4f}s")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Component precompilation failed: {e}")
            self.precompiled_ready = False
            return False
    
    def get_precompiled_mapper(self):
        """Get precompiled parameter mapper"""
        if self.precompiled_ready and hasattr(self, 'hardcoded_mapper'):
            return self.hardcoded_mapper
        
        # Fallback to lazy loading
        from hardcoded_parameters import get_hardcoded_mapper
        return get_hardcoded_mapper()
    
    def get_precompiled_parser(self):
        """Get precompiled optimized parser"""
        if self.precompiled_ready and hasattr(self, 'optimized_parser'):
            return self.optimized_parser
        
        # Fallback to lazy loading
        from optimized_parser import get_optimized_parser
        return get_optimized_parser()
    
    def optimize_trend_initialization(self):
        """Pre-generate trend control data for faster UI initialization"""
        try:
            if not self.precompiled_ready:
                return None
            
            # Pre-categorize parameters for trend controls
            categories = self.hardcoded_mapper.get_all_categories()
            
            optimized_trend_data = {
                "flow_parameters": [],
                "voltage_parameters": [],
                "temperature_parameters": [],
                "humidity_parameters": [],
                "fan_parameters": []
            }
            
            for category in categories:
                params = self.hardcoded_mapper.get_category_parameters(category)
                friendly_names = [p["friendly_name"] for p in params]
                
                if category == "water_system":
                    optimized_trend_data["flow_parameters"].extend(friendly_names)
                elif category in ["mlc_voltage", "col_voltage", "power_supply"]:
                    optimized_trend_data["voltage_parameters"].extend(friendly_names)
                elif category in ["temperature", "mlc_temperature", "col_temperature"]:
                    optimized_trend_data["temperature_parameters"].extend(friendly_names)
                elif category == "humidity":
                    optimized_trend_data["humidity_parameters"].extend(friendly_names)
                elif category == "fan_speed":
                    optimized_trend_data["fan_parameters"].extend(friendly_names)
            
            # Sort for consistent UI
            for key in optimized_trend_data:
                optimized_trend_data[key] = sorted(optimized_trend_data[key])
            
            print(f"✓ Trend data pre-generated:")
            for key, params in optimized_trend_data.items():
                print(f"  - {key}: {len(params)} parameters")
            
            return optimized_trend_data
            
        except Exception as e:
            print(f"⚠️ Trend optimization failed: {e}")
            return None
    
    def get_startup_report(self) -> str:
        """Generate startup performance report"""
        total_time = time.time() - self.startup_time
        self.metrics["total_startup_time"] = total_time
        
        report = f"""
🚀 HALOGx Startup Performance Report
{'='*50}
Total Startup Time: {total_time:.3f}s

Component Initialization:
  - Parameter Mapper: {self.metrics['parameter_mapper_time']:.4f}s
  - Optimized Parser: {self.metrics['parser_init_time']:.4f}s
  - UI Setup: {self.metrics.get('ui_setup_time', 0):.4f}s
  - Database: {self.metrics.get('database_init_time', 0):.4f}s

Optimizations Applied:
  ✓ Hardcoded parameters (eliminates file I/O)
  ✓ Precompiled regex patterns
  ✓ Optimized parser algorithms
  ✓ Component preloading
  {"✓ Trend data pre-generation" if self.precompiled_ready else "⚠ Trend optimization not applied"}

Performance Status: {"🟢 OPTIMIZED" if total_time < 3.0 else "🟡 ACCEPTABLE" if total_time < 5.0 else "🔴 NEEDS IMPROVEMENT"}
        """
        
        return report.strip()
    
    def record_component_time(self, component: str, duration: float):
        """Record timing for specific component"""
        self.metrics[f"{component}_time"] = duration
    
    def is_optimized_startup(self) -> bool:
        """Check if startup was optimized"""
        return self.precompiled_ready and self.optimization_enabled

# Global startup optimizer instance
_startup_optimizer = None

def get_startup_optimizer() -> StartupPerformanceOptimizer:
    """Get global startup optimizer instance"""
    global _startup_optimizer
    if _startup_optimizer is None:
        _startup_optimizer = StartupPerformanceOptimizer()
    return _startup_optimizer

def initialize_optimized_startup():
    """Initialize optimized startup sequence"""
    optimizer = get_startup_optimizer()
    
    print("🚀 Initializing optimized startup sequence...")
    
    # Precompile components
    if optimizer.precompile_components():
        print("✓ Fast startup mode enabled")
        
        # Pre-generate trend data
        trend_data = optimizer.optimize_trend_initialization()
        if trend_data:
            print("✓ Trend controls pre-optimized")
        
        return optimizer
    else:
        print("⚠️ Falling back to standard startup")
        return None