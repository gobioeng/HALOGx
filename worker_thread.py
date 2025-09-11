from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from unified_parser import UnifiedParser
from database import DatabaseManager
import os
import json
import traceback
import sys
from datetime import datetime


class ThreadCrashSafetyMixin:
    """Mixin class to provide crash safety for QThread implementations"""
    
    def __init__(self):
        super().__init__()
        self._crash_recovery_enabled = True
        self._thread_id = f"thread_{id(self)}"
        self._start_time = None
        self._watchdog_timer = None
        self._max_runtime_seconds = 3600  # 1 hour max runtime
        
    def _setup_crash_safety(self):
        """Setup crash safety mechanisms"""
        try:
            self._start_time = datetime.now()
            
            # Setup watchdog timer if not already done
            if self._watchdog_timer is None:
                self._watchdog_timer = QTimer()
                self._watchdog_timer.timeout.connect(self._check_thread_health)
                self._watchdog_timer.start(30000)  # Check every 30 seconds
                
            print(f"✓ Crash safety enabled for {self._thread_id}")
        except Exception as e:
            print(f"Warning: Could not setup crash safety: {e}")
            
    def _check_thread_health(self):
        """Check thread health and handle potential issues"""
        try:
            if self._start_time:
                runtime = (datetime.now() - self._start_time).total_seconds()
                if runtime > self._max_runtime_seconds:
                    print(f"⚠️ Thread {self._thread_id} exceeded maximum runtime ({runtime}s)")
                    self._handle_thread_timeout()
                    
        except Exception as e:
            print(f"Warning: Thread health check failed: {e}")
            
    def _handle_thread_timeout(self):
        """Handle thread timeout"""
        try:
            print(f"🛑 Forcefully terminating thread {self._thread_id}")
            if hasattr(self, 'error'):
                self.error.emit(f"Thread timeout - operation cancelled after {self._max_runtime_seconds}s")
            self._cleanup_resources()
            self.terminate()
        except Exception as e:
            print(f"Error handling thread timeout: {e}")
            
    def _cleanup_resources(self):
        """Cleanup resources before thread termination"""
        try:
            if self._watchdog_timer:
                self._watchdog_timer.stop()
                self._watchdog_timer = None
                
            # Subclasses can override this method for specific cleanup
            print(f"✓ Resources cleaned up for {self._thread_id}")
        except Exception as e:
            print(f"Warning: Error during resource cleanup: {e}")
            
    def _safe_emit(self, signal, *args):
        """Safely emit signals with error handling"""
        try:
            signal.emit(*args)
        except Exception as e:
            print(f"Error emitting signal: {e}")
            
    def run_with_crash_safety(self, main_function):
        """Run main function with crash safety wrapper"""
        try:
            self._setup_crash_safety()
            result = main_function()
            return result
        except Exception as e:
            error_msg = f"Thread {self._thread_id} crashed: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            
            if hasattr(self, 'error'):
                self._safe_emit(self.error, error_msg)
                
            return None
        finally:
            # Always clean up resources regardless of success/failure
            self._cleanup_resources()
            # Don't emit finished signal here - let the main function handle it


