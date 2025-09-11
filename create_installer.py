#!/usr/bin/env python3
"""
HALbasic Windows Installer Creation Script
Creates a comprehensive Windows installer for HALbasic LINAC monitoring application
Developer: gobioeng.com
Date: 2025-01-21
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


class HALbasicInstaller:
    """Comprehensive installer creator for HALbasic application"""
    
    def __init__(self, build_type="onedir"):
        self.build_type = build_type  # "onedir" or "onefile"
        self.app_name = "HALbasic"
        self.app_version = "0.0.1"
        self.company = "gobioeng.com"
        self.description = "Professional LINAC Water System Monitor"
        
        # Paths
        self.project_root = Path(__file__).parent.resolve()
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.spec_file = self.project_root / f"{self.app_name}.spec"
        
    def clean_build_directories(self):
        """Clean previous build artifacts"""
        print("🧹 Cleaning previous build artifacts...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   Removed: {dir_path}")
        
        if self.spec_file.exists():
            os.remove(self.spec_file)
            print(f"   Removed: {self.spec_file}")
    
    def verify_dependencies(self):
        """Verify all required dependencies are installed"""
        print("🔍 Verifying dependencies...")
        
        # Do NOT include PyInstaller here; we test its CLI separately.
        required_packages = [
            'PyQt5', 'pandas', 'numpy', 'matplotlib', 
            'scipy', 'pyqtgraph'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package if package != 'PyQt5' else 'PyQt5')
                print(f"   ✓ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"   ✗ {package} - MISSING")
        
        # Check PyInstaller CLI separately
        print("   Checking PyInstaller CLI...")
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'PyInstaller', '--version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                print(f"   ✓ PyInstaller (version: {result.stdout.strip()})")
            else:
                raise RuntimeError("PyInstaller CLI not working")
        except Exception:
            missing_packages.append('PyInstaller')
            print("   ✗ PyInstaller - MISSING (pip install pyinstaller)")
        
        if missing_packages:
            print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
            print("Install with:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
        
        print("✅ All dependencies verified")
        return True
    
    def create_spec_file(self):
        """Create PyInstaller spec file for HALbasic"""
        print("📝 Creating PyInstaller spec file...")
        
        # Candidate data directories
        candidate_datas = [
            ('data', 'data'),
            ('assets', 'assets'),
        ]
        
        # Only include ones that actually exist
        datas_list = []
        for src, dest in candidate_datas:
            full_path = self.project_root / src
            if full_path.exists():
                datas_list.append((full_path.as_posix(), dest))
            else:
                print(f"   ⚠️ Skipping missing data directory: {full_path}")
        
        # CRITICAL FIX: Add matplotlib data files for PyInstaller
        # This ensures matplotlib fonts and configuration work in the executable
        try:
            import matplotlib
            import os
            mpl_data_path = matplotlib.get_data_path()
            if os.path.exists(mpl_data_path):
                datas_list.append((mpl_data_path, 'matplotlib/mpl-data'))
                print(f"   ✓ Added matplotlib data: {mpl_data_path}")
                
            # Also add matplotlib configuration directory
            import matplotlib as mpl
            config_dir = mpl.get_configdir()
            if os.path.exists(config_dir):
                datas_list.append((config_dir, 'matplotlib/config'))
                print(f"   ✓ Added matplotlib config: {config_dir}")
                
        except Exception as e:
            print(f"   ⚠️ Could not add matplotlib data: {e}")
        
        # Hidden imports - remove ones you do NOT actually use to avoid failures
        hidden_imports = [
            'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
            'matplotlib.backends.backend_qt5agg',
            'matplotlib.backends.backend_pdf',
            'matplotlib.backends._backend_qt5',
            'matplotlib.backends.backend_agg',  # Fallback backend
            'matplotlib.figure',
            'matplotlib.dates',
            'matplotlib.pyplot',
            'matplotlib._path',
            'matplotlib.ft2font',
            'matplotlib.style',
            'matplotlib.font_manager',
            'pandas', 'numpy', 'scipy',
            # Remove if unused:
            # 'sklearn', 'sqlalchemy', 'openpyxl',
            'pyqtgraph'
        ]
        
        # Build the spec content
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
# HALbasic PyInstaller Spec File
# Generated by create_installer.py

import sys
from pathlib import Path

block_cipher = None

APP_NAME = '{self.app_name}'
APP_VERSION = '{self.app_version}'
COMPANY = '{self.company}'
DESCRIPTION = '{self.description}'

a = Analysis(
    ['main.py'],
    pathex=['{self.project_root.as_posix()}'],
    binaries=[],
    datas={datas_list},
    hiddenimports={hidden_imports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'tk', 'tcl',
        'PIL', 'Pillow',
        'test', 'tests',
        'distutils',
        'setuptools',
        '_pytest',
        'pytest',
        'sphinx',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# Build type selection
"""
        if self.build_type == "onefile":
            spec_content += """
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='assets/halogo.ico'
)
"""
        else:
            spec_content += """
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='assets/halogo.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
"""
        with open(self.spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"✅ Spec file created: {self.spec_file}")
    
    def create_version_info(self):
        """Create version information file for Windows executable"""
        print("📄 Creating version information...")
        
        version_info_content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({self.app_version.replace('.', ', ')}, 0),
    prodvers=({self.app_version.replace('.', ', ')}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{self.company}'),
         StringStruct(u'FileDescription', u'{self.description}'),
         StringStruct(u'FileVersion', u'{self.app_version}'),
         StringStruct(u'InternalName', u'{self.app_name}'),
         StringStruct(u'LegalCopyright', u'Copyright © 2025 {self.company}'),
         StringStruct(u'OriginalFilename', u'{self.app_name}.exe'),
         StringStruct(u'ProductName', u'{self.app_name}'),
         StringStruct(u'ProductVersion', u'{self.app_version}')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
        version_file = self.project_root / "version_info.txt"
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(version_info_content)
        
        print(f"✅ Version info created: {version_file}")
    
    def ensure_assets_exist(self):
        """Ensure required assets exist or create fallbacks"""
        print("🎨 Checking assets...")
        assets_dir = self.project_root / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        icon_file = assets_dir / "halogo.ico"
        if not icon_file.exists():
            png_file = assets_dir / "halogo.png"
            if png_file.exists():
                print(f"   Converting {png_file} to ICO format...")
                try:
                    from PIL import Image
                    img = Image.open(png_file)
                    img.save(icon_file)
                    print(f"   ✓ Created {icon_file}")
                except ImportError:
                    print("   ⚠️ PIL not installed; skipping ICO conversion")
            else:
                print(f"   ⚠️ No icon found ({icon_file}); default icon will be used")
    
    def build_application(self):
        """Build the application using PyInstaller"""
        print(f"🔨 Building {self.app_name} ({self.build_type})...")
        
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(self.spec_file)
        ]
        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ Build completed successfully!")
                self._show_build_results()
            else:
                print("❌ Build failed!")
                print("STDOUT:\n" + result.stdout)
                print("STDERR:\n" + result.stderr)
                return False
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
        
        return True
    
    def _show_build_results(self):
        """Show build results and file locations"""
        print("\n📦 Build Results:")
        if self.build_type == "onedir":
            app_dir = self.dist_dir / self.app_name
            if app_dir.exists():
                exe_file = app_dir / f"{self.app_name}.exe"
                if exe_file.exists():
                    size_mb = exe_file.stat().st_size / (1024 * 1024)
                    print(f"   📁 Directory: {app_dir}")
                    print(f"   🚀 Executable: {exe_file}")
                    print(f"   📏 Exe Size: {size_mb:.1f} MB")
                    total_files = sum(1 for _ in app_dir.rglob('*') if _.is_file())
                    total_size = sum(f.stat().st_size for f in app_dir.rglob('*') if f.is_file())
                    print(f"   📊 Total Files: {total_files}")
                    print(f"   💾 Total Size: {total_size / (1024 * 1024):.1f} MB")
        else:
            exe_file = self.dist_dir / f"{self.app_name}.exe"
            if exe_file.exists():
                size_mb = exe_file.stat().st_size / (1024 * 1024)
                print(f"   🚀 Executable: {exe_file}")
                print(f"   📏 Size: {size_mb:.1f} MB")
    
    def create_installer_script(self):
        """Create a simple installer script (batch)"""
        print("📦 Creating installer script...")
        self.dist_dir.mkdir(exist_ok=True)
        
        installer_script = f"""@echo off
echo Installing {self.app_name} {self.app_version}
echo Company: {self.company}
echo.

set INSTALL_DIR=%PROGRAMFILES%\\{self.company}\\{self.app_name}
echo Creating installation directory: %INSTALL_DIR%
mkdir "%INSTALL_DIR%" 2>nul

echo Copying application files...
xcopy /E /I /Y ".\\{self.app_name}\\*" "%INSTALL_DIR%\\"

echo Creating desktop shortcut...
set DESKTOP=%USERPROFILE%\\Desktop
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%DESKTOP%\\{self.app_name}.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%INSTALL_DIR%\\{self.app_name}.exe" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> CreateShortcut.vbs
echo oLink.Description = "{self.description}" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs

echo Creating start menu entry...
set STARTMENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs
mkdir "%STARTMENU%\\{self.company}" 2>nul
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateStartMenu.vbs
echo sLinkFile = "%STARTMENU%\\{self.company}\\{self.app_name}.lnk" >> CreateStartMenu.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateStartMenu.vbs
echo oLink.TargetPath = "%INSTALL_DIR%\\{self.app_name}.exe" >> CreateStartMenu.vbs
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> CreateStartMenu.vbs
echo oLink.Description = "{self.description}" >> CreateStartMenu.vbs
echo oLink.Save >> CreateStartMenu.vbs
cscript //nologo CreateStartMenu.vbs
del CreateStartMenu.vbs

echo.
echo ✅ {self.app_name} installation completed!
echo 🚀 You can now run {self.app_name} from:
echo    - Desktop shortcut
echo    - Start Menu -> {self.company} -> {self.app_name}
echo    - Direct path: %INSTALL_DIR%\\{self.app_name}.exe
echo.
pause
"""
        installer_file = self.dist_dir / "install.bat"
        with open(installer_file, 'w', encoding='utf-8') as f:
            f.write(installer_script)
        print(f"✅ Installer script created: {installer_file}")
    
    def create_readme(self):
        """Create README file for distribution"""
        print("📚 Creating README...")
        self.dist_dir.mkdir(exist_ok=True)
        
        readme_content = f"""# {self.app_name} {self.app_version}

## {self.description}

Developer: {self.company}
Version: {self.app_version}
Build Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

(See repository documentation for full usage details.)
"""
        readme_file = self.dist_dir / "README.txt"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✅ README created: {readme_file}")
    
    def run_full_build(self):
        """Run the complete build process"""
        print(f"🚀 Starting {self.app_name} installer creation...")
        print(f"Build Type: {self.build_type}")
        print(f"Version: {self.app_version}")
        print(f"Company: {self.company}")
        print("=" * 60)
        
        try:
            self.clean_build_directories()
            if not self.verify_dependencies():
                return False
            self.ensure_assets_exist()
            self.create_version_info()
            self.create_spec_file()
            if not self.build_application():
                return False
            self.create_installer_script()
            self.create_readme()
            
            print("\n" + "=" * 60)
            print(f"🎉 {self.app_name} installer creation completed successfully!")
            print(f"📁 Distribution folder: {self.dist_dir}")
            print("📋 Next steps:")
            print("   1. Test the application by running the .exe file")
            print("   2. Run install.bat to test installation process")
            print("   3. Distribute the entire dist folder to users")
            print("=" * 60)
            return True
        except Exception as e:
            print(f"\n❌ Build process failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function to run installer creation"""
    parser = argparse.ArgumentParser(
        description="Create Windows installer for HALbasic LINAC monitoring application"
    )
    parser.add_argument(
        '--type',
        choices=['onedir', 'onefile'],
        default='onedir',
        help='Build type: onedir (faster startup) or onefile (single executable)'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean build directories only (no build)'
    )
    
    args = parser.parse_args()
    installer = HALbasicInstaller(build_type=args.type)
    
    if args.clean:
        installer.clean_build_directories()
        print("✅ Clean completed!")
        return True
    
    success = installer.run_full_build()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
