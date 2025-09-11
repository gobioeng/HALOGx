
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Tuple, Any
import traceback


class DataAnalyzer:
    """Comprehensive data analysis engine for LINAC parameters"""
    
    def __init__(self):
        self.parameter_thresholds = {
            # Water System Parameters
            "Cooling Pump Pressure": {
                "min": 170, "max": 230, "optimal_min": 190, "optimal_max": 210,
                "unit": "PSI", "cv_threshold": 0.05
            },
            "Mag Flow": {
                "min": 3, "max": 10, "optimal_min": 5, "optimal_max": 7,
                "unit": "L/min", "cv_threshold": 0.08
            },
            "Flow Target": {
                "min": 2, "max": 5, "optimal_min": 2.8, "optimal_max": 3.5,
                "unit": "L/min", "cv_threshold": 0.06
            },
            "Flow Chiller Water": {
                "min": 8, "max": 18, "optimal_min": 11, "optimal_max": 14,
                "unit": "L/min", "cv_threshold": 0.08
            },
            
            # Voltage Parameters
            "MLC Bank A 24V": {
                "min": 22, "max": 26, "optimal_min": 23.5, "optimal_max": 24.5,
                "unit": "V", "cv_threshold": 0.02
            },
            "MLC Bank B 24V": {
                "min": 22, "max": 26, "optimal_min": 23.5, "optimal_max": 24.5,
                "unit": "V", "cv_threshold": 0.02
            },
            "COL 48V": {
                "min": 46, "max": 50, "optimal_min": 47.5, "optimal_max": 48.5,
                "unit": "V", "cv_threshold": 0.02
            },
            
            # Temperature Parameters
            "Temp Room": {
                "min": 18, "max": 25, "optimal_min": 20, "optimal_max": 23,
                "unit": "°C", "cv_threshold": 0.1
            },
            "Temp PDU": {
                "min": 20, "max": 40, "optimal_min": 25, "optimal_max": 35,
                "unit": "°C", "cv_threshold": 0.15
            },
            "Temp COL Board": {
                "min": 25, "max": 45, "optimal_min": 30, "optimal_max": 40,
                "unit": "°C", "cv_threshold": 0.12
            },
            "Temp Magnetron": {
                "min": 30, "max": 60, "optimal_min": 35, "optimal_max": 50,
                "unit": "°C", "cv_threshold": 0.15
            },
            
            # Fan Speed Parameters
            "Speed FAN 1": {
                "min": 1000, "max": 3000, "optimal_min": 1500, "optimal_max": 2500,
                "unit": "RPM", "cv_threshold": 0.1
            },
            "Speed FAN 2": {
                "min": 1000, "max": 3000, "optimal_min": 1500, "optimal_max": 2500,
                "unit": "RPM", "cv_threshold": 0.1
            },
            "Speed FAN 3": {
                "min": 1000, "max": 3000, "optimal_min": 1500, "optimal_max": 2500,
                "unit": "RPM", "cv_threshold": 0.1
            },
            "Speed FAN 4": {
                "min": 1000, "max": 3000, "optimal_min": 1500, "optimal_max": 2500,
                "unit": "RPM", "cv_threshold": 0.1
            },
            
            # Humidity Parameters
            "Room Humidity": {
                "min": 30, "max": 70, "optimal_min": 40, "optimal_max": 60,
                "unit": "%RH", "cv_threshold": 0.15
            }
        }
    
    def analyze_parameter(self, data: pd.DataFrame, parameter: str) -> Dict[str, Any]:
        """Comprehensive parameter analysis"""
        try:
            if data.empty or parameter not in data.columns:
                return {"error": f"No data available for parameter: {parameter}"}
            
            values = data[parameter].dropna()
            if values.empty:
                return {"error": f"No valid values for parameter: {parameter}"}
            
            # Get threshold configuration
            thresholds = self.parameter_thresholds.get(parameter, {})
            
            # Basic statistics
            analysis = {
                "parameter": parameter,
                "count": len(values),
                "mean": float(values.mean()),
                "median": float(values.median()),
                "std": float(values.std()),
                "min": float(values.min()),
                "max": float(values.max()),
                "cv": float(values.std() / values.mean()) if values.mean() != 0 else float('inf'),
                "unit": thresholds.get("unit", ""),
                "data_range": f"{values.min():.3f} to {values.max():.3f}"
            }
            
            # Quality assessment
            if thresholds:
                analysis.update(self._assess_parameter_quality(values, thresholds))
            
            # Trend analysis
            if len(values) > 5:
                analysis.update(self._analyze_trends(values))
            
            # Outlier detection
            analysis.update(self._detect_outliers(values))
            
            # Statistical tests
            analysis.update(self._run_statistical_tests(values))
            
            return analysis
            
        except Exception as e:
            return {"error": f"Analysis error: {str(e)}"}
    
    def _assess_parameter_quality(self, values: pd.Series, thresholds: Dict) -> Dict:
        """Assess parameter quality against thresholds"""
        analysis = {}
        
        # Threshold compliance
        min_thresh = thresholds.get("min", float('-inf'))
        max_thresh = thresholds.get("max", float('inf'))
        optimal_min = thresholds.get("optimal_min", min_thresh)
        optimal_max = thresholds.get("optimal_max", max_thresh)
        cv_threshold = thresholds.get("cv_threshold", 0.1)
        
        # Compliance rates
        within_range = ((values >= min_thresh) & (values <= max_thresh)).sum()
        within_optimal = ((values >= optimal_min) & (values <= optimal_max)).sum()
        
        analysis.update({
            "range_compliance": float(within_range / len(values) * 100),
            "optimal_compliance": float(within_optimal / len(values) * 100),
            "cv_compliance": "PASS" if values.std() / values.mean() <= cv_threshold else "FAIL",
            "threshold_min": min_thresh,
            "threshold_max": max_thresh,
            "optimal_min": optimal_min,
            "optimal_max": optimal_max
        })
        
        # Overall quality score
        range_score = within_range / len(values)
        optimal_score = within_optimal / len(values)
        cv_score = 1.0 if values.std() / values.mean() <= cv_threshold else 0.5
        
        quality_score = (range_score * 0.4 + optimal_score * 0.4 + cv_score * 0.2) * 100
        
        if quality_score >= 90:
            quality_rating = "Excellent"
        elif quality_score >= 75:
            quality_rating = "Good"
        elif quality_score >= 60:
            quality_rating = "Fair"
        else:
            quality_rating = "Poor"
        
        analysis.update({
            "quality_score": float(quality_score),
            "quality_rating": quality_rating
        })
        
        return analysis
    
    def _analyze_trends(self, values: pd.Series) -> Dict:
        """Analyze parameter trends"""
        try:
            # Simple linear trend
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # Trend classification
            if abs(slope) < std_err:
                trend = "Stable"
            elif slope > 0:
                trend = "Increasing"
            else:
                trend = "Decreasing"
            
            # Change rate
            total_change = values.iloc[-1] - values.iloc[0] if len(values) > 1 else 0
            change_rate = total_change / len(values)
            
            return {
                "trend": trend,
                "slope": float(slope),
                "r_squared": float(r_value ** 2),
                "p_value": float(p_value),
                "trend_strength": "Strong" if abs(r_value) > 0.7 else "Moderate" if abs(r_value) > 0.3 else "Weak",
                "change_rate": float(change_rate),
                "total_change": float(total_change)
            }
            
        except Exception as e:
            return {"trend_error": str(e)}
    
    def _detect_outliers(self, values: pd.Series) -> Dict:
        """Detect outliers using multiple methods"""
        try:
            # IQR method
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            iqr_outliers = ((values < lower_bound) | (values > upper_bound)).sum()
            
            # Z-score method
            z_scores = np.abs(stats.zscore(values))
            z_outliers = (z_scores > 3).sum()
            
            # Modified Z-score method
            median = values.median()
            mad = np.median(np.abs(values - median))
            modified_z_scores = 0.6745 * (values - median) / mad if mad != 0 else np.zeros_like(values)
            modified_z_outliers = (np.abs(modified_z_scores) > 3.5).sum()
            
            return {
                "iqr_outliers": int(iqr_outliers),
                "iqr_outlier_rate": float(iqr_outliers / len(values) * 100),
                "z_score_outliers": int(z_outliers),
                "modified_z_outliers": int(modified_z_outliers),
                "outlier_bounds": {"lower": float(lower_bound), "upper": float(upper_bound)}
            }
            
        except Exception as e:
            return {"outlier_error": str(e)}
    
    def _run_statistical_tests(self, values: pd.Series) -> Dict:
        """Run statistical tests on the data"""
        try:
            results = {}
            
            # Normality test (Shapiro-Wilk for small samples, Anderson-Darling for larger)
            if len(values) <= 5000:
                shapiro_stat, shapiro_p = stats.shapiro(values)
                results.update({
                    "normality_test": "Shapiro-Wilk",
                    "normality_statistic": float(shapiro_stat),
                    "normality_p_value": float(shapiro_p),
                    "is_normal": shapiro_p > 0.05
                })
            else:
                anderson_result = stats.anderson(values, dist='norm')
                results.update({
                    "normality_test": "Anderson-Darling",
                    "normality_statistic": float(anderson_result.statistic),
                    "is_normal": anderson_result.statistic < anderson_result.critical_values[2]  # 5% level
                })
            
            # Stationarity check (simple variance-based)
            if len(values) > 20:
                mid_point = len(values) // 2
                first_half_var = values.iloc[:mid_point].var()
                second_half_var = values.iloc[mid_point:].var()
                variance_ratio = max(first_half_var, second_half_var) / min(first_half_var, second_half_var)
                
                results.update({
                    "variance_ratio": float(variance_ratio),
                    "is_stationary": variance_ratio < 2.0  # Simple threshold
                })
            
            return results
            
        except Exception as e:
            return {"statistical_test_error": str(e)}
    
    def generate_summary_report(self, data: pd.DataFrame) -> str:
        """Generate comprehensive summary report"""
        try:
            if data.empty:
                return "No data available for analysis."
            
            report = []
            report.append("HALog Analysis Report")
            report.append("=" * 50)
            report.append("")
            
            # Overall statistics
            report.append("📊 OVERALL STATISTICS:")
            report.append(f"   Total Records: {len(data):,}")
            
            if 'datetime' in data.columns:
                date_range = data['datetime'].max() - data['datetime'].min()
                report.append(f"   Time Range: {date_range}")
                report.append(f"   From: {data['datetime'].min()}")
                report.append(f"   To: {data['datetime'].max()}")
            
            # Parameter analysis
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            
            if len(numeric_columns) > 0:
                report.append("")
                report.append("📈 PARAMETER ANALYSIS:")
                
                for param in numeric_columns:
                    if param in ['avg', 'min', 'max']:  # Skip statistics columns
                        continue
                    
                    analysis = self.analyze_parameter(data, param)
                    if "error" not in analysis:
                        report.append(f"\n  {param}:")
                        report.append(f"    Count: {analysis['count']:,}")
                        report.append(f"    Mean: {analysis['mean']:.4f} {analysis['unit']}")
                        report.append(f"    Std Dev: {analysis['std']:.4f}")
                        report.append(f"    Range: {analysis['data_range']}")
                        
                        if 'quality_rating' in analysis:
                            report.append(f"    Quality: {analysis['quality_rating']} ({analysis['quality_score']:.1f}%)")
                        
                        if 'trend' in analysis:
                            report.append(f"    Trend: {analysis['trend']} ({analysis['trend_strength']})")
            
            # Data quality summary
            if 'data_quality' in data.columns:
                report.append("")
                report.append("🔍 DATA QUALITY DISTRIBUTION:")
                quality_counts = data['data_quality'].value_counts()
                total = len(data)
                
                for quality, count in quality_counts.items():
                    percentage = (count / total) * 100
                    report.append(f"   {quality}: {count:,} ({percentage:.1f}%)")
            
            return "\n".join(report)
            
        except Exception as e:
            return f"Report generation error: {str(e)}\n\n{traceback.format_exc()}"
    
    def detect_anomalies(self, data: pd.DataFrame, parameter: str, 
                        method: str = "iqr") -> pd.DataFrame:
        """Detect anomalies in parameter data"""
        try:
            if parameter not in data.columns:
                return pd.DataFrame()
            
            values = data[parameter].dropna()
            if values.empty:
                return pd.DataFrame()
            
            if method == "iqr":
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                anomaly_mask = (values < lower_bound) | (values > upper_bound)
                
            elif method == "zscore":
                z_scores = np.abs(stats.zscore(values))
                anomaly_mask = z_scores > 3
                
            else:  # Modified Z-score
                median = values.median()
                mad = np.median(np.abs(values - median))
                if mad == 0:
                    return pd.DataFrame()
                modified_z_scores = 0.6745 * (values - median) / mad
                anomaly_mask = np.abs(modified_z_scores) > 3.5
            
            # Return anomalous records
            anomalies = data.loc[values.index[anomaly_mask]]
            return anomalies
            
        except Exception as e:
            print(f"Anomaly detection error: {e}")
            return pd.DataFrame()
    
    def calculate_parameter_correlation(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix for numeric parameters"""
        try:
            numeric_data = data.select_dtypes(include=[np.number])
            
            if numeric_data.empty:
                return pd.DataFrame()
            
            correlation_matrix = numeric_data.corr()
            return correlation_matrix
            
        except Exception as e:
            print(f"Correlation calculation error: {e}")
            return pd.DataFrame()
    
    def generate_alert_conditions(self, data: pd.DataFrame) -> List[Dict]:
        """Generate alert conditions based on thresholds"""
        alerts = []
        
        try:
            for param, thresholds in self.parameter_thresholds.items():
                if param not in data.columns:
                    continue
                
                values = data[param].dropna()
                if values.empty:
                    continue
                
                latest_value = values.iloc[-1] if len(values) > 0 else None
                if latest_value is None:
                    continue
                
                # Check thresholds
                min_thresh = thresholds.get("min", float('-inf'))
                max_thresh = thresholds.get("max", float('inf'))
                optimal_min = thresholds.get("optimal_min", min_thresh)
                optimal_max = thresholds.get("optimal_max", max_thresh)
                
                alert = {
                    "parameter": param,
                    "current_value": float(latest_value),
                    "unit": thresholds.get("unit", ""),
                    "severity": "normal",
                    "message": ""
                }
                
                if latest_value < min_thresh or latest_value > max_thresh:
                    alert["severity"] = "critical"
                    alert["message"] = f"Value {latest_value:.3f} outside safe range [{min_thresh}-{max_thresh}]"
                elif latest_value < optimal_min or latest_value > optimal_max:
                    alert["severity"] = "warning"
                    alert["message"] = f"Value {latest_value:.3f} outside optimal range [{optimal_min}-{optimal_max}]"
                else:
                    alert["severity"] = "normal"
                    alert["message"] = f"Value {latest_value:.3f} within optimal range"
                
                alerts.append(alert)
        
        except Exception as e:
            print(f"Alert generation error: {e}")
        
        return alerts