class FileProcessingWorker(QThread, ThreadCrashSafetyMixin):
    """Background worker thread for processing large LINAC log files with crash safety"""

    # Signals for communication with main thread
    progress_update = pyqtSignal(
        float, str, int, int, int, int
    )  # percentage, message, lines_processed, total_lines, bytes_processed, total_bytes
    status_update = pyqtSignal(str)  # status message
    finished = pyqtSignal(int, dict)  # records_count, parsing_stats
    error = pyqtSignal(str)  # error message

    def __init__(self, file_path: str, file_size: int, database: DatabaseManager):
        QThread.__init__(self)
        ThreadCrashSafetyMixin.__init__(self)
        
        self.file_path = file_path
        self.file_size = file_size
        self.database = database
        self.parser = UnifiedParser()
        self._cancel_requested = False
        
        # Optimize chunk size based on file size
        if file_size > 100 * 1024 * 1024:  # > 100MB
            self.chunk_size = 5000  # Larger chunks for big files
        elif file_size > 10 * 1024 * 1024:  # > 10MB  
            self.chunk_size = 2000  # Medium chunks
        else:
            self.chunk_size = 1000  # Default chunk size

    def run(self):
        """Main worker thread execution with crash safety"""
        return self.run_with_crash_safety(self._main_processing)
        
    def _main_processing(self):
        """Main processing logic wrapped by crash safety"""
        self._safe_emit(self.status_update, "Preparing to read file...")
        self._safe_emit(self.progress_update, 0, "Preparing to read file...", 0, 0, 0, self.file_size)
        
        # Give progress dialog time to show
        import time
        time.sleep(0.1)
        
        self._safe_emit(self.status_update, "Opening file for reading...")
        self._safe_emit(self.progress_update, 5, f"Opening file ({self.file_size:,} bytes)...", 0, 0, 0, self.file_size)
        
        # Give more feedback
        time.sleep(0.1)
        
        self._safe_emit(self.status_update, "Initializing parser...")
        self._safe_emit(self.progress_update, 10, "Starting file processing...", 0, 0, 0, self.file_size)

        # Parse file with chunked processing
        df = self.parser.parse_linac_file(
            file_path=self.file_path,
            chunk_size=self.chunk_size,
            progress_callback=self._progress_callback,
            cancel_callback=self._cancel_callback,
        )

        if self._cancel_requested:
            self._safe_emit(self.status_update, "Processing cancelled by user")
            return

        if df.empty:
            self._safe_emit(self.finished, 0, self.parser.get_parsing_stats())
            return

        # Update progress for database insertion
        self._safe_emit(self.status_update, "Saving data to database...")
        self._safe_emit(self.progress_update, 90, "Inserting records into database...",
                       self.parser.parsing_stats["lines_processed"],
                       self.parser.parsing_stats["lines_processed"],
                       self.file_size, self.file_size)

        # Insert data into database in optimized batches
        batch_size = min(1000, max(100, len(df) // 10))  # Dynamic batch size
        records_inserted = self.database.insert_data_batch(df, batch_size=batch_size)

        # Insert file metadata
        filename = os.path.basename(self.file_path)
        parsing_stats_json = json.dumps(self.parser.get_parsing_stats())
        self.database.insert_file_metadata(
            filename=filename,
            file_size=self.file_size,
            records_imported=records_inserted,
            parsing_stats=parsing_stats_json,
        )

        # Create backup after successful processing
        if hasattr(self.database, 'create_backup'):
            self.database.create_backup()

        # Final progress update
        self._safe_emit(self.progress_update, 100, "Processing completed successfully!",
                       self.parser.parsing_stats["lines_processed"],
                       self.parser.parsing_stats["lines_processed"],
                       self.file_size, self.file_size)

        # Emit completion signal
        self._safe_emit(self.finished, records_inserted, self.parser.get_parsing_stats())
        
    def _cleanup_resources(self):
        """Override cleanup to handle file processing specific resources"""
        try:
            super()._cleanup_resources()
            
            # Cancel any ongoing operations
            self._cancel_requested = True
            
            # Close any file handles
            if hasattr(self, 'parser') and self.parser:
                self.parser = None
                
            print(f"✓ File processing resources cleaned up for {self._thread_id}")
        except Exception as e:
            print(f"Warning: Error cleaning up file processing resources: {e}")

    def _progress_callback(self, percentage: float, message: str):
        """Handle progress updates from parser"""
        if self._cancel_requested:
            return

        # Calculate estimated lines and bytes processed
        lines_processed = self.parser.parsing_stats.get("lines_processed", 0)
        estimated_total_lines = max(lines_processed, int(self.file_size / 100))
        bytes_processed = int((percentage / 100.0) * self.file_size)

        # Ensure percentage is properly bounded integer
        progress_value = max(0.0, min(100.0, float(percentage)))

        self.progress_update.emit(
            progress_value,
            message,
            lines_processed,
            estimated_total_lines,
            bytes_processed,
            self.file_size,
        )

        self.status_update.emit(message)

    def _cancel_callback(self) -> bool:
        """Check if cancellation was requested"""
        return self._cancel_requested

    def cancel_processing(self):
        """Request cancellation of processing"""
        self._cancel_requested = True
        self.status_update.emit("Cancelling processing...")

        # Terminate thread if it's still running
        if self.isRunning():
            self.terminate()
            self.wait(5000)  # Wait up to 5 seconds for clean termination


class AnalysisWorker(QThread, ThreadCrashSafetyMixin):
    """Background worker for data analysis operations with crash safety"""

    analysis_progress = pyqtSignal(int, str)  # percentage, message
    analysis_finished = pyqtSignal(dict)  # results dictionary
    analysis_error = pyqtSignal(str)  # error message

    def __init__(self, data_analyzer, dataframe):
        QThread.__init__(self)
        ThreadCrashSafetyMixin.__init__(self)
        
        self.analyzer = data_analyzer
        self.df = dataframe
        self._cancel_requested = False

    def run(self):
        """Run comprehensive data analysis in background with crash safety"""
        return self.run_with_crash_safety(self._main_analysis)
        
    def _main_analysis(self):
        """Main analysis logic wrapped by crash safety"""
        results = {}

        # Step 1: Calculate comprehensive statistics
        self._safe_emit(self.analysis_progress, 25, "Calculating comprehensive statistics...")
        if not self._cancel_requested:
            results["statistics"] = self.analyzer.calculate_comprehensive_statistics(self.df)

        # Step 2: Detect anomalies
        self._safe_emit(self.analysis_progress, 50, "Detecting anomalies...")
        if not self._cancel_requested:
            results["anomalies"] = self.analyzer.detect_advanced_anomalies(self.df)

        # Step 3: Calculate trends
        self._safe_emit(self.analysis_progress, 75, "Analyzing trends...")
        if not self._cancel_requested:
            results["trends"] = self.analyzer.calculate_advanced_trends(self.df)

        # Step 4: Complete
        self._safe_emit(self.analysis_progress, 100, "Analysis completed!")
        if not self._cancel_requested:
            self._safe_emit(self.analysis_finished, results)

    def cancel_analysis(self):
        """Cancel the analysis operation"""
        self._cancel_requested = True


class DatabaseWorker(QThread, ThreadCrashSafetyMixin):
    """Background worker for database operations with crash safety"""

    db_progress = pyqtSignal(int, str)  # percentage, message
    db_finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, database: DatabaseManager, operation: str, **kwargs):
        QThread.__init__(self)
        ThreadCrashSafetyMixin.__init__(self)
        
        self.database = database
        self.operation = operation
        self.kwargs = kwargs

    def run(self):
        """Execute database operation in background with crash safety"""
        return self.run_with_crash_safety(self._main_database_operation)
        
    def _main_database_operation(self):
        """Main database operation logic wrapped by crash safety"""
        if self.operation == "clear_all":
            self._safe_emit(self.db_progress, 50, "Clearing database...")
            self.database.clear_all()
            self._safe_emit(self.db_progress, 100, "Database cleared successfully")
            self._safe_emit(self.db_finished, True, "Database cleared successfully")

        elif self.operation == "vacuum":
            self._safe_emit(self.db_progress, 50, "Optimizing database...")
            self.database.vacuum_database()
            self._safe_emit(self.db_progress, 100, "Database optimized")
            self._safe_emit(self.db_finished, True, "Database optimized successfully")
            
        elif self.operation == "backup":
            self._safe_emit(self.db_progress, 50, "Creating database backup...")
            success = self.database.create_backup()
            self._safe_emit(self.db_progress, 100, "Backup completed")
            self._safe_emit(self.db_finished, success, "Backup created successfully" if success else "Backup failed")

        else:
            self._safe_emit(self.db_finished, False, f"Unknown operation: {self.operation}")