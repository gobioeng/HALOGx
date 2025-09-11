import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest  
from typing import Dict, Tuple
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")


class DataAnalyzer:
    """Enhanced data analyzer with advanced statistical methods and machine learning"""

    def __init__(self):
        self.parameter_thresholds = {
            # Water System Parameters
            "pumpPressure": {
                "min": 170,
                "max": 230,
                "optimal_min": 190,
                "optimal_max": 210,
                "unit": "PSI",
                "cv_threshold": 0.05,
            },
            "magnetronFlow": {
                "min": 3,
                "max": 10,
                "optimal_min": 5,
                "optimal_max": 7,
                "unit": "L/min",
                "cv_threshold": 0.08,
            },
            "Mag Flow": {  # Updated parameter name
                "min": 3,
                "max": 10,
                "optimal_min": 5,
                "optimal_max": 7,
                "unit": "L/min",
                "cv_threshold": 0.08,
            },
            "targetAndCirculatorFlow": {
                "min": 2,
                "max": 5,
                "optimal_min": 2.8,
                "optimal_max": 3.5,
                "unit": "L/min",
                "cv_threshold": 0.06,
            },
            "Flow Target": {  # Updated parameter name
                "min": 2,
                "max": 5,
                "optimal_min": 2.8,
                "optimal_max": 3.5,
                "unit": "L/min",
                "cv_threshold": 0.06,
            },
            "cityWaterFlow": {
                "min": 8,
                "max": 18,
                "optimal_min": 11,
                "optimal_max": 14,
                "unit": "L/min",
                "cv_threshold": 0.07,
            },
            "Flow Chiller Water": {  # Updated parameter name
                "min": 8,
                "max": 18,
                "optimal_min": 11,
                "optimal_max": 14,
                "unit": "L/min",
                "cv_threshold": 0.07,
            },
            "Cooling Pump Pressure": {  # Updated parameter name
                "min": 170,
                "max": 230,
                "optimal_min": 190,
                "optimal_max": 210,
                "unit": "PSI",
                "cv_threshold": 0.05,
            },
            
            # Voltage Parameters
            "MLC Bank A 48V": {
                "min": 46.0,
                "max": 50.0,
                "optimal_min": 47.5,
                "optimal_max": 48.5,
                "unit": "V",
                "cv_threshold": 0.02,
            },
            "MLC Bank B 48V": {
                "min": 46.0,
                "max": 50.0,
                "optimal_min": 47.5,
                "optimal_max": 48.5,
                "unit": "V",
                "cv_threshold": 0.02,
            },
            "MLC Bank A 24V": {
                "min": 23.0,
                "max": 25.0,
                "optimal_min": 23.8,
                "optimal_max": 24.2,
                "unit": "V",
                "cv_threshold": 0.02,
            },
            "MLC Bank B 24V": {
                "min": 23.0,
                "max": 25.0,
                "optimal_min": 23.8,
                "optimal_max": 24.2,
                "unit": "V",
                "cv_threshold": 0.02,
            },
            "COL 24V Monitor": {
                "min": 23.0,
                "max": 25.0,
                "optimal_min": 23.8,
                "optimal_max": 24.2,
                "unit": "V",
                "cv_threshold": 0.02,
            },
            "COL 5V Monitor": {
                "min": 4.8,
                "max": 5.2,
                "optimal_min": 4.9,
                "optimal_max": 5.1,
                "unit": "V",
                "cv_threshold": 0.01,
            },
            
            # Temperature Parameters
            "Temp Magnetron": {
                "min": 20.0,
                "max": 60.0,
                "optimal_min": 30.0,
                "optimal_max": 50.0,
                "unit": "°C",
                "cv_threshold": 0.10,
            },
            "Temp COL Board": {
                "min": 20.0,
                "max": 55.0,
                "optimal_min": 25.0,
                "optimal_max": 45.0,
                "unit": "°C",
                "cv_threshold": 0.08,
            },
            "Temp PDU": {
                "min": 20.0,
                "max": 50.0,
                "optimal_min": 25.0,
                "optimal_max": 40.0,
                "unit": "°C",
                "cv_threshold": 0.08,
            },
            "Temp Room": {
                "min": 18.0,
                "max": 28.0,
                "optimal_min": 20.0,
                "optimal_max": 25.0,
                "unit": "°C",
                "cv_threshold": 0.05,
            },
            "Temp Water Tank": {
                "min": 15.0,
                "max": 30.0,
                "optimal_min": 18.0,
                "optimal_max": 25.0,
                "unit": "°C",
                "cv_threshold": 0.08,
            },
            
            # Fan Speed Parameters
            "Speed FAN 1": {
                "min": 2500,
                "max": 3500,
                "optimal_min": 2800,
                "optimal_max": 3200,
                "unit": "RPM",
                "cv_threshold": 0.05,
            },
            "Speed FAN 2": {
                "min": 2500,
                "max": 3500,
                "optimal_min": 2700,
                "optimal_max": 3100,
                "unit": "RPM",
                "cv_threshold": 0.05,
            },
            "Speed FAN 3": {
                "min": 2500,
                "max": 3500,
                "optimal_min": 2900,
                "optimal_max": 3300,
                "unit": "RPM",
                "cv_threshold": 0.05,
            },
            "Speed FAN 4": {
                "min": 2500,
                "max": 3500,
                "optimal_min": 2750,
                "optimal_max": 3150,
                "unit": "RPM",
                "cv_threshold": 0.05,
            },
            
            # Humidity Parameters
            "Room Humidity": {
                "min": 30.0,
                "max": 70.0,
                "optimal_min": 40.0,
                "optimal_max": 60.0,
                "unit": "%",
                "cv_threshold": 0.15,
            },
        }

        # Machine learning models for anomaly detection
        self.anomaly_models = {}
        self.scalers = {}

    def calculate_comprehensive_statistics(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive statistics with confidence intervals and advanced metrics"""
        if data.empty:
            return pd.DataFrame()

        try:
            stats_list = []

            for param_type in data["parameter_type"].unique():
                param_data = data[data["parameter_type"] == param_type]

                for stat_type in param_data["statistic_type"].unique():
                    values = param_data[param_data["statistic_type"] == stat_type][
                        "value"
                    ]

                    if len(values) == 0:
                        continue

                    # Basic statistics
                    stats_dict = {
                        "parameter": param_type,
                        "statistic_type": stat_type,
                        "count": len(values),
                        "mean": values.mean(),
                        "median": values.median(),
                        "std": values.std(),
                        "min": values.min(),
                        "max": values.max(),
                        "q25": values.quantile(0.25),
                        "q75": values.quantile(0.75),
                        "unit": (
                            param_data["unit"].iloc[0] if not param_data.empty else ""
                        ),
                    }

                    # Advanced statistics
                    stats_dict.update(self._calculate_advanced_statistics(values))

                    # Confidence intervals
                    stats_dict.update(self._calculate_confidence_intervals(values))

                    # Trend analysis
                    if len(values) > 5:
                        stats_dict.update(self._calculate_trend_statistics(values))

                    # Quality assessment
                    stats_dict.update(self._assess_data_quality(values, param_type))

                    stats_list.append(stats_dict)

            if stats_list:
                return pd.DataFrame(stats_list)
            else:
                return pd.DataFrame()

        except Exception as e:
            print(f"Error calculating comprehensive statistics: {e}")
            return pd.DataFrame()

    def _calculate_advanced_statistics(self, values: pd.Series) -> Dict:
        """Calculate advanced statistical measures"""
        try:
            # Coefficient of variation
            cv = values.std() / abs(values.mean()) if values.mean() != 0 else np.inf

            # IQR and outlier detection
            q25, q75 = values.quantile(0.25), values.quantile(0.75)
            iqr = q75 - q25
            lower_bound = q25 - 1.5 * iqr
            upper_bound = q75 + 1.5 * iqr
            outliers = values[(values < lower_bound) | (values > upper_bound)]

            # Shape statistics
            skewness = stats.skew(values.dropna())
            kurtosis = stats.kurtosis(values.dropna())

            # Normality test
            if len(values) >= 3:
                shapiro_stat, shapiro_p = stats.shapiro(values.dropna())
            else:
                shapiro_stat, shapiro_p = np.nan, np.nan

            # Range statistics
            value_range = values.max() - values.min()
            relative_range = (
                value_range / values.mean() if values.mean() != 0 else np.inf
            )

            # Stability metrics
            rolling_std = values.rolling(window=min(10, len(values) // 2)).std().mean()
            stability_score = 1 / (1 + cv) if cv < np.inf else 0

            return {
                "cv": cv,
                "iqr": iqr,
                "outlier_count": len(outliers),
                "outlier_percentage": (len(outliers) / len(values)) * 100,
                "skewness": skewness,
                "kurtosis": kurtosis,
                "shapiro_stat": shapiro_stat,
                "shapiro_p_value": shapiro_p,
                "is_normal": shapiro_p > 0.05 if not np.isnan(shapiro_p) else None,
                "range": value_range,
                "relative_range": relative_range,
                "rolling_std": rolling_std,
                "stability_score": stability_score,
            }

        except Exception as e:
            print(f"Error calculating advanced statistics: {e}")
            return {}

    def _calculate_confidence_intervals(
        self, values: pd.Series, confidence_level: float = 0.95
    ) -> Dict:
        """Calculate confidence intervals for mean and median"""
        try:
            if len(values) < 2:
                return {
                    "mean_ci_lower": np.nan,
                    "mean_ci_upper": np.nan,
                    "median_ci_lower": np.nan,
                    "median_ci_upper": np.nan,
                }

            # Confidence interval for mean
            mean = values.mean()
            sem = stats.sem(values.dropna())
            t_critical = stats.t.ppf((1 + confidence_level) / 2, len(values) - 1)
            mean_margin = t_critical * sem

            # Bootstrap confidence interval for median
            n_bootstrap = 1000
            bootstrap_medians = []

            for _ in range(n_bootstrap):
                bootstrap_sample = values.sample(n=len(values), replace=True)
                bootstrap_medians.append(bootstrap_sample.median())

            median_ci_lower = np.percentile(
                bootstrap_medians, (1 - confidence_level) / 2 * 100
            )
            median_ci_upper = np.percentile(
                bootstrap_medians, (1 + confidence_level) / 2 * 100
            )

            return {
                "mean_ci_lower": mean - mean_margin,
                "mean_ci_upper": mean + mean_margin,
                "median_ci_lower": median_ci_lower,
                "median_ci_upper": median_ci_upper,
                "confidence_level": confidence_level,
            }

        except Exception as e:
            print(f"Error calculating confidence intervals: {e}")
            return {
                "mean_ci_lower": np.nan,
                "mean_ci_upper": np.nan,
                "median_ci_lower": np.nan,
                "median_ci_upper": np.nan,
            }

    def _calculate_trend_statistics(self, values: pd.Series) -> Dict:
        """Calculate trend-related statistics"""
        try:
            if len(values) < 3:
                return {
                    "trend_slope": np.nan,
                    "trend_r2": np.nan,
                    "trend_p_value": np.nan,
                }

            # Linear trend
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)

            # Trend direction
            if p_value < 0.05:
                if slope > 0:
                    trend_direction = "increasing"
                elif slope < 0:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "no_significant_trend"

            # Mann-Kendall test for monotonic trend
            mk_stat, mk_p_value = self._mann_kendall_test(values)

            return {
                "trend_slope": slope,
                "trend_r2": r_value**2,
                "trend_p_value": p_value,
                "trend_direction": trend_direction,
                "trend_strength": (
                    "strong"
                    if abs(r_value) > 0.7
                    else "moderate" if abs(r_value) > 0.3 else "weak"
                ),
                "mk_statistic": mk_stat,
                "mk_p_value": mk_p_value,
            }

        except Exception as e:
            print(f"Error calculating trend statistics: {e}")
            return {"trend_slope": np.nan, "trend_r2": np.nan, "trend_p_value": np.nan}

    def _mann_kendall_test(self, values: pd.Series) -> Tuple[float, float]:
        """Perform Mann-Kendall test for monotonic trend"""
        try:
            n = len(values)
            if n < 3:
                return np.nan, np.nan

            # Calculate S statistic
            s = 0
            for i in range(n - 1):
                for j in range(i + 1, n):
                    s += np.sign(values.iloc[j] - values.iloc[i])

            # Calculate variance
            var_s = n * (n - 1) * (2 * n + 5) / 18

            # Calculate Z statistic
            if s > 0:
                z = (s - 1) / np.sqrt(var_s)
            elif s < 0:
                z = (s + 1) / np.sqrt(var_s)
            else:
                z = 0

            # Calculate p-value
            p_value = 2 * (1 - stats.norm.cdf(abs(z)))

            return s, p_value

        except Exception as e:
            print(f"Error in Mann-Kendall test: {e}")
            return np.nan, np.nan

    def _assess_data_quality(self, values: pd.Series, parameter: str) -> Dict:
        """Assess data quality based on parameter-specific criteria"""
        try:
            quality_score = 100.0
            quality_issues = []

            # Check for missing values
            missing_ratio = values.isna().sum() / len(values)
            if missing_ratio > 0.1:
                quality_score -= 20
                quality_issues.append(f"High missing value ratio: {missing_ratio:.1%}")

            # Check for parameter-specific thresholds
            if parameter in self.parameter_thresholds:
                thresholds = self.parameter_thresholds[parameter]

                # Check range violations
                out_of_range = (
                    (values < thresholds["min"]) | (values > thresholds["max"])
                ).sum()
                if out_of_range > 0:
                    quality_score -= min(30, out_of_range / len(values) * 100)
                    quality_issues.append(
                        f"Values outside acceptable range: {out_of_range}"
                    )

                # Check stability
                cv = values.std() / abs(values.mean()) if values.mean() != 0 else np.inf
                if cv > thresholds["cv_threshold"]:
                    quality_score -= 15
                    quality_issues.append(f"High variability (CV={cv:.3f})")

            # Check for constant values
            if values.nunique() == 1:
                quality_score -= 25
                quality_issues.append("All values are identical")

            # Check for extreme outliers (>3 standard deviations)
            if len(values) > 3:
                z_scores = np.abs(stats.zscore(values.dropna()))
                extreme_outliers = (z_scores > 3).sum()
                if extreme_outliers > 0:
                    quality_score -= min(20, extreme_outliers / len(values) * 100)
                    quality_issues.append(
                        f"Extreme outliers detected: {extreme_outliers}"
                    )

            # Determine quality grade
            if quality_score >= 90:
                quality_grade = "excellent"
            elif quality_score >= 75:
                quality_grade = "good"
            elif quality_score >= 60:
                quality_grade = "fair"
            else:
                quality_grade = "poor"

            return {
                "quality_score": quality_score,
                "quality_grade": quality_grade,
                "quality_issues": (
                    "; ".join(quality_issues) if quality_issues else "None"
                ),
            }

        except Exception as e:
            print(f"Error assessing data quality: {e}")
            return {
                "quality_score": np.nan,
                "quality_grade": "unknown",
                "quality_issues": f"Error: {str(e)}",
            }

    def detect_advanced_anomalies(self, data: pd.DataFrame) -> pd.DataFrame:
        """Detect anomalies using multiple advanced techniques"""
        if data.empty:
            return pd.DataFrame()

        try:
            anomaly_results = []

            for param_type in data["parameter_type"].unique():
                param_data = data[data["parameter_type"] == param_type]

                for stat_type in [
                    "avg"
                ]:  # Focus on average values for anomaly detection
                    values = param_data[param_data["statistic_type"] == stat_type]

                    if len(values) < 10:  # Need sufficient data for anomaly detection
                        continue

                    # Prepare data
                    X = values[["value"]].values
                    timestamps = values["datetime"].values

                    # Method 1: Isolation Forest
                    iso_forest = IsolationForest(contamination=0.1, random_state=42)
                    iso_anomalies = iso_forest.fit_predict(X)

                    # Method 2: Statistical outliers (Z-score)
                    z_scores = np.abs(stats.zscore(X.flatten()))
                    z_anomalies = z_scores > 3

                    # Method 3: IQR-based outliers
                    Q1 = np.percentile(X, 25)
                    Q3 = np.percentile(X, 75)
                    IQR = Q3 - Q1
                    iqr_anomalies = (X.flatten() < (Q1 - 1.5 * IQR)) | (
                        X.flatten() > (Q3 + 1.5 * IQR)
                    )

                    # Combine anomaly detection results
                    for i, (timestamp, value) in enumerate(
                        zip(timestamps, X.flatten())
                    ):
                        anomaly_score = 0
                        anomaly_methods = []

                        if iso_anomalies[i] == -1:
                            anomaly_score += 1
                            anomaly_methods.append("IsolationForest")

                        if z_anomalies[i]:
                            anomaly_score += 1
                            anomaly_methods.append("Z-score")

                        if iqr_anomalies[i]:
                            anomaly_score += 1
                            anomaly_methods.append("IQR")

                        if anomaly_score > 0:
                            anomaly_results.append(
                                {
                                    "datetime": timestamp,
                                    "parameter_type": param_type,
                                    "statistic_type": stat_type,
                                    "value": value,
                                    "anomaly_score": anomaly_score,
                                    "anomaly_methods": ", ".join(anomaly_methods),
                                    "severity": (
                                        "High"
                                        if anomaly_score >= 2
                                        else "Medium" if anomaly_score == 1 else "Low"
                                    ),
                                }
                            )

            if anomaly_results:
                return pd.DataFrame(anomaly_results)
            else:
                return pd.DataFrame()

        except Exception as e:
            print(f"Error detecting anomalies: {e}")
            return pd.DataFrame()

    def calculate_advanced_trends(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate advanced trend analysis"""
        if data.empty:
            return pd.DataFrame()

        try:
            trend_results = []

            for param_type in data["parameter_type"].unique():
                param_data = data[data["parameter_type"] == param_type]

                for stat_type in ["avg"]:  # Focus on average values for trend analysis
                    values_df = param_data[
                        param_data["statistic_type"] == stat_type
                    ].sort_values("datetime")

                    if len(values_df) < 5:  # Need sufficient data for trend analysis
                        continue

                    values = values_df["value"]

                    # Calculate trend statistics
                    trend_stats = self._calculate_trend_statistics(values)

                    # Add parameter information
                    trend_result = {
                        "parameter_type": param_type,
                        "statistic_type": stat_type,
                        "data_points": len(values),
                        "time_span_hours": (
                            values_df["datetime"].max() - values_df["datetime"].min()
                        ).total_seconds()
                        / 3600,
                        **trend_stats,
                    }

                    trend_results.append(trend_result)

            if trend_results:
                return pd.DataFrame(trend_results)
            else:
                return pd.DataFrame()

        except Exception as e:
            print(f"Error calculating trends: {e}")
            return pd.DataFrame()
