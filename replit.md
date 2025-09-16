# HALog - Professional LINAC Monitoring System

## Overview
HALog is a professional desktop application for monitoring LINAC (Linear Accelerator) systems, developed by gobioeng.com. This is a PyQt5-based GUI application that provides data analysis, fault code management, and comprehensive system monitoring capabilities for medical linear accelerator systems.

**Current Status**: Fully operational in Replit VNC environment with all systems working
**Version**: 0.0.1 (Beta)
**Last Updated**: 2025-09-16

## Project Architecture

### Core Components
- **main.py**: Main application entry point with PyQt5 GUI framework
- **run_halog.py**: Replit-specific wrapper script for VNC/offscreen display configuration
- **main_window.py**: Primary UI window definition 
- **database.py**: Database management with SQLite backend
- **unified_parser.py**: Fault code and data parsing system
- **fault_notes_manager.py**: Fault annotation and management
- **machine_manager.py**: Multi-machine support system

### Key Features
- Real-time LINAC system monitoring (water, voltage, temperature, humidity, fans)
- Fault code database (HAL and TB fault systems)
- Data trend analysis and visualization
- Multi-machine management support
- Professional Material Design UI
- SQLite database with backup support

### Data Structure
- **data/**: Core application data directory
  - `HALfault.txt`: HAL system fault code database
  - `TBFault.txt`: TB system fault code database
  - `database/`: SQLite database files with backup metadata
  - `cache/`: Performance and data caching system

## Technology Stack
- **Framework**: PyQt5 (GUI), SQLite (Database)
- **Analytics**: pandas, numpy, scipy, scikit-learn
- **Visualization**: matplotlib, pyqtgraph
- **Platform**: Python 3.11 with VNC support for Replit

## Recent Changes
- **2025-09-16**: Completed setup and verification in Replit environment
  - Fixed Qt platform configuration for VNC compatibility using offscreen mode
  - Installed all Python dependencies including PyQt5, matplotlib, pandas, scipy
  - Configured workflow for VNC desktop application execution
  - Verified application runs successfully with database (2980 records loaded)
  - All trend systems operational (flow, voltage, temperature, humidity, fan_speed)
  - Fault code caching system working with performance optimization
  - Startup time optimized to ~6 seconds

## Replit Configuration

### Running the Application
The application runs as a desktop GUI using Replit's VNC display:
- **Command**: `python run_halog.py`
- **Display Mode**: VNC (Virtual Network Computing)
- **Platform**: PyQt5 offscreen with VNC fallback

### User Interface Access
- The GUI appears in Replit's VNC viewer panel
- Workflow is configured to automatically start the application
- Desktop interface provides full LINAC monitoring functionality

### Development Notes
- Application uses offscreen rendering for Replit compatibility
- VNC platform provides desktop GUI access through web browser
- All dependencies are pre-installed and ready for immediate use
- Database and cache systems are fully functional

## User Preferences
- Professional Material Design styling preferred
- Desktop application interface (not web-based)
- Scientific/medical equipment monitoring focus
- Multi-machine system support required

## Deployment
- **Environment**: Replit VNC Desktop Application
- **Type**: Desktop GUI (not web deployment)
- **Dependencies**: All Python packages installed via requirements.txt
- **Database**: SQLite with automatic backup management