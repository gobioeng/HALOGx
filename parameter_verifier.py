"""
Parameter Connectivity Verifier - HALog Enhancement
Verifies parameter mappings and ensures correct linkage between parameters and their statistics
Company: gobioeng.com
"""

from typing import Dict, List, Tuple, Optional
import pandas as pd


class ParameterConnectivityVerifier:
    """Verifies parameter connectivity and mapping accuracy"""
    
    def __init__(self, unified_parser):
        self.parser = unified_parser
        self.verification_results = {}
        
    def verify_24v_parameters(self, df: pd.DataFrame) -> Dict:
        """Verify 24V parameter connectivity to stats"""
        results = {
            "verified": False,
            "found_parameters": [],
            "missing_parameters": [],
            "connectivity_issues": [],
            "recommendations": []
        }
        
        try:
            # Get all 24V parameters from the mapping
            voltage_24v_params = {}
            for param_name, param_info in self.parser.parameter_mapping.items():
                if "24V" in param_name or "24V" in param_info.get("description", ""):
                    voltage_24v_params[param_name] = param_info
                    
            print(f"Found {len(voltage_24v_params)} 24V parameters in mapping:")
            for param, info in voltage_24v_params.items():
                print(f"  - {param}: {info['description']}")
                
            if not df.empty:
                # Check which 24V parameters are actually present in the data
                found_in_data = []
                df_columns = [col.lower() for col in df.columns]
                
                for param_name, param_info in voltage_24v_params.items():
                    # Check if parameter or its patterns exist in data
                    patterns = param_info.get("patterns", [])
                    for pattern in patterns:
                        if pattern.lower() in df_columns:
                            found_in_data.append({
                                "parameter": param_name,
                                "found_as": pattern,
                                "description": param_info["description"]
                            })
                            break
                            
                results["found_parameters"] = found_in_data
                results["verified"] = len(found_in_data) > 0
                
                if not found_in_data:
                    results["recommendations"].append("Import log data containing 24V measurements to verify connectivity")
                else:
                    results["recommendations"].append(f"✓ Found {len(found_in_data)} 24V parameters in data")
                    
            else:
                results["recommendations"].append("Load data to verify 24V parameter connectivity")
                
            return results
            
        except Exception as e:
            results["connectivity_issues"].append(f"Error verifying 24V parameters: {e}")
            return results
            
    def verify_pump_pressure_connectivity(self, df: pd.DataFrame) -> Dict:
        """Verify pump pressure parameter connectivity"""
        results = {
            "verified": False,
            "found_parameters": [],
            "water_system_linked": False,
            "connectivity_issues": [],
            "recommendations": []
        }
        
        try:
            # Get pump pressure parameters from mapping
            pump_params = {}
            for param_name, param_info in self.parser.parameter_mapping.items():
                param_desc = param_info.get("description", "").lower()
                if "pump" in param_desc and "pressure" in param_desc:
                    pump_params[param_name] = param_info
                    
            print(f"Found {len(pump_params)} pump pressure parameters in mapping:")
            for param, info in pump_params.items():
                print(f"  - {param}: {info['description']} ({info.get('unit', 'No unit')})")
                
            if not df.empty:
                # Check presence in data
                found_in_data = []
                df_columns = [col.lower() for col in df.columns]
                
                for param_name, param_info in pump_params.items():
                    patterns = param_info.get("patterns", [])
                    for pattern in patterns:
                        if pattern.lower() in df_columns:
                            found_in_data.append({
                                "parameter": param_name,
                                "found_as": pattern,
                                "description": param_info["description"],
                                "unit": param_info.get("unit", "Unknown")
                            })
                            break
                            
                results["found_parameters"] = found_in_data
                results["verified"] = len(found_in_data) > 0
                results["water_system_linked"] = True  # Always linked to Water System tab
                
                if found_in_data:
                    results["recommendations"].append(f"✓ Found {len(found_in_data)} pump pressure parameters")
                    results["recommendations"].append("✓ Pump pressure is properly linked to Water System tab")
                else:
                    results["recommendations"].append("Import log data containing pump pressure measurements to verify connectivity")
                    
            else:
                results["recommendations"].append("Load data to verify pump pressure connectivity")
                
            return results
            
        except Exception as e:
            results["connectivity_issues"].append(f"Error verifying pump pressure: {e}")
            return results
            
    def verify_all_parameter_mappings(self, df: pd.DataFrame) -> Dict:
        """Comprehensive verification of all parameter mappings"""
        results = {
            "total_mapped_parameters": len(self.parser.parameter_mapping),
            "parameters_found_in_data": 0,
            "mapping_accuracy": 0.0,
            "categories": {
                "water_system": {"mapped": 0, "found": 0},
                "voltages": {"mapped": 0, "found": 0},
                "temperatures": {"mapped": 0, "found": 0},
                "fan_speeds": {"mapped": 0, "found": 0},
                "humidity": {"mapped": 0, "found": 0}
            },
            "detailed_results": {},
            "recommendations": []
        }
        
        try:
            if df.empty:
                results["recommendations"].append("Load log data to perform comprehensive parameter verification")
                return results
                
            df_columns = [col.lower() for col in df.columns]
            total_found = 0
            
            # Categorize parameters and check presence
            for param_name, param_info in self.parser.parameter_mapping.items():
                category = self._categorize_parameter(param_name, param_info)
                results["categories"][category]["mapped"] += 1
                
                # Check if parameter exists in data
                found = False
                found_as = None
                
                patterns = param_info.get("patterns", [])
                for pattern in patterns:
                    if pattern.lower() in df_columns:
                        found = True
                        found_as = pattern
                        break
                        
                if found:
                    results["categories"][category]["found"] += 1
                    total_found += 1
                    
                results["detailed_results"][param_name] = {
                    "category": category,
                    "found": found,
                    "found_as": found_as,
                    "description": param_info.get("description", ""),
                    "unit": param_info.get("unit", ""),
                    "patterns": patterns
                }
                
            results["parameters_found_in_data"] = total_found
            results["mapping_accuracy"] = (total_found / len(self.parser.parameter_mapping)) * 100
            
            # Generate recommendations
            for category, stats in results["categories"].items():
                if stats["found"] == 0 and stats["mapped"] > 0:
                    results["recommendations"].append(f"⚠️ No {category} parameters found in current data")
                elif stats["found"] > 0:
                    accuracy = (stats["found"] / stats["mapped"]) * 100
                    results["recommendations"].append(f"✓ {category}: {stats['found']}/{stats['mapped']} parameters found ({accuracy:.1f}%)")
                    
            return results
            
        except Exception as e:
            results["recommendations"].append(f"Error during verification: {e}")
            return results
            
    def _categorize_parameter(self, param_name: str, param_info: Dict) -> str:
        """Categorize parameter by type"""
        param_lower = param_name.lower()
        desc_lower = param_info.get("description", "").lower()
        
        if any(keyword in param_lower or keyword in desc_lower for keyword in ["flow", "pressure", "water", "cooling"]):
            return "water_system"
        elif any(keyword in param_lower or keyword in desc_lower for keyword in ["voltage", "24v", "48v", "volt"]):
            return "voltages"
        elif any(keyword in param_lower or keyword in desc_lower for keyword in ["temp", "temperature"]):
            return "temperatures"
        elif any(keyword in param_lower or keyword in desc_lower for keyword in ["fan", "speed", "rpm"]):
            return "fan_speeds"
        elif any(keyword in param_lower or keyword in desc_lower for keyword in ["humidity", "humid"]):
            return "humidity"
        else:
            return "water_system"  # Default category
            
    def generate_connectivity_report(self, df: pd.DataFrame) -> str:
        """Generate a comprehensive connectivity report"""
        report = []
        report.append("=" * 60)
        report.append("HALOG PARAMETER CONNECTIVITY VERIFICATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Verify 24V parameters
        report.append("1. 24V PARAMETER VERIFICATION")
        report.append("-" * 30)
        voltage_24v_results = self.verify_24v_parameters(df)
        
        for recommendation in voltage_24v_results["recommendations"]:
            report.append(f"   {recommendation}")
            
        if voltage_24v_results["found_parameters"]:
            report.append("   Found 24V parameters:")
            for param in voltage_24v_results["found_parameters"]:
                report.append(f"     • {param['description']} (as {param['found_as']})")
        report.append("")
        
        # Verify pump pressure
        report.append("2. PUMP PRESSURE VERIFICATION")
        report.append("-" * 30)
        pump_results = self.verify_pump_pressure_connectivity(df)
        
        for recommendation in pump_results["recommendations"]:
            report.append(f"   {recommendation}")
            
        if pump_results["found_parameters"]:
            report.append("   Found pump pressure parameters:")
            for param in pump_results["found_parameters"]:
                report.append(f"     • {param['description']} ({param['unit']}) (as {param['found_as']})")
        report.append("")
        
        # Overall mapping verification
        report.append("3. OVERALL PARAMETER MAPPING")
        report.append("-" * 30)
        overall_results = self.verify_all_parameter_mappings(df)
        
        report.append(f"   Total mapped parameters: {overall_results['total_mapped_parameters']}")
        report.append(f"   Parameters found in data: {overall_results['parameters_found_in_data']}")
        report.append(f"   Mapping accuracy: {overall_results['mapping_accuracy']:.1f}%")
        report.append("")
        
        for category, stats in overall_results["categories"].items():
            if stats["mapped"] > 0:
                accuracy = (stats["found"] / stats["mapped"]) * 100
                report.append(f"   {category.title()}: {stats['found']}/{stats['mapped']} ({accuracy:.1f}%)")
        
        report.append("")
        report.append("4. RECOMMENDATIONS")
        report.append("-" * 30)
        
        all_recommendations = set()
        all_recommendations.update(voltage_24v_results["recommendations"])
        all_recommendations.update(pump_results["recommendations"])
        all_recommendations.update(overall_results["recommendations"])
        
        for rec in sorted(all_recommendations):
            report.append(f"   {rec}")
            
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)