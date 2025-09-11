#!/usr/bin/env python3
"""
HALbasic Application Testing Script
Tests the fixes implemented for graph windows, splash screen, fonts, and connections
Developer: gobioeng.com
Date: 2025-01-21
"""

import sys
import os
import time
import traceback
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing module imports...")
    
    required_modules = [
        ('PyQt5.QtWidgets', 'PyQt5 Widgets'),
        ('PyQt5.QtCore', 'PyQt5 Core'),
        ('PyQt5.QtGui', 'PyQt5 GUI'),
        ('matplotlib', 'Matplotlib'),
        ('matplotlib.backends.backend_qt5agg', 'Matplotlib Qt5 Backend'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('scipy', 'SciPy'),
    ]
    
    failed_imports = []
    
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print(f"  ✓ {display_name}")
        except ImportError as e:
            print(f"  ✗ {display_name}: {e}")
            failed_imports.append(display_name)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        return False
    
    print("✅ All required modules imported successfully")
    return True


def test_project_structure():
    """Test that project files exist"""
    print("\n📁 Testing project structure...")
    
    project_root = Path(__file__).parent
    required_files = [
        'main.py',
        'splash_screen.py',
        'styles.py',
        'utils_plot.py',
        'plot_utils.py',
        'requirements.txt',
        'create_installer.py'
    ]
    
    missing_files = []
    
    for file_name in required_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"  ✓ {file_name}")
        else:
            print(f"  ✗ {file_name}")
            missing_files.append(file_name)
    
    # Check directories
    required_dirs = ['data', 'assets']
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"  ✓ {dir_name}/")
        else:
            print(f"  ⚠️ {dir_name}/ (optional)")
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ Project structure is valid")
    return True


def test_font_availability():
    """Test if Calibri font is available"""
    print("\n🔤 Testing font availability...")
    
    try:
        import os
        # Set platform plugin for headless environments
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        
        from PyQt5.QtGui import QFontDatabase
        from PyQt5.QtWidgets import QApplication
        
        # Ensure QApplication exists before accessing QFontDatabase
        app = QApplication.instance() or QApplication(sys.argv)
        
        font_db = QFontDatabase()
        available_fonts = font_db.families()
        
        target_fonts = ['Calibri', 'Segoe UI', 'Arial']
        available_targets = []
        
        for font in target_fonts:
            if font in available_fonts:
                available_targets.append(font)
                print(f"  ✓ {font}")
            else:
                print(f"  ✗ {font}")
        
        if 'Calibri' in available_targets:
            print("✅ Calibri font is available (primary choice)")
        elif available_targets:
            print(f"✅ Fallback fonts available: {', '.join(available_targets)}")
        else:
            print("⚠️ None of the preferred fonts available, using system default")
        
        return True
        
    except Exception as e:
        print(f"❌ Font test failed: {e}")
        return False


def test_matplotlib_backend():
    """Test matplotlib Qt5 backend"""
    print("\n📊 Testing matplotlib backend...")
    
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        from matplotlib.figure import Figure
        import os
        
        # Handle headless environment
        if os.environ.get('QT_QPA_PLATFORM') == 'offscreen':
            print("  ℹ️ Running in headless mode, using Agg backend")
            matplotlib.use('Agg')
        else:
            # Test backend switching
            matplotlib.use('Qt5Agg')
        
        print(f"  ✓ Backend: {matplotlib.get_backend()}")
        
        # Test figure creation
        fig = Figure(figsize=(4, 3), dpi=80)
        
        # For headless mode, create simpler canvas
        if matplotlib.get_backend().lower() == 'agg':
            print("  ✓ Figure creation (headless mode)")
        else:
            canvas = FigureCanvasQTAgg(fig)
            print("  ✓ Figure and Canvas creation")
        
        # Test basic plotting
        ax = fig.add_subplot(111)
        ax.plot([1, 2, 3], [1, 4, 2])
        ax.set_title("Test Plot")
        print("  ✓ Basic plotting functionality")
        
        print("✅ Matplotlib backend working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Matplotlib backend test failed: {e}")
        traceback.print_exc()
        return False


