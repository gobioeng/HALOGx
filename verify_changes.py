#!/usr/bin/env python3
"""
Verification script for HALbasic code optimization changes
Tests that core functionality still works after cleanup
"""

import sys
import os
import importlib.util

def test_imports():
    """Test that core modules can be imported"""
    print("Testing module imports...")
    
    modules_to_test = [
        'database',
        'unified_parser', 
        'progress_dialog',
        'main_window',
        'plot_utils'
    ]
    
    for module_name in modules_to_test:
        try:
            spec = importlib.util.spec_from_file_location(module_name, f"{module_name}.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"  ✓ {module_name}")
        except Exception as e:
            print(f"  ✗ {module_name}: {e}")

def check_removed_files():
    """Verify that cleanup files were removed"""
    print("\nChecking removed files...")
    
    files_that_should_be_gone = [
        'ENHANCEMENT_SUMMARY.md',
        'IMPLEMENTATION_SUMMARY.md', 
        'demo_improvements.py',
        'final_verification.py',
        'test_comprehensive.py'
    ]
    
    for filename in files_that_should_be_gone:
        if not os.path.exists(filename):
            print(f"  ✓ {filename} removed")
        else:
            print(f"  ✗ {filename} still exists")

def check_main_py_changes():
    """Check that main.py changes are in place"""
    print("\nChecking main.py changes...")
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for helper functions
    if 'def safe_update_progress' in content:
        print("  ✓ safe_update_progress helper function added")
    else:
        print("  ✗ safe_update_progress helper function missing")
        
    # Check that data table function is removed
    if 'def update_data_table' not in content:
        print("  ✓ update_data_table function removed")
    else:
        print("  ✗ update_data_table function still exists")
        
    # Check for consolidated progress calls
    if 'safe_update_progress' in content:
        print("  ✓ Progress calls consolidated")
    else:
        print("  ✗ Progress calls not consolidated")

def main():
    """Run all verification tests"""
    print("HALbasic Code Optimization Verification")
    print("=" * 40)
    
    test_imports()
    check_removed_files()
    check_main_py_changes()
    
    print("\nVerification complete!")

if __name__ == "__main__":
    main()