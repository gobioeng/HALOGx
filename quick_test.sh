#!/bin/bash
# HALbasic Quick Test Script
# Run this to validate all fixes are working

echo "🧪 HALbasic Quick Validation"
echo "=========================="

echo ""
echo "1. Testing Python environment..."
python3 -c "
import sys
print(f'Python version: {sys.version}')
try:
    from PyQt5.QtWidgets import QApplication
    print('✅ PyQt5 available')
except ImportError:
    print('❌ PyQt5 not available - run: pip install -r requirements.txt')
    exit(1)
"

echo ""
echo "2. Testing application files..."
if [ -f "main.py" ]; then
    echo "✅ main.py found"
else
    echo "❌ main.py not found"
    exit 1
fi

if [ -f "create_installer.py" ]; then
    echo "✅ create_installer.py found"
else
    echo "❌ create_installer.py not found"
    exit 1
fi

echo ""
echo "3. Testing fixes..."
python3 -c "
print('Checking graph popup fix...')
with open('utils_plot.py', 'r') as f:
    if 'canvas.setParent(widget)' in f.read():
        print('✅ Graph popup fix applied')
    else:
        print('❌ Graph popup fix missing')

print('Checking splash screen fix...')        
with open('splash_screen.py', 'r') as f:
    if 'minimum_display_time = 1.0' in f.read():
        print('✅ Splash screen timing optimized')
    else:
        print('❌ Splash screen fix missing')

print('Checking font fix...')
with open('styles.py', 'r') as f:
    if 'Calibri' in f.read():
        print('✅ Calibri font implemented')
    else:
        print('❌ Calibri font missing')
"

echo ""
echo "4. Testing installer script..."
if python3 create_installer.py --clean > /dev/null 2>&1; then
    echo "✅ Installer script functional"
else
    echo "❌ Installer script has issues"
fi

echo ""
echo "=========================="
echo "🎉 Quick validation complete!"
echo ""
echo "📋 Next Steps:"
echo "  • Run full tests: python test_app.py"  
echo "  • Launch app: python main.py"
echo "  • Create installer: python create_installer.py"
echo ""
echo "🔧 If issues found:"
echo "  • Install dependencies: pip install -r requirements.txt"
echo "  • Check Python version (3.8+ required)"
echo "  • Ensure all files are present"