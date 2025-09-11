"""
Fault Notes Manager
Handles persistent storage and retrieval of user notes for fault codes
Company: gobioeng.com
"""

import json
import os
from typing import Dict, Optional
from datetime import datetime


class FaultNotesManager:
    """Manages persistent storage of fault code notes"""
    
    def __init__(self, notes_file_path: str = None):
        """Initialize notes manager with optional custom file path"""
        if notes_file_path is None:
            # Store notes file in the same directory as the application
            app_dir = os.path.dirname(os.path.abspath(__file__))
            notes_file_path = os.path.join(app_dir, "fault_notes.json")
        
        self.notes_file_path = notes_file_path
        self.notes: Dict[str, Dict] = {}
        self._load_notes()
    
    def _load_notes(self):
        """Load notes from JSON file"""
        try:
            if os.path.exists(self.notes_file_path):
                with open(self.notes_file_path, 'r', encoding='utf-8') as f:
                    self.notes = json.load(f)
                print(f"✓ Loaded {len(self.notes)} fault code notes from {self.notes_file_path}")
            else:
                self.notes = {}
                print(f"No existing fault notes file found. Will create {self.notes_file_path}")
        except Exception as e:
            print(f"Error loading fault notes: {e}")
            self.notes = {}
    
    def _save_notes(self):
        """Save notes to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.notes_file_path), exist_ok=True)
            
            with open(self.notes_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved fault notes to {self.notes_file_path}")
            return True
        except Exception as e:
            print(f"Error saving fault notes: {e}")
            return False
    
    def save_note(self, fault_code: str, note_text: str, author: str = "User") -> bool:
        """
        Save a note for a specific fault code
        
        Args:
            fault_code: The fault code (e.g., "400027")
            note_text: The note content
            author: Who wrote the note (optional)
        
        Returns:
            bool: True if saved successfully
        """
        try:
            fault_code = str(fault_code).strip()
            if not fault_code:
                return False
            
            # Create note entry with metadata
            note_entry = {
                "note": note_text.strip(),
                "author": author,
                "created_date": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            }
            
            # If note already exists, update it and preserve creation date
            if fault_code in self.notes:
                note_entry["created_date"] = self.notes[fault_code].get("created_date", note_entry["created_date"])
            
            self.notes[fault_code] = note_entry
            return self._save_notes()
            
        except Exception as e:
            print(f"Error saving note for fault code {fault_code}: {e}")
            return False
    
    def get_note(self, fault_code: str) -> Optional[Dict]:
        """
        Get the note for a specific fault code
        
        Args:
            fault_code: The fault code to look up
            
        Returns:
            Dict with note information or None if no note exists
        """
        try:
            fault_code = str(fault_code).strip()
            return self.notes.get(fault_code)
        except Exception as e:
            print(f"Error getting note for fault code {fault_code}: {e}")
            return None
    
    def delete_note(self, fault_code: str) -> bool:
        """
        Delete a note for a specific fault code
        
        Args:
            fault_code: The fault code to delete note for
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            fault_code = str(fault_code).strip()
            if fault_code in self.notes:
                del self.notes[fault_code]
                return self._save_notes()
            return True  # Note didn't exist, consider it successful
        except Exception as e:
            print(f"Error deleting note for fault code {fault_code}: {e}")
            return False
    
    def get_all_notes(self) -> Dict[str, Dict]:
        """Get all fault code notes"""
        return self.notes.copy()
    
    def get_notes_count(self) -> int:
        """Get total number of fault codes with notes"""
        return len(self.notes)
    
    def export_notes(self, export_path: str) -> bool:
        """
        Export all notes to a file
        
        Args:
            export_path: Path to export file
            
        Returns:
            bool: True if exported successfully
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, indent=2, ensure_ascii=False)
            print(f"✓ Exported {len(self.notes)} fault notes to {export_path}")
            return True
        except Exception as e:
            print(f"Error exporting fault notes: {e}")
            return False
    
    def import_notes(self, import_path: str, merge: bool = True) -> bool:
        """
        Import notes from a file
        
        Args:
            import_path: Path to import file
            merge: If True, merge with existing notes. If False, replace all notes.
            
        Returns:
            bool: True if imported successfully
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_notes = json.load(f)
            
            if merge:
                self.notes.update(imported_notes)
            else:
                self.notes = imported_notes
            
            result = self._save_notes()
            print(f"✓ Imported {len(imported_notes)} fault notes from {import_path}")
            return result
        except Exception as e:
            print(f"Error importing fault notes: {e}")
            return False