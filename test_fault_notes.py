"""
Test script for Fault Notes Manager functionality
"""

import os
import sys
import tempfile
import json

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fault_notes_manager import FaultNotesManager


def test_fault_notes_manager():
    """Test the basic functionality of FaultNotesManager"""
    print("🔍 Testing FaultNotesManager functionality...")
    
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Initialize manager with test file
        manager = FaultNotesManager(temp_path)
        
        # Test saving a note
        print("✓ Testing save_note...")
        success = manager.save_note("400027", "This is a test note for fault code 400027", "TestUser")
        assert success, "Failed to save note"
        print("  ✓ Note saved successfully")
        
        # Test retrieving the note
        print("✓ Testing get_note...")
        note_data = manager.get_note("400027")
        assert note_data is not None, "Failed to retrieve note"
        assert note_data['note'] == "This is a test note for fault code 400027", "Note content mismatch"
        assert note_data['author'] == "TestUser", "Author mismatch"
        print("  ✓ Note retrieved successfully")
        
        # Test updating the note
        print("✓ Testing note update...")
        success = manager.save_note("400027", "Updated test note", "TestUser")
        assert success, "Failed to update note"
        updated_note = manager.get_note("400027")
        assert updated_note['note'] == "Updated test note", "Note update failed"
        print("  ✓ Note updated successfully")
        
        # Test saving another note
        print("✓ Testing multiple notes...")
        success = manager.save_note("251330", "Another test note for a different fault code")
        assert success, "Failed to save second note"
        
        # Test getting all notes
        all_notes = manager.get_all_notes()
        assert len(all_notes) == 2, f"Expected 2 notes, got {len(all_notes)}"
        print("  ✓ Multiple notes handled correctly")
        
        # Test notes count
        count = manager.get_notes_count()
        assert count == 2, f"Expected count 2, got {count}"
        print("  ✓ Notes count correct")
        
        # Test deleting a note
        print("✓ Testing delete_note...")
        success = manager.delete_note("251330")
        assert success, "Failed to delete note"
        deleted_note = manager.get_note("251330")
        assert deleted_note is None, "Note was not deleted"
        print("  ✓ Note deleted successfully")
        
        # Test getting note for non-existent fault code
        print("✓ Testing non-existent fault code...")
        non_existent = manager.get_note("999999")
        assert non_existent is None, "Expected None for non-existent fault code"
        print("  ✓ Non-existent fault code handled correctly")
        
        # Verify file was created and contains expected data
        print("✓ Testing file persistence...")
        assert os.path.exists(temp_path), "Notes file was not created"
        with open(temp_path, 'r') as f:
            file_data = json.load(f)
        assert "400027" in file_data, "Note not persisted to file"
        print("  ✓ File persistence verified")
        
        print("🎉 All tests passed! FaultNotesManager is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up test file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == "__main__":
    success = test_fault_notes_manager()
    sys.exit(0 if success else 1)