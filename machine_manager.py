"""
Machine Manager for HALbasic Multi-Machine Log Analysis
Handles machine-specific dataset filtering and management.

This module provides functionality to:
- Extract unique machine serial numbers from uploaded logs
- Filter data by selected machine
- Manage machine-specific analysis contexts
- Handle fallback behavior for single-machine scenarios

Developer: HALog Enhancement Team
Company: gobioeng.com
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from database import DatabaseManager


class MachineManager:
    """Manages machine-specific datasets and analysis contexts for multi-machine support"""
    
    def __init__(self, database_manager: DatabaseManager):
        """Initialize machine manager with database connection"""
        self.db = database_manager
        self._available_machines = []
        self._selected_machine = None
        self._selected_machines = []  # For multi-selection support
        self._machine_data_cache = {}
        
    def get_available_machines(self) -> List[str]:
        """Get list of unique serial numbers available in the database"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT serial_number 
                    FROM water_logs 
                    WHERE serial_number IS NOT NULL 
                    AND serial_number != ''
                    AND serial_number != 'Unknown'
                    ORDER BY serial_number
                """)
                machines = [row[0] for row in cursor.fetchall()]
                self._available_machines = machines
                return machines
        except Exception as e:
            print(f"Error getting available machines: {e}")
            return []
    
    def get_machine_count(self) -> int:
        """Get total number of unique machines in database"""
        return len(self.get_available_machines())
    
    def set_selected_machine(self, machine_id: str, validate=True):
        """Set the currently selected machine for analysis (single selection)
        
        Args:
            machine_id: Machine ID to select
            validate: Whether to validate machine exists (set False for testing)
        """
        if validate:
            available_machines = self.get_available_machines()
            if machine_id not in available_machines and machine_id != "All Machines":
                raise ValueError(f"Machine {machine_id} not found in available machines")
        
        self._selected_machine = machine_id
        # For backward compatibility, reset multi-selection when single machine is selected
        if machine_id == "All Machines":
            self._selected_machines = []
        else:
            self._selected_machines = [machine_id]
        # Clear cached data when selection changes
        self._machine_data_cache.clear()
    
    def set_selected_machines(self, machine_ids: List[str], validate=True):
        """Set multiple selected machines for analysis (multi-selection)
        
        Args:
            machine_ids: List of machine IDs to select
            validate: Whether to validate machines exist (set False for testing)
        """
        if validate:
            available_machines = self.get_available_machines()
            valid_machines = []
            for machine_id in machine_ids:
                if machine_id in available_machines:
                    valid_machines.append(machine_id)
                else:
                    print(f"Warning: Machine {machine_id} not found in available machines")
        else:
            valid_machines = machine_ids
        
        self._selected_machines = valid_machines
        # Update single selection for backward compatibility
        if len(valid_machines) == 1:
            self._selected_machine = valid_machines[0]
        elif len(valid_machines) == 0:
            self._selected_machine = "All Machines"
        else:
            self._selected_machine = "Multiple Machines"
        
        # Clear cached data when selection changes
        self._machine_data_cache.clear()
    
    def get_selected_machines(self) -> List[str]:
        """Get list of currently selected machines"""
        return self._selected_machines.copy()
    
    def is_multi_machine_selected(self) -> bool:
        """Check if multiple machines are selected"""
        return len(self._selected_machines) > 1
    
    def get_selected_machine(self) -> Optional[str]:
        """Get currently selected machine ID"""
        return self._selected_machine
    
    def get_filtered_data(self, data: pd.DataFrame = None) -> pd.DataFrame:
        """Filter data by currently selected machine
        
        Args:
            data: DataFrame to filter. If None, loads raw data from database
            
        Returns:
            Filtered DataFrame for selected machine
        """
        if data is None:
            # Load raw data from database using a simple query
            try:
                with self.db.get_connection() as conn:
                    data = pd.read_sql_query("""
                        SELECT datetime, serial_number, parameter_type, 
                               statistic_type, value, count, unit, description
                        FROM water_logs
                        ORDER BY datetime
                    """, conn)
                    # Convert datetime with flexible parsing
                    if not data.empty and 'datetime' in data.columns:
                        try:
                            data['datetime'] = pd.to_datetime(data['datetime'], format='mixed')
                        except:
                            # Fallback to basic conversion
                            data['datetime'] = pd.to_datetime(data['datetime'], errors='coerce')
            except Exception as e:
                print(f"Error loading raw data: {e}")
                return pd.DataFrame()
        
        if data.empty:
            return data
            
        # If no machine selected or "All Machines" selected, return all data
        if not self._selected_machine or self._selected_machine == "All Machines":
            return data
        
        # If multiple machines selected, return data for all selected machines
        if self.is_multi_machine_selected():
            # Use 'serial' column name for DataFrames from get_all_logs()
            serial_col = 'serial' if 'serial' in data.columns else 'serial_number'
            filtered_data = data[data[serial_col].isin(self._selected_machines)].copy()
            return filtered_data
        
        # Filter by single selected machine
        # Use 'serial' column name for DataFrames from get_all_logs()
        serial_col = 'serial' if 'serial' in data.columns else 'serial_number'
        filtered_data = data[data[serial_col] == self._selected_machine].copy()
        return filtered_data
    
    def get_machine_summary(self, machine_id: str = None) -> Dict[str, Any]:
        """Get summary statistics for a specific machine
        
        Args:
            machine_id: Machine to get summary for. If None, uses selected machine
            
        Returns:
            Dictionary with machine summary statistics
        """
        target_machine = machine_id or self._selected_machine
        if not target_machine or target_machine == "All Machines":
            return self._get_all_machines_summary()
        
        try:
            with self.db.get_connection() as conn:
                # Get record count for machine
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM water_logs 
                    WHERE serial_number = ?
                """, (target_machine,))
                record_count = cursor.fetchone()[0]
                
                # Get parameter count for machine
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT parameter_type) FROM water_logs 
                    WHERE serial_number = ?
                """, (target_machine,))
                parameter_count = cursor.fetchone()[0]
                
                # Get date range for machine
                cursor = conn.execute("""
                    SELECT MIN(datetime), MAX(datetime) FROM water_logs 
                    WHERE serial_number = ?
                """, (target_machine,))
                date_range = cursor.fetchone()
                
                return {
                    'machine_id': target_machine,
                    'record_count': record_count,
                    'parameter_count': parameter_count,
                    'start_date': date_range[0] if date_range[0] else 'N/A',
                    'end_date': date_range[1] if date_range[1] else 'N/A'
                }
        except Exception as e:
            print(f"Error getting machine summary: {e}")
            return {}
    
    def _get_all_machines_summary(self) -> Dict[str, Any]:
        """Get summary for all machines combined"""
        try:
            summary_stats = self.db.get_summary_statistics()
            machines = self.get_available_machines()
            
            return {
                'machine_id': 'All Machines',
                'record_count': summary_stats.get('total_records', 0),
                'parameter_count': summary_stats.get('unique_parameters', 0),
                'machine_count': len(machines),
                'machines': machines
            }
        except Exception as e:
            print(f"Error getting all machines summary: {e}")
            return {}
    
    def auto_select_machine(self) -> str:
        """Auto-select machine based on available data
        
        Returns:
            Selected machine ID or "All Machines"
        """
        machines = self.get_available_machines()
        
        if len(machines) == 0:
            return "No Machines"
        elif len(machines) == 1:
            # Single machine - auto select it
            self.set_selected_machine(machines[0])
            return machines[0]
        else:
            # Multiple machines - default to "All Machines"
            self.set_selected_machine("All Machines")
            return "All Machines"
    
    def get_machine_dropdown_options(self) -> List[str]:
        """Get list of options for machine selection dropdown
        
        Returns:
            List including "All Machines" option plus individual machines
        """
        machines = self.get_available_machines()
        
        if len(machines) == 0:
            return ["No Machines Available"]
        elif len(machines) == 1:
            # Single machine - just show the machine name
            return machines
        else:
            # Multiple machines - show "All Machines" option first
            return ["All Machines"] + machines
    
    def clear_cache(self):
        """Clear internal data cache"""
        self._machine_data_cache.clear()
    
    def get_multi_machine_data(self, data: pd.DataFrame = None) -> Dict[str, pd.DataFrame]:
        """Get data for multiple selected machines, organized by machine ID
        
        Args:
            data: DataFrame to filter. If None, loads from database
            
        Returns:
            Dictionary mapping machine IDs to their filtered data
        """
        if data is None:
            # Load raw data from database
            try:
                with self.db.get_connection() as conn:
                    data = pd.read_sql_query("""
                        SELECT datetime, serial_number, parameter_type, 
                               statistic_type, value, count, unit, description
                        FROM water_logs
                        ORDER BY datetime
                    """, conn)
                    if not data.empty and 'datetime' in data.columns:
                        try:
                            data['datetime'] = pd.to_datetime(data['datetime'], format='mixed')
                        except:
                            data['datetime'] = pd.to_datetime(data['datetime'], errors='coerce')
            except Exception as e:
                print(f"Error loading raw data: {e}")
                return {}
        
        if data.empty:
            return {}
        
        # If no specific machines selected, return all available machines
        if not self._selected_machines or len(self._selected_machines) == 0:
            available_machines = self.get_available_machines()
            result = {}
            # Use 'serial' column name for DataFrames from get_all_logs()
            serial_col = 'serial' if 'serial' in data.columns else 'serial_number'
            for machine in available_machines:
                machine_data = data[data[serial_col] == machine].copy()
                if not machine_data.empty:
                    result[machine] = machine_data
            return result
        
        # Return data for selected machines only
        result = {}
        # Use 'serial' column name for DataFrames from get_all_logs()
        serial_col = 'serial' if 'serial' in data.columns else 'serial_number'
        for machine_id in self._selected_machines:
            machine_data = data[data[serial_col] == machine_id].copy()
            if not machine_data.empty:
                result[machine_id] = machine_data
        return result
    
    def get_machine_color_scheme(self) -> Dict[str, str]:
        """Get color scheme for multi-machine visualization
        
        Returns:
            Dictionary mapping machine IDs to colors
        """
        machines = self.get_available_machines() if not self._selected_machines else self._selected_machines
        
        # Professional color palette for multiple machines
        colors = [
            '#2196F3',  # Blue
            '#4CAF50',  # Green  
            '#FF9800',  # Orange
            '#9C27B0',  # Purple
            '#F44336',  # Red
            '#00BCD4',  # Cyan
            '#795548',  # Brown
            '#607D8B',  # Blue Grey
            '#E91E63',  # Pink
            '#3F51B5',  # Indigo
        ]
        
        machine_colors = {}
        for i, machine in enumerate(machines):
            machine_colors[machine] = colors[i % len(colors)]
        
        return machine_colors