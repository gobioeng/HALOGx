#!/usr/bin/env python3
"""
HALog Replit VNC Wrapper Script
Professional LINAC Monitoring System - gobioeng.com
Replit-specific wrapper for VNC/offscreen display configuration
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Configure Qt platform for Replit VNC environment
def configure_qt_platform():
    """Configure Qt platform for VNC compatibility"""
    # Display configuration for VNC
    if 'DISPLAY' not in os.environ:
        os.environ['DISPLAY'] = ':0'
    
    # Display configuration for VNC
    display = os.environ.get('DISPLAY', ':0')
    
    # For Replit VNC environment, use offscreen platform
    # The VNC server will capture the rendered content
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    print(f"✓ Qt platform configured for VNC: offscreen (Display: {display})")
    print("ℹ️ Using offscreen rendering - VNC server will capture GUI output")
    
    # Additional Qt configuration for VNC compatibility
    os.environ['QT_X11_NO_MITSHM'] = '1'
    os.environ['QT_QPA_FONTDIR'] = '/usr/share/fonts'
    
    # Configure matplotlib to use a default font to reduce warnings
    os.environ['MPLBACKEND'] = 'Qt5Agg'

def ensure_assets():
    """Ensure required assets exist"""
    app_dir = Path(__file__).parent.absolute()
    assets_dir = app_dir / "assets"
    
    if not assets_dir.exists():
        assets_dir.mkdir(exist_ok=True)
        print(f"✓ Created assets directory: {assets_dir}")
    
    # Check for icon files
    icon_files = ["halogo.ico", "halogo.png"]
    for icon_file in icon_files:
        icon_path = assets_dir / icon_file
        if icon_path.exists():
            print(f"✓ Found icon: {icon_file}")
        else:
            print(f"ℹ️ Icon not found: {icon_file} (will use default)")

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main entry point for HALog in Replit VNC environment"""
    print("🚀 Starting HALog - Professional LINAC Monitoring System")
    print("🌐 Company: gobioeng.com")
    print("📊 Version: 0.0.1 (Beta)")
    print("🖥️  Platform: Replit VNC Environment")
    print("-" * 60)
    
    try:
        # Configure environment
        configure_qt_platform()
        ensure_assets()
        setup_signal_handlers()
        
        # Change to application directory
        app_dir = Path(__file__).parent.absolute()
        os.chdir(app_dir)
        
        print(f"📁 Working directory: {app_dir}")
        print("⏳ Launching HALog application...")
        
        # Import and run the main application
        sys.path.insert(0, str(app_dir))
        
        # Import main application
        from main import HALogApp
        from PyQt5.QtWidgets import QApplication
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(True)
        
        # Create and run HALog
        halog_app = HALogApp()
        
        # Create splash screen
        splash = halog_app.create_splash()
        
        # Create main window
        main_window = halog_app.create_main_window()
        
        # Show main window and hide splash
        if splash:
            splash.hide()
        if main_window:
            main_window.show()
            
            # Verify window is visible (sanity check for VNC)
            if hasattr(main_window, 'isVisible') and main_window.isVisible():
                print("✅ Main window is visible and ready")
            else:
                print("⚠️ Main window might not be visible - check Qt platform configuration")
        
        print("✅ HALog application started successfully!")
        print("🎯 Application ready for VNC desktop access")
        print("📈 Professional LINAC monitoring system operational")
        
        # Run the application event loop
        sys.exit(app.exec_())
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Please ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()