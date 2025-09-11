"""
Enhanced Database Manager - Gobioeng HALog
Provides optimized database operations for LINAC water system data
Enhanced with backup and recovery capabilities
"""

import sqlite3
import pandas as pd
from typing import Optional, Dict, List
import os
from functools import reduce
import time
import traceback
from contextlib import contextmanager


class DatabaseManager:
    """Enhanced database manager with batch operations, optimized queries, and backup support"""

    def __init__(self, db_path: str = None):
        # Import backup manager
        from database_backup_manager import DatabaseBackupManager
        
        # Initialize backup manager first
        self.backup_manager = DatabaseBackupManager()
        
        # Use backup manager's database path if none specified
        if db_path is None:
            self.db_path = self.backup_manager.get_main_db_path()
        else:
            self.db_path = db_path
            
        self.connection_pool = {}
        self.prepared_statements = {}
        
        # Setup crash recovery and backup system
        self._setup_database_resilience()
        
        # Initialize database
        self.init_db()
        
    def _setup_database_resilience(self):
        """Setup database backup and crash recovery system"""
        try:
            # Ensure backup system is ready
            self.backup_manager.setup_crash_recovery()
            
            # Check if database file exists and is valid
            if os.path.exists(self.db_path):
                if not self._verify_database_health():
                    print("⚠️ Database corruption detected!")
                    self._handle_database_corruption()
            
            print("✓ Database resilience system initialized")
        except Exception as e:
            print(f"Warning: Could not setup database resilience: {e}")
            
    def _verify_database_health(self) -> bool:
        """Verify database file integrity and accessibility"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                if result[0] != "ok":
                    return False
                    
                # Try a simple query
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                return True
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False
            
    def _handle_database_corruption(self):
        """Handle database corruption with user prompt for recovery"""
        try:
            backup_filename = self.backup_manager.handle_database_corruption()
            
            if backup_filename:
                # For now, automatically restore the most recent backup
                # In a GUI environment, this would show a dialog
                print(f"🔄 Attempting automatic recovery from backup: {backup_filename}")
                if self.backup_manager.restore_backup(backup_filename):
                    print("✅ Database successfully restored from backup")
                else:
                    print("❌ Failed to restore database from backup")
            else:
                print("❌ No backup available for recovery")
        except Exception as e:
            print(f"Error handling database corruption: {e}")

    def init_db(self):
        """Initialize database with enhanced schema and performance optimizations"""
        with self.get_connection() as conn:
            # Enable performance optimizations
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=50000")  # Increased cache size
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory mapping
            conn.execute("PRAGMA page_size=8192")  # Larger page size for better performance
            conn.execute("PRAGMA optimize")  # Optimize database statistics
            
            # Connection-specific optimizations
            conn.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout

            # Create tables if they don't exist
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS water_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    datetime TEXT NOT NULL,
                    serial_number TEXT NOT NULL,
                    parameter_type TEXT NOT NULL,
                    statistic_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    count INTEGER,
                    unit TEXT,
                    description TEXT,
                    data_quality TEXT,
                    raw_parameter TEXT,
                    line_number INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create optimized indices
            self._create_indices(conn)

            # Create metadata table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS file_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_size INTEGER,
                    records_imported INTEGER,
                    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    parsing_stats TEXT
                )
            """
            )

            conn.commit()

    def _create_indices(self, conn):
        """Create optimized database indices"""
        # Check if indices already exist to avoid redundant operations
        indices = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
        existing_indices = [idx[0] for idx in indices]

        index_definitions = [
            (
                "idx_datetime",
                "CREATE INDEX IF NOT EXISTS idx_datetime ON water_logs(datetime)",
            ),
            (
                "idx_parameter_type",
                "CREATE INDEX IF NOT EXISTS idx_parameter_type ON water_logs(parameter_type)",
            ),
            (
                "idx_serial_parameter",
                "CREATE INDEX IF NOT EXISTS idx_serial_parameter ON water_logs(serial_number, parameter_type)",
            ),
            (
                "idx_datetime_parameter",
                "CREATE INDEX IF NOT EXISTS idx_datetime_parameter ON water_logs(datetime, parameter_type)",
            ),
            (
                "idx_statistic_type",
                "CREATE INDEX IF NOT EXISTS idx_statistic_type ON water_logs(statistic_type)",
            ),
            (
                "idx_combined",
                "CREATE INDEX IF NOT EXISTS idx_combined ON water_logs(datetime, serial_number, parameter_type, statistic_type)",
            ),
        ]

        for idx_name, idx_query in index_definitions:
            if idx_name not in existing_indices:
                conn.execute(idx_query)

    @contextmanager
    def get_connection(self):
        """Get a database connection with thread safety and performance optimizations"""
        # Thread-safe connection pool
        import threading

        thread_id = threading.get_ident()

        if thread_id not in self.connection_pool:
            self.connection_pool[thread_id] = sqlite3.connect(
                self.db_path, timeout=30.0, isolation_level=None
            )
            conn = self.connection_pool[thread_id]
            
            # Apply performance optimizations to new connections
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=50000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")
            conn.execute("PRAGMA busy_timeout=30000")

        conn = self.connection_pool[thread_id]
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            # Don't close the connection, keep it in the pool
            pass

    def insert_data_batch(self, df: pd.DataFrame, batch_size: int = 1000) -> int:
        """Insert data in optimized batches for better performance"""
        if df.empty:
            return 0

        total_inserted = 0
        start_time = time.time()

        try:
            with self.get_connection() as conn:
                # Begin transaction for all inserts
                conn.execute("BEGIN TRANSACTION")

                # Prepare DataFrame for insertion
                df_clean = df.copy()
                if (
                    "datetime" in df_clean.columns
                    and pd.api.types.is_datetime64_any_dtype(df_clean["datetime"])
                ):
                    df_clean["datetime"] = df_clean["datetime"].dt.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                # Ensure all required columns exist
                columns_to_insert = [
                    "datetime",
                    "serial_number",
                    "parameter_type",
                    "statistic_type",
                    "value",
                    "count",
                    "unit",
                    "description",
                    "data_quality",
                    "raw_parameter",
                    "line_number",
                ]

                for col in columns_to_insert:
                    if col not in df_clean.columns:
                        df_clean[col] = None

                # Prepare the insert statement once
                insert_sql = """
                    INSERT INTO water_logs
                    (datetime, serial_number, parameter_type, statistic_type,
                     value, count, unit, description, data_quality,
                     raw_parameter, line_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                # Process in batches for memory efficiency
                for start_idx in range(0, len(df_clean), batch_size):
                    end_idx = min(start_idx + batch_size, len(df_clean))
                    batch_df = df_clean.iloc[start_idx:end_idx]
                    data_to_insert = batch_df[columns_to_insert].values.tolist()

                    # Execute batch insert
                    conn.executemany(insert_sql, data_to_insert)
                    total_inserted += len(batch_df)

                    # Intermediate commit for very large datasets to avoid transaction overhead
                    if total_inserted % 10000 == 0:
                        conn.execute("COMMIT")
                        conn.execute("BEGIN TRANSACTION")

                # Final commit
                conn.execute("COMMIT")

                # Log performance metrics
                elapsed = time.time() - start_time
                print(
                    f"Batch insert completed: {total_inserted:,} records in {elapsed:.2f}s ({total_inserted/elapsed:.1f} records/sec)"
                )

        except Exception as e:
            print(f"Error inserting data: {e}")
            traceback.print_exc()
            return 0

        return total_inserted

    def insert_file_metadata(
        self, filename: str, file_size: int, records_imported: int, parsing_stats: str
    ):
        """Insert file metadata with error handling"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO file_metadata
                    (filename, file_size, records_imported, parsing_stats)
                    VALUES (?, ?, ?, ?)
                """,
                    (filename, file_size, records_imported, parsing_stats),
                )
        except Exception as e:
            print(f"Error inserting file metadata: {e}")
            traceback.print_exc()

    def get_all_logs(
        self, limit: Optional[int] = None, chunk_size: int = None
    ) -> pd.DataFrame:
        """
        Get all logs with memory-optimized processing for large datasets
        """
        try:
            with self.get_connection() as conn:
                stats = ["avg", "min", "max"]
                frames = []

                # Process each statistic type separately for memory efficiency
                for stat in stats:
                    stat_query = f"""
                        SELECT
                            datetime,
                            serial_number AS serial,
                            parameter_type AS param,
                            value AS {stat},
                            unit
                        FROM water_logs
                        WHERE statistic_type = ?
                    """

                    # Add limit if specified
                    if limit:
                        stat_query += f" LIMIT {limit}"

                    # Use chunked reading for large datasets
                    if chunk_size:
                        chunks = []
                        for chunk in pd.read_sql_query(
                            stat_query,
                            conn,
                            params=[stat],
                            parse_dates=["datetime"],
                            chunksize=chunk_size,
                        ):
                            chunks.append(chunk)

                        if chunks:
                            df_stat = pd.concat(chunks)
                        else:
                            df_stat = pd.DataFrame()
                    else:
                        df_stat = pd.read_sql_query(
                            stat_query, conn, params=[stat], parse_dates=["datetime"]
                        )

                    print(f"Retrieved {len(df_stat)} records for statistic type '{stat}'")
                    frames.append(df_stat)

                # Only return empty if ALL frames are empty (more lenient)
                non_empty_frames = [df for df in frames if not df.empty]
                if not non_empty_frames:
                    print("⚠️ No data found for any statistic type")
                    return pd.DataFrame()
                
                # Use only non-empty frames for merging
                if len(non_empty_frames) == 1:
                    df_merged = non_empty_frames[0].copy()
                    # Add missing columns with NaN values
                    for stat in stats:
                        if stat not in df_merged.columns:
                            df_merged[stat] = pd.NA
                else:
                    # Optimize merge for memory efficiency
                    def merge_func(left, right):
                        return pd.merge(
                            left,
                            right,
                            on=["datetime", "serial", "param", "unit"],
                            how="outer",
                            # Use copy=False for memory efficiency (modifies in place)
                            copy=False,
                        )

                    df_merged = reduce(merge_func, non_empty_frames)

                # Calculate diff column safely
                if 'max' in df_merged.columns and 'min' in df_merged.columns:
                    df_merged["diff"] = df_merged["max"] - df_merged["min"]
                else:
                    df_merged["diff"] = 0
                
                print(f"Final merged dataset: {len(df_merged)} records with columns: {list(df_merged.columns)}")

                return df_merged

        except Exception as e:
            print(f"Error retrieving logs: {e}")
            traceback.print_exc()
            return pd.DataFrame()

    def diagnose_data_issues(self) -> Dict:
        """Diagnose potential data issues that could cause dashboard problems"""
        try:
            with self.get_connection() as conn:
                diagnosis = {
                    "issues_found": [],
                    "recommendations": [],
                    "data_health": "good"
                }
                
                # Check 1: Total records
                total_records = conn.execute("SELECT COUNT(*) FROM water_logs").fetchone()[0]
                if total_records == 0:
                    diagnosis["issues_found"].append("No data in database")
                    diagnosis["recommendations"].append("Import LINAC log files")
                    diagnosis["data_health"] = "critical"
                    return diagnosis
                
                # Check 2: Statistic type distribution
                stat_types = conn.execute("""
                    SELECT statistic_type, COUNT(*) as count 
                    FROM water_logs 
                    GROUP BY statistic_type
                """).fetchall()
                
                stat_dict = dict(stat_types)
                required_stats = ['avg', 'min', 'max']
                missing_stats = [stat for stat in required_stats if stat not in stat_dict]
                
                if missing_stats:
                    diagnosis["issues_found"].append(f"Missing statistic types: {missing_stats}")
                    diagnosis["recommendations"].append("Check data parsing and import process")
                    diagnosis["data_health"] = "poor"
                
                # Check 3: Parameter diversity
                param_count = conn.execute("SELECT COUNT(DISTINCT parameter_type) FROM water_logs").fetchone()[0]
                if param_count < 3:
                    diagnosis["issues_found"].append(f"Low parameter diversity: only {param_count} unique parameters")
                    diagnosis["recommendations"].append("Import more comprehensive log files")
                    if diagnosis["data_health"] == "good":
                        diagnosis["data_health"] = "fair"
                
                # Check 4: Recent data availability
                recent_data = conn.execute("""
                    SELECT COUNT(*) FROM water_logs 
                    WHERE datetime >= datetime('now', '-7 days')
                """).fetchone()[0]
                
                if recent_data == 0:
                    diagnosis["issues_found"].append("No recent data (last 7 days)")
                    diagnosis["recommendations"].append("Import recent log files")
                    if diagnosis["data_health"] == "good":
                        diagnosis["data_health"] = "fair"
                
                # Check 5: Serial number consistency
                serial_count = conn.execute("SELECT COUNT(DISTINCT serial_number) FROM water_logs").fetchone()[0]
                if serial_count == 0:
                    diagnosis["issues_found"].append("No valid serial numbers found")
                    diagnosis["recommendations"].append("Check log file format and parsing")
                    diagnosis["data_health"] = "poor"
                
                # Summary
                diagnosis["total_records"] = total_records
                diagnosis["unique_parameters"] = param_count
                diagnosis["unique_serials"] = serial_count
                diagnosis["statistic_distribution"] = stat_dict
                
                return diagnosis
                
        except Exception as e:
            return {
                "issues_found": [f"Database error: {str(e)}"],
                "recommendations": ["Check database connectivity and integrity"],
                "data_health": "critical",
                "error": str(e)
            }

    def get_logs_by_parameter(
        self,
        parameter_type: str,
        serial_number: Optional[str] = None,
        chunk_size: Optional[int] = None,
    ) -> pd.DataFrame:
        """Get logs filtered by parameter type with chunked processing"""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT
                        datetime,
                        serial_number as serial,
                        parameter_type as param,
                        value as avg,
                        unit,
                        statistic_type,
                        data_quality
                    FROM water_logs
                    WHERE parameter_type = ?
                """
                params = [parameter_type]

                if serial_number:
                    query += " AND serial_number = ?"
                    params.append(serial_number)

                query += " ORDER BY datetime ASC"

                # Use chunked reading for large datasets
                if chunk_size:
                    chunks = []
                    for chunk in pd.read_sql_query(
                        query,
                        conn,
                        params=params,
                        parse_dates=["datetime"],
                        chunksize=chunk_size,
                    ):
                        chunks.append(chunk)

                    if chunks:
                        return pd.concat(chunks)
                    return pd.DataFrame()
                else:
                    return pd.read_sql_query(
                        query, conn, params=params, parse_dates=["datetime"]
                    )

        except Exception as e:
            print(f"Error retrieving parameter logs: {e}")
            traceback.print_exc()
            return pd.DataFrame()

    def get_recent_logs(self, limit: int = 1000) -> pd.DataFrame:
        """Get recent logs for fast startup - optimized for performance"""
        try:
            with self.get_connection() as conn:
                # Get only recent records with average values for quick loading
                query = """
                    SELECT
                        datetime,
                        serial_number as serial,
                        parameter_type as param,
                        value as avg,
                        unit
                    FROM water_logs
                    WHERE statistic_type = 'avg'
                    ORDER BY datetime DESC
                    LIMIT ?
                """
                
                df = pd.read_sql_query(
                    query, 
                    conn, 
                    params=[limit], 
                    parse_dates=["datetime"]
                )
                
                # Reverse to get chronological order
                if not df.empty:
                    df = df.iloc[::-1].reset_index(drop=True)
                
                return df

        except Exception as e:
            print(f"Error retrieving recent logs: {e}")
            traceback.print_exc()
            return pd.DataFrame()

    def get_summary_statistics(self) -> Dict:
        """Get summary statistics with optimized queries"""
        try:
            with self.get_connection() as conn:
                # Use a single transaction for better performance
                conn.execute("BEGIN")

                # Get basic counts with optimized queries
                total_records = conn.execute(
                    "SELECT COUNT(*) FROM water_logs"
                ).fetchone()[0]

                unique_params = conn.execute(
                    "SELECT COUNT(DISTINCT parameter_type) FROM water_logs"
                ).fetchone()[0]

                unique_serials = conn.execute(
                    "SELECT COUNT(DISTINCT serial_number) FROM water_logs"
                ).fetchone()[0]

                date_range = conn.execute(
                    "SELECT MIN(datetime), MAX(datetime) FROM water_logs"
                ).fetchone()

                # Get quality distribution efficiently
                quality_dist = pd.read_sql_query(
                    """
                    SELECT data_quality, COUNT(*) as count
                    FROM water_logs
                    GROUP BY data_quality
                    """,
                    conn,
                )

                conn.execute("COMMIT")

                return {
                    "total_records": total_records,
                    "unique_parameters": unique_params,
                    "unique_serials": unique_serials,
                    "date_range": date_range,
                    "quality_distribution": (
                        quality_dist.to_dict("records")
                        if not quality_dist.empty
                        else []
                    ),
                }

        except Exception as e:
            print(f"Error getting summary statistics: {e}")
            traceback.print_exc()
            return {}

    def get_file_history(self, chunk_size: Optional[int] = None) -> pd.DataFrame:
        """Get file import history with chunked reading"""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT
                        filename,
                        file_size,
                        records_imported,
                        import_timestamp,
                        parsing_stats
                    FROM file_metadata
                    ORDER BY import_timestamp DESC
                """

                if chunk_size:
                    chunks = []
                    for chunk in pd.read_sql_query(
                        query,
                        conn,
                        parse_dates=["import_timestamp"],
                        chunksize=chunk_size,
                    ):
                        chunks.append(chunk)

                    if chunks:
                        return pd.concat(chunks)
                    return pd.DataFrame()
                else:
                    return pd.read_sql_query(
                        query, conn, parse_dates=["import_timestamp"]
                    )

        except Exception as e:
            print(f"Error retrieving file history: {e}")
            traceback.print_exc()
            return pd.DataFrame()

    def clear_all(self):
        """Clear all data with optimized transaction handling"""
        try:
            with self.get_connection() as conn:
                conn.execute("BEGIN TRANSACTION")
                conn.execute("DELETE FROM water_logs")
                conn.execute("DELETE FROM file_metadata")
                conn.execute("COMMIT")

                # Reset auto-increment counters
                conn.execute("BEGIN TRANSACTION")
                conn.execute("DELETE FROM sqlite_sequence WHERE name='water_logs'")
                conn.execute("DELETE FROM sqlite_sequence WHERE name='file_metadata'")
                conn.execute("COMMIT")

        except Exception as e:
            print(f"Error clearing database: {e}")
            traceback.print_exc()

    def vacuum_database(self):
        """Optimize database by running VACUUM"""
        try:
            # VACUUM requires its own connection
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                print("Database vacuumed successfully")
        except Exception as e:
            print(f"Error vacuuming database: {e}")
            traceback.print_exc()

    def get_database_size(self) -> int:
        """Get database file size in bytes with error handling"""
        try:
            return os.path.getsize(self.db_path)
        except Exception as e:
            print(f"Error getting database size: {e}")
            return 0

    def optimize_for_reading(self):
        """Apply optimizations for read performance"""
        try:
            with self.get_connection() as conn:
                # Memory and performance optimizations
                conn.execute("PRAGMA cache_size=20000")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.execute("PRAGMA mmap_size=30000000")

                # Analyze tables for query planner
                conn.execute("ANALYZE water_logs")
                conn.execute("ANALYZE file_metadata")

                print("Database optimized for reading")
        except Exception as e:
            print(f"Error optimizing DB: {e}")
            traceback.print_exc()

    def get_record_count(self) -> int:
        """Get total record count from database"""
        try:
            with self.get_connection() as conn:
                result = conn.execute("SELECT COUNT(*) FROM water_logs").fetchone()
                return result[0] if result else 0
        except Exception as e:
            print(f"Error getting record count: {e}")
            return 0

    def create_backup(self) -> bool:
        """Create a backup of the current database"""
        try:
            return self.backup_manager.create_backup(self.db_path)
        except Exception as e:
            print(f"Error creating database backup: {e}")
            return False
            
    def get_available_backups(self) -> list:
        """Get list of available backup files"""
        try:
            return self.backup_manager.get_available_backups()
        except Exception as e:
            print(f"Error getting backup list: {e}")
            return []
            
    def restore_from_backup(self, backup_filename: str) -> bool:
        """Restore database from specified backup"""
        try:
            success = self.backup_manager.restore_backup(backup_filename)
            if success:
                # Reinitialize after restore
                self.init_db()
            return success
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            return False

    def __del__(self):
        """Cleanup database connections on object destruction"""
        try:
            # Create backup before closing if database was modified
            if hasattr(self, 'backup_manager') and os.path.exists(self.db_path):
                self.backup_manager.create_backup(self.db_path)
                
            # Close all pooled connections
            for thread_id, conn in self.connection_pool.items():
                try:
                    conn.close()
                except:
                    pass
        except:
            pass
    
    def get_unique_serial_numbers(self) -> List[str]:
        """Get list of unique serial numbers from the database
        
        Returns:
            List of unique serial numbers, excluding 'Unknown' and empty values
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT serial_number 
                    FROM water_logs 
                    WHERE serial_number IS NOT NULL 
                    AND serial_number != ''
                    AND serial_number != 'Unknown'
                    ORDER BY serial_number
                """)
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting unique serial numbers: {e}")
            traceback.print_exc()
            return []
