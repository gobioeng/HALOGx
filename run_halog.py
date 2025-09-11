#!/usr/bin/env python3
"""
Wrapper script to run HALog application in Replit environment
Handles Qt platform configuration for VNC display
"""

import os
import sys

def setup_qt_environment():
    """Configure Qt for Replit VNC environment"""
    # Use xcb platform with Replit's X server (don't override DISPLAY)
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    
    # Disable debug plugins output for cleaner logs
    # os.environ['QT_DEBUG_PLUGINS'] = '1'
    
    # Additional Qt environment variables for stability
    os.environ['QT_X11_NO_MITSHM'] = '1'
    os.environ['QT_LOGGING_RULES'] = '*.debug=false'
    os.environ['QT_ACCESSIBILITY'] = '0'
    
    print("✓ Qt environment configured for xcb platform with Replit VNC")

def main():
    """Main wrapper function"""
    setup_qt_environment()
    
    # Execute the HALog application properly
    try:
        print("🚀 Starting HALog application...")
        print("📱 This is a desktop GUI application running in Replit")
        print("🖥️  The GUI interface will appear in the VNC viewer")
        
        # Execute main.py as a script so __name__ == "__main__" triggers
        os.execvp(sys.executable, [sys.executable, "-u", "main.py"])
        
    except Exception as e:
        print(f"❌ Error starting HALog: {e}")
        import traceback
        traceback.print_exc()
        
        print("ℹ️  This application requires a GUI environment")
        print("ℹ️  In Replit, desktop apps appear in the VNC viewer panel")
        return 1

if __name__ == "__main__":
    sys.exit(main())