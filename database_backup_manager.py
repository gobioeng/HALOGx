"""
Database Backup Manager - HALog Enhancement
Handles database backup, versioning, and recovery functionality
Company: gobioeng.com
"""

import os
import shutil
import sqlite3
import time
from pathlib import Path
from typing import List, Optional, Dict
import json
from datetime import datetime


class DatabaseBackupManager:
    """Manages database backup, versioning, and crash recovery"""
    
    def __init__(self, app_data_dir: str = "data"):
        self.app_data_dir = Path(app_data_dir)
        self.db_dir = self.app_data_dir / "database"
        self.backup_dir = self.db_dir / "backups"
        self.main_db_path = self.db_dir / "halog_water.db"
        self.metadata_path = self.db_dir / "backup_metadata.json"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Maximum number of backup versions to keep
        self.max_backups = 3
        
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        self.app_data_dir.mkdir(exist_ok=True)
        self.db_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
    def get_main_db_path(self) -> str:
        """Get the path to the main database file"""
        return str(self.main_db_path)
        
    def create_backup(self, source_db_path: Optional[str] = None) -> bool:
        """Create a backup of the database with metadata"""
        try:
            # Use main db path if no source specified
            if source_db_path is None:
                source_db_path = str(self.main_db_path)
                
            if not os.path.exists(source_db_path):
                print(f"Source database not found: {source_db_path}")
                return False
                
            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"halog_water_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            # Copy database file
            shutil.copy2(source_db_path, backup_path)
            
            # Update backup metadata
            self._update_backup_metadata(backup_filename, source_db_path)
            
            # Clean up old backups (keep only max_backups)
            self._cleanup_old_backups()
            
            print(f"✓ Database backup created: {backup_filename}")
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
            
    def _update_backup_metadata(self, backup_filename: str, source_path: str):
        """Update backup metadata file"""
        try:
            metadata = self._load_backup_metadata()
            
            # Add new backup info
            backup_info = {
                "filename": backup_filename,
                "created_at": datetime.now().isoformat(),
                "source_path": source_path,
                "file_size": os.path.getsize(self.backup_dir / backup_filename)
            }
            
            metadata["backups"].append(backup_info)
            
            # Sort by creation time (newest first)
            metadata["backups"].sort(key=lambda x: x["created_at"], reverse=True)
            
            # Save updated metadata
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not update backup metadata: {e}")
            
    def _load_backup_metadata(self) -> Dict:
        """Load backup metadata or create default structure"""
        try:
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load backup metadata: {e}")
            
        # Return default structure
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "backups": []
        }
        
    def _cleanup_old_backups(self):
        """Remove old backup files beyond max_backups limit"""
        try:
            metadata = self._load_backup_metadata()
            backups = metadata["backups"]
            
            if len(backups) > self.max_backups:
                # Remove old backup files
                for backup in backups[self.max_backups:]:
                    backup_path = self.backup_dir / backup["filename"]
                    if backup_path.exists():
                        backup_path.unlink()
                        print(f"Removed old backup: {backup['filename']}")
                        
                # Update metadata to remove deleted backups
                metadata["backups"] = backups[:self.max_backups]
                with open(self.metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                    
        except Exception as e:
            print(f"Warning: Error cleaning up old backups: {e}")
            
    def get_available_backups(self) -> List[Dict]:
        """Get list of available backup files with metadata"""
        try:
            metadata = self._load_backup_metadata()
            available_backups = []
            
            for backup in metadata["backups"]:
                backup_path = self.backup_dir / backup["filename"]
                if backup_path.exists():
                    # Add display information
                    backup_copy = backup.copy()
                    backup_copy["display_name"] = f"Backup {backup['created_at'][:16].replace('T', ' ')}"
                    backup_copy["file_path"] = str(backup_path)
                    backup_copy["size_mb"] = round(backup["file_size"] / (1024 * 1024), 2)
                    available_backups.append(backup_copy)
                    
            return available_backups
            
        except Exception as e:
            print(f"Error getting available backups: {e}")
            return []
            
    def restore_backup(self, backup_filename: str) -> bool:
        """Restore database from backup file"""
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                print(f"Backup file not found: {backup_filename}")
                return False
                
            # Verify backup database integrity
            if not self._verify_database_integrity(backup_path):
                print(f"Backup file is corrupted: {backup_filename}")
                return False
                
            # Create backup of current database before restore
            if self.main_db_path.exists():
                current_backup_name = f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(self.main_db_path, self.backup_dir / current_backup_name)
                print(f"✓ Current database backed up as: {current_backup_name}")
                
            # Restore from backup
            shutil.copy2(backup_path, self.main_db_path)
            print(f"✓ Database restored from backup: {backup_filename}")
            return True
            
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
            
    def _verify_database_integrity(self, db_path: Path) -> bool:
        """Verify SQLite database integrity"""
        try:
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                return result[0] == "ok"
        except Exception as e:
            print(f"Database integrity check failed: {e}")
            return False
            
    def setup_crash_recovery(self) -> bool:
        """Setup crash recovery mechanism"""
        try:
            # Create initial backup if main database exists
            if self.main_db_path.exists():
                return self.create_backup()
            return True
        except Exception as e:
            print(f"Error setting up crash recovery: {e}")
            return False
            
    def handle_database_corruption(self) -> Optional[str]:
        """Handle database corruption by offering restore options"""
        try:
            available_backups = self.get_available_backups()
            
            if not available_backups:
                print("No backup files available for recovery")
                return None
                
            # Return the most recent backup for automatic recovery
            return available_backups[0]["filename"]
            
        except Exception as e:
            print(f"Error handling database corruption: {e}")
            return None