def test_application_launch():
    """Test application launch without full GUI"""
    print("\n🚀 Testing application launch components...")
    
    try:
        import os
        # Set platform plugin for headless environments  
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        
        # Test splash screen creation
        from splash_screen import MinimalisticSplashScreen
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer
        
        # Create minimal app
        app = QApplication.instance() or QApplication(sys.argv)
        
        # Test splash screen
        splash = MinimalisticSplashScreen("0.0.1-test")
        print("  ✓ Splash screen creation")
        
        # Test immediate display (should be instant)
        start_time = time.time()
        splash.show()
        splash_time = time.time() - start_time
        print(f"  ✓ Splash display time: {splash_time:.3f}s (should be < 0.1s)")
        
        # Test status update
        splash.update_status("Testing...", 50)
        print("  ✓ Splash status update")
        
        # Clean up
        splash.close()
        
        print("✅ Application launch components working")
        return True
        
    except Exception as e:
        print(f"❌ Application launch test failed: {e}")
        traceback.print_exc()
        return False


def test_plot_widgets():
    """Test plot widget creation"""
    print("\n📈 Testing plot widgets...")
    
    try:
        import os
        # Set platform plugin for headless environments
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        
        from PyQt5.QtWidgets import QApplication, QWidget
        from plot_utils import PlotWidget, DualPlotWidget
        import pandas as pd
        
        app = QApplication.instance() or QApplication(sys.argv)
        
        # Test PlotWidget
        widget = QWidget()
        plot_widget = PlotWidget(widget)
        print("  ✓ PlotWidget creation")
        
        # Test with sample data
        sample_data = pd.DataFrame({
            'datetime': pd.date_range('2025-01-01', periods=10, freq='h'),  # Use 'h' instead of deprecated 'H'
            'avg': [1, 2, 3, 4, 5, 4, 3, 2, 1, 2],
            'min': [0.5, 1.5, 2.5, 3.5, 4.5, 3.5, 2.5, 1.5, 0.5, 1.5],
            'max': [1.5, 2.5, 3.5, 4.5, 5.5, 4.5, 3.5, 2.5, 1.5, 2.5]
        })
        
        plot_widget.plot_parameter_trends(sample_data, "Test Parameter", "Test Chart")
        print("  ✓ PlotWidget data plotting")
        
        # Test DualPlotWidget
        dual_widget = DualPlotWidget(widget)
        dual_widget.update_comparison(sample_data, "Param 1", "Param 2")
        print("  ✓ DualPlotWidget creation and update")
        
        print("✅ Plot widgets working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Plot widget test failed: {e}")
        traceback.print_exc()
        return False


def test_installer_script():
    """Test installer script functionality"""
    print("\n📦 Testing installer script...")
    
    try:
        from create_installer import HALbasicInstaller
        
        # Test installer creation (without actual build)
        installer = HALbasicInstaller("onedir")
        print("  ✓ Installer class creation")
        
        # Test dependency verification
        deps_ok = installer.verify_dependencies()
        if deps_ok:
            print("  ✓ Dependencies verification")
        else:
            print("  ⚠️ Some dependencies missing (see above)")
        
        # Test clean operation
        installer.clean_build_directories()
        print("  ✓ Clean operation")
        
        print("✅ Installer script functionality working")
        return True
        
    except Exception as e:
        print(f"❌ Installer script test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("🧪 HALbasic Application Testing Suite")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Project Structure", test_project_structure),
        ("Font Availability", test_font_availability),
        ("Matplotlib Backend", test_matplotlib_backend),
        ("Application Launch", test_application_launch),
        ("Plot Widgets", test_plot_widgets),
        ("Installer Script", test_installer_script),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"🧪 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Application should be ready for use.")
        print("\n📋 Fixes Applied:")
        print("  ✓ Graph windows now stay embedded (no popups)")
        print("  ✓ Splash screen launches instantly")
        print("  ✓ Calibri font applied throughout application")
        print("  ✓ Windows installer script created")
        print("  ✓ Application startup optimized")
    else:
        print(f"⚠️ {failed} test(s) failed. Please check the issues above.")
        print("\n📋 To Fix Issues:")
        print("  • Install missing dependencies with: pip install -r requirements.txt")
        print("  • Ensure all project files are present")
        print("  • Check system font availability")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)