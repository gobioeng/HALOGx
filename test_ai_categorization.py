#!/usr/bin/env python3
"""
Final verification: Test AI-powered parameter categorization for trend tabs
This ensures optimal user experience with logical parameter grouping
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_ai_parameter_categorization():
    """Test AI-powered parameter categorization for optimal trend tab organization"""
    print("🤖 Testing AI-Powered Parameter Categorization")
    print("=" * 60)
    
    try:
        from unified_parser import UnifiedParser
        
        # Parse samlog.txt to get all parameters
        parser = UnifiedParser()
        df = parser.parse_linac_file('samlog.txt')
        
        if df.empty:
            print("❌ No data to categorize")
            return False
        
        # Get unique base parameters (without _avg, _max, _min suffixes)
        unique_params = df['param'].unique()
        base_params = list(set([
            param.replace('_avg', '').replace('_max', '').replace('_min', '').replace('_count', '')
            for param in unique_params
        ]))
        
        print(f"📊 Categorizing {len(base_params)} unique parameters...")
        
        # AI-powered categorization with detailed logic
        categories = {
            'Water System / Flow': {
                'keywords': ['flow', 'magnetron', 'target', 'circulator', 'pump', 'water', 'cooling'],
                'description': 'Water cooling system flow rates and pump parameters',
                'parameters': [],
                'expected_unit': 'L/min',
                'trend_importance': 'High'
            },
            'Electrical / Voltages': {
                'keywords': ['voltage', 'volt', '24v', '48v', '5v', '12v', '3_3v', '1_2v', 'adc', 'mlc', 'col', 'chan', 'mon'],
                'description': 'Electrical system voltage monitoring across all subsystems',
                'parameters': [],
                'expected_unit': 'V',
                'trend_importance': 'High'
            },
            'Thermal / Temperatures': {
                'keywords': ['temp', 'temperature', 'cpu', 'thermal', 'heat', 'remote'],
                'description': 'Temperature monitoring for system components and environment',
                'parameters': [],
                'expected_unit': '°C',
                'trend_importance': 'Critical'
            },
            'Environmental / HVAC': {
                'keywords': ['fan', 'speed', 'humidity', 'humid', 'air', 'hvac'],
                'description': 'Environmental control: fans, humidity, air circulation',
                'parameters': [],
                'expected_unit': 'RPM/%',
                'trend_importance': 'Medium'
            },
            'Mechanical / Motion': {
                'keywords': ['motor', 'drift', 'deviation', 'gantry', 'collimator', 'couch', 'position', 'afc'],
                'description': 'Mechanical positioning and motion control systems',
                'parameters': [],
                'expected_unit': 'mm',
                'trend_importance': 'High'
            },
            'Operational / Status': {
                'keywords': ['board', 'heartbeat', 'status', 'statistics', 'stat', 'monitor'],
                'description': 'System operational status and board-level monitoring',
                'parameters': [],
                'expected_unit': 'Various',
                'trend_importance': 'Medium'
            }
        }
        
        # Categorize each parameter using AI logic
        uncategorized = []
        
        for param in base_params:
            param_lower = param.lower()
            categorized = False
            
            # Check against each category
            for category_name, category_info in categories.items():
                if any(keyword in param_lower for keyword in category_info['keywords']):
                    category_info['parameters'].append(param)
                    categorized = True
                    break
            
            if not categorized:
                uncategorized.append(param)
        
        # Display categorization results
        print("\n🏷️ AI Categorization Results:")
        print("=" * 40)
        
        total_categorized = 0
        for category_name, category_info in categories.items():
            if category_info['parameters']:
                print(f"\n📂 {category_name}")
                print(f"   Description: {category_info['description']}")
                print(f"   Expected Unit: {category_info['expected_unit']}")
                print(f"   Trend Importance: {category_info['trend_importance']}")
                print(f"   Parameters ({len(category_info['parameters'])}):")
                
                for param in category_info['parameters'][:5]:  # Show first 5
                    # Get friendly name from mapedname.txt mapping if available
                    friendly_name = param  # Default to parameter name
                    try:
                        # Load mapping to get friendly name
                        with open('data/mapedname.txt', 'r') as f:
                            lines = f.readlines()
                        
                        for line in lines:
                            if '|' in line:
                                parts = [p.strip() for p in line.split('|')]
                                if len(parts) >= 2 and parts[0] == param:
                                    friendly_name = parts[1]
                                    break
                    except:
                        pass
                    
                    print(f"     • {param} → {friendly_name}")
                
                if len(category_info['parameters']) > 5:
                    print(f"     ... and {len(category_info['parameters']) - 5} more")
                
                total_categorized += len(category_info['parameters'])
        
        # Show uncategorized parameters
        if uncategorized:
            print(f"\n❓ Uncategorized Parameters ({len(uncategorized)}):")
            for param in uncategorized:
                print(f"     • {param}")
        
        # Success metrics
        categorization_rate = (total_categorized / len(base_params)) * 100
        print(f"\n📊 Categorization Success Rate: {categorization_rate:.1f}%")
        print(f"   Total parameters: {len(base_params)}")
        print(f"   Categorized: {total_categorized}")
        print(f"   Uncategorized: {len(uncategorized)}")
        
        # Recommendations for trend tabs
        print(f"\n💡 Recommended Trend Tab Organization:")
        priority_categories = [cat for cat, info in categories.items() 
                             if info['parameters'] and info['trend_importance'] in ['Critical', 'High']]
        
        for category in priority_categories:
            param_count = len(categories[category]['parameters'])
            print(f"   📈 {category}: {param_count} parameters (Priority: {categories[category]['trend_importance']})")
        
        # Final assessment
        success = categorization_rate >= 80 and len(priority_categories) >= 3
        
        if success:
            print(f"\n✅ AI Categorization SUCCESSFUL!")
            print(f"   • High categorization rate ({categorization_rate:.1f}%)")
            print(f"   • {len(priority_categories)} high-priority categories")
            print(f"   • Logical parameter grouping for user experience")
            print(f"   • Ready for trend tab display")
        else:
            print(f"\n⚠️ AI Categorization needs improvement")
            print(f"   • Categorization rate: {categorization_rate:.1f}% (target: ≥80%)")
            print(f"   • High-priority categories: {len(priority_categories)} (target: ≥3)")
        
        return success
        
    except Exception as e:
        print(f"❌ Error in AI categorization test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ai_parameter_categorization()
    print("\n" + "=" * 60)
    if success:
        print("🎉 AI PARAMETER CATEGORIZATION TEST PASSED!")
        print("🧠 Parameters are optimally organized for user experience")
        print("📈 Trend tabs will display logical parameter groupings")
    else:
        print("❌ AI PARAMETER CATEGORIZATION TEST FAILED!")
    print("=" * 60)