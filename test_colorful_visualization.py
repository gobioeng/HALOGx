#!/usr/bin/env python3
"""
Test script to showcase the enhanced colorful visualization features
"""

import sys
import os
sys.path.append('.')

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from plot_utils import PlotUtils

def create_sample_data():
    """Create sample LINAC monitoring data for visualization testing"""
    # Generate timestamps over 24 hours
    start_time = datetime.now() - timedelta(hours=24)
    timestamps = [start_time + timedelta(minutes=x*5) for x in range(288)]  # Every 5 minutes
    
    # Create sample data for different parameter types
    data = []
    
    # CPU Temperature data (enhanced with noise)
    base_temp = 42.0
    cpu_temps = [base_temp + 3*np.sin(x/10) + np.random.normal(0, 1) for x in range(len(timestamps))]
    
    for i, (ts, temp) in enumerate(zip(timestamps, cpu_temps)):
        data.append({
            'datetime': ts,
            'parameter': 'cpuTemperatureSensor0_avg',
            'value': temp,
            'unit': '°C',
            'serial_number': '2182',
            'avg': temp,
            'min': temp - 2,
            'max': temp + 2
        })
    
    # System Mode events (periodic changes)
    mode_changes = [
        (timestamps[50], 'SERVICE'),
        (timestamps[150], 'TREATMENT'),
        (timestamps[220], 'SERVICE'),
    ]
    
    for ts, mode in mode_changes:
        data.append({
            'datetime': ts,
            'parameter': 'system_mode',
            'value': mode,
            'unit': 'mode',
            'serial_number': '2182'
        })
    
    # Flow rate data 
    flow_rates = [15.5 + 2*np.sin(x/20) + np.random.normal(0, 0.5) for x in range(len(timestamps))]
    
    for i, (ts, flow) in enumerate(zip(timestamps[::3], flow_rates[::3])):  # Every 15 minutes
        data.append({
            'datetime': ts,
            'parameter': 'cooling_flow_rate',
            'value': flow,
            'unit': 'L/min',
            'serial_number': '2182',
            'avg': flow,
            'min': flow - 1,
            'max': flow + 1
        })
    
    return pd.DataFrame(data)

def test_colorful_visualization():
    """Test the enhanced colorful visualization features"""
    print("🎨 Testing Enhanced Colorful LINAC Visualizations")
    print("=" * 55)
    
    # Create sample data
    df = create_sample_data()
    print(f"📊 Generated {len(df)} sample data points")
    
    # Setup professional styling
    PlotUtils.setup_professional_style()
    
    # Create figure with multiple subplots to showcase different features
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('🌈 Enhanced Colorful HALog LINAC Monitoring Visualizations', 
                 fontsize=16, fontweight='bold', color='#2C3E50')
    
    # Get color scheme
    colors = PlotUtils.get_group_colors()
    
    # Plot 1: Temperature data with gradient fill
    ax1 = axes[0, 0]
    temp_data = df[df['parameter'] == 'cpuTemperatureSensor0_avg']
    if not temp_data.empty:
        PlotUtils.plot_with_gradient_fill(
            ax1, temp_data['datetime'], temp_data['value'], 
            colors['cpuTemperatureSensor'], 'CPU Temperature'
        )
        ax1.set_title('🌡️ CPU Temperature Trends', fontweight='bold')
        ax1.set_ylabel('Temperature (°C)')
        PlotUtils.apply_colorful_enhancements(ax1, 'cpuTemperatureSensor0')
    
    # Plot 2: Flow rate with different colors for min/avg/max
    ax2 = axes[0, 1]
    flow_data = df[df['parameter'] == 'cooling_flow_rate']
    if not flow_data.empty:
        ax2.plot(flow_data['datetime'], flow_data['avg'], 
                color=colors['Flow'], linewidth=3, marker='o', 
                markersize=4, label='Average', alpha=0.8)
        ax2.fill_between(flow_data['datetime'], flow_data['min'], flow_data['max'],
                        alpha=0.2, color=colors['Flow'], label='Min-Max Range')
        ax2.set_title('💧 Cooling Flow Rate', fontweight='bold')
        ax2.set_ylabel('Flow Rate (L/min)')
        ax2.legend()
        PlotUtils.apply_colorful_enhancements(ax2, 'Flow')
    
    # Plot 3: System Mode with colorful bars
    ax3 = axes[1, 0]
    mode_data = df[df['parameter'] == 'system_mode'].copy()
    if not mode_data.empty:
        mode_colors = {'SERVICE': colors['system_mode'], 'TREATMENT': '#FF4757'}
        for i, (_, row) in enumerate(mode_data.iterrows()):
            ax3.barh(i, 1, color=mode_colors.get(row['value'], '#CCC'), 
                    alpha=0.7, height=0.6)
            ax3.text(0.5, i, row['value'], ha='center', va='center', 
                    fontweight='bold', color='white')
        ax3.set_title('⚙️ System Mode Changes', fontweight='bold')
        ax3.set_yticks(range(len(mode_data)))
        ax3.set_yticklabels([ts.strftime('%H:%M') for ts in mode_data['datetime']])
        PlotUtils.apply_colorful_enhancements(ax3, 'system_mode')
    
    # Plot 4: Color palette showcase
    ax4 = axes[1, 1]
    param_types = list(colors.keys())[:8]  # First 8 parameters
    y_positions = range(len(param_types))
    
    for i, param_type in enumerate(param_types):
        ax4.barh(i, 100, color=colors[param_type], alpha=0.8, height=0.7)
        ax4.text(50, i, param_type.replace('_', ' ').title(), 
                ha='center', va='center', fontweight='bold', color='white')
    
    ax4.set_title('🎨 Enhanced Color Palette', fontweight='bold')
    ax4.set_xlim(0, 100)
    ax4.set_yticks([])
    ax4.set_xlabel('Parameter Types with Vibrant Colors')
    PlotUtils.apply_colorful_enhancements(ax4)
    
    # Apply tight layout and save
    plt.tight_layout()
    output_file = 'enhanced_colorful_visualization_test.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"✅ Colorful visualization test completed!")
    print(f"📁 Enhanced charts saved to: {output_file}")
    print("🎨 Features demonstrated:")
    print("   • Vibrant color palette for different parameter types")
    print("   • Gradient fills under curves")
    print("   • Shadow effects for depth")
    print("   • Enhanced grid and styling")
    print("   • Color-coded titles and legends")
    print("   • Professional typography and spacing")
    
    return True

if __name__ == "__main__":
    success = test_colorful_visualization()
    sys.exit(0 if success else 1)