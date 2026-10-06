"""
IoT-Based Gas Leakage Detection and Emergency Alert System
For Residential and Industrial Safety
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Set style for better visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['font.size'] = 10

class GasSensor:
    """Simulates MQ-series gas sensor for detecting LPG, Methane, and CO"""
    
    def __init__(self, sensor_id, location, sensor_type='MQ-5', calibration_factor=1.0):
        self.sensor_id = sensor_id
        self.location = location
        self.sensor_type = sensor_type  # MQ-5 (LPG), MQ-7 (CO), MQ-4 (Methane)
        self.calibration_factor = calibration_factor
        self.current_reading = 0.0  # ppm (parts per million)
        self.measurement_history = []
        self.last_alert_time = None
        self.total_alerts = 0
        self.sensor_status = 'normal'  # normal, warning, alert, critical
        
    def read_gas_level(self, actual_gas_level, environmental_noise=0):
        """
        Read gas concentration with realistic sensor characteristics
        actual_gas_level: actual gas concentration in ppm
        environmental_noise: noise level (0-1) affecting reading accuracy
        Returns: measured_gas_level (float)
        """
        # Simulate sensor noise and drift
        noise = np.random.normal(0, 2)  # 2 ppm standard deviation
        drift = np.random.normal(0, 0.5)  # Sensor drift
        
        # Calculate measured reading
        measured_reading = actual_gas_level * self.calibration_factor + noise + drift
        measured_reading = max(0, measured_reading)  # Ensure non-negative
        
        self.current_reading = measured_reading
        
        self.measurement_history.append({
            'timestamp': datetime.now(),
            'actual_level': actual_gas_level,
            'measured_level': measured_reading,
            'sensor_id': self.sensor_id,
            'location': self.location,
            'sensor_type': self.sensor_type
        })
        
        return measured_reading


class AlertManager:
    """Manages gas leak alerts and emergency notifications"""
    
    def __init__(self, lpg_threshold=1000, co_threshold=35, methane_threshold=5000):
        self.lpg_threshold = lpg_threshold  # ppm
        self.co_threshold = co_threshold    # ppm
        self.methane_threshold = methane_threshold  # ppm
        self.alerts = []
        self.alert_history = []
        self.emergency_triggered = False
        
    def evaluate_gas_level(self, sensor_id, location, gas_type, measured_level, current_time):
        """
        Evaluate gas level and generate alerts
        gas_type: 'LPG', 'CO', 'Methane'
        measured_level: measured concentration in ppm
        Returns: alert_info (dict) or None
        """
        alert_info = None
        severity = 'normal'
        threshold = self.lpg_threshold if gas_type == 'LPG' else (
            self.co_threshold if gas_type == 'CO' else self.methane_threshold
        )
        
        # Determine severity level
        if measured_level >= threshold * 1.5:
            severity = 'critical'
            self.emergency_triggered = True
        elif measured_level >= threshold:
            severity = 'high'
        elif measured_level >= threshold * 0.7:
            severity = 'medium'
        elif measured_level >= threshold * 0.5:
            severity = 'low'
        
        if severity != 'normal':
            alert_info = {
                'timestamp': current_time,
                'sensor_id': sensor_id,
                'location': location,
                'gas_type': gas_type,
                'measured_level': measured_level,
                'threshold': threshold,
                'severity': severity,
                'message': f"{severity.upper()} ALERT: {gas_type} level at {location} is {measured_level:.1f} ppm (threshold: {threshold} ppm)"
            }
            
            self.alerts.append(alert_info)
            self.alert_history.append(alert_info)
        
        return alert_info


class MonitoringZone:
    """Represents a monitoring zone (room/area) with multiple gas sensors"""
    
    def __init__(self, zone_id, zone_name, zone_type='residential'):
        self.zone_id = zone_id
        self.zone_name = zone_name
        self.zone_type = zone_type  # residential, industrial, laboratory
        self.sensors = {}
        self.alert_manager = AlertManager()
        self.zone_status = 'safe'  # safe, warning, alert, critical
        self.last_alert_time = None
        self.total_alerts = 0
        
    def add_sensor(self, sensor_id, location, sensor_type='MQ-5'):
        """Add a gas sensor to the zone"""
        self.sensors[sensor_id] = GasSensor(sensor_id, location, sensor_type)
        
    def evaluate_zone_safety(self, current_time):
        """Evaluate overall zone safety status"""
        active_alerts = len([a for a in self.alert_manager.alerts if 
                           (current_time - a['timestamp']).total_seconds() < 300])
        
        if active_alerts > 0:
            critical_alerts = len([a for a in self.alert_manager.alerts if 
                                 a['severity'] == 'critical' and 
                                 (current_time - a['timestamp']).total_seconds() < 300])
            
            if critical_alerts > 0:
                self.zone_status = 'critical'
            elif any(a['severity'] == 'high' for a in self.alert_manager.alerts[-3:]):
                self.zone_status = 'alert'
            else:
                self.zone_status = 'warning'
        else:
            self.zone_status = 'safe'


class GasDetectionSystem:
    """Main system managing gas detection and emergency alerts"""
    
    def __init__(self, system_name='Gas Detection System'):
        self.system_name = system_name
        self.zones = {}
        self.system_status = 'active'  # active, maintenance, offline
        self.daily_statistics = []
        self.all_alerts = []
        self.emergency_events = []
        
    def add_zone(self, zone_id, zone_name, zone_type='residential'):
        """Add a monitoring zone to the system"""
        self.zones[zone_id] = MonitoringZone(zone_id, zone_name, zone_type)
        
    def simulate_day(self, date=None, num_intervals=96):
        """
        Simulate a full day with 15-minute intervals (96 intervals in 24 hours)
        """
        if date is None:
            date = datetime.now().date()
        
        daily_data = []
        total_alerts = 0
        critical_events = 0
        
        for interval in range(num_intervals):
            quarter_hour = (interval * 15) / 60
            hour = int(quarter_hour)
            minutes = int((quarter_hour % 1) * 60)
            
            current_time = datetime.combine(date, datetime.min.time()) + timedelta(hours=quarter_hour)
            
            for zone_id, zone in self.zones.items():
                # Simulate gas patterns based on zone type and time
                lpg_level = self._generate_lpg_pattern(zone.zone_type, hour)
                co_level = self._generate_co_pattern(zone.zone_type, hour)
                methane_level = self._generate_methane_pattern(zone.zone_type, hour)
                
                # Process each sensor in the zone
                for sensor_id, sensor in zone.sensors.items():
                    if 'MQ-5' in sensor.sensor_type:
                        measured_lpg = sensor.read_gas_level(lpg_level)
                        alert = zone.alert_manager.evaluate_gas_level(
                            sensor_id, zone.zone_name, 'LPG', measured_lpg, current_time
                        )
                        if alert:
                            total_alerts += 1
                            if alert['severity'] == 'critical':
                                critical_events += 1
                            self.all_alerts.append(alert)
                            
                    elif 'MQ-7' in sensor.sensor_type:
                        measured_co = sensor.read_gas_level(co_level)
                        alert = zone.alert_manager.evaluate_gas_level(
                            sensor_id, zone.zone_name, 'CO', measured_co, current_time
                        )
                        if alert:
                            total_alerts += 1
                            if alert['severity'] == 'critical':
                                critical_events += 1
                            self.all_alerts.append(alert)
                            
                    elif 'MQ-4' in sensor.sensor_type:
                        measured_methane = sensor.read_gas_level(methane_level)
                        alert = zone.alert_manager.evaluate_gas_level(
                            sensor_id, zone.zone_name, 'Methane', measured_methane, current_time
                        )
                        if alert:
                            total_alerts += 1
                            if alert['severity'] == 'critical':
                                critical_events += 1
                            self.all_alerts.append(alert)
                
                # Evaluate zone safety
                zone.evaluate_zone_safety(current_time)
                
                daily_data.append({
                    'date': date,
                    'time': f"{hour:02d}:{minutes:02d}",
                    'hour': hour,
                    'zone_id': zone_id,
                    'zone_name': zone.zone_name,
                    'zone_type': zone.zone_type,
                    'zone_status': zone.zone_status,
                    'lpg_level': lpg_level,
                    'co_level': co_level,
                    'methane_level': methane_level,
                    'active_alerts': len(zone.alert_manager.alerts)
                })
        
        self.daily_statistics.append({
            'date': date,
            'total_alerts': total_alerts,
            'critical_events': critical_events,
            'num_zones': len(self.zones),
            'system_status': self.system_status
        })
        
        return pd.DataFrame(daily_data)
    
    def _generate_lpg_pattern(self, zone_type, hour):
        """Generate realistic LPG concentration patterns"""
        if zone_type == 'industrial':
            # Industrial: high baseline with peaks during work hours
            if 6 <= hour < 18:
                base = 200 + np.random.normal(0, 50)
                if np.random.random() < 0.05:  # 5% chance of spike
                    return max(0, base + np.random.uniform(500, 1200))
                return max(0, base)
            else:
                return max(0, np.random.normal(50, 20))
        elif zone_type == 'residential':
            # Residential: low baseline, peaks during cooking
            if 7 <= hour < 9 or 18 <= hour < 20:
                return max(0, np.random.normal(300, 100))
            else:
                return max(0, np.random.normal(50, 15))
        else:  # laboratory
            return max(0, np.random.normal(100, 30))
    
    def _generate_co_pattern(self, zone_type, hour):
        """Generate realistic CO concentration patterns"""
        if zone_type == 'industrial':
            if 6 <= hour < 18:
                return max(0, np.random.normal(15, 5))
            else:
                return max(0, np.random.normal(5, 2))
        elif zone_type == 'residential':
            # Higher during heating season (winter)
            if 6 <= hour < 9 or 18 <= hour < 22:
                return max(0, np.random.normal(8, 3))
            else:
                return max(0, np.random.normal(3, 1))
        else:
            return max(0, np.random.normal(5, 2))
    
    def _generate_methane_pattern(self, zone_type, hour):
        """Generate realistic Methane concentration patterns"""
        if zone_type == 'industrial':
            if 6 <= hour < 18:
                return max(0, np.random.normal(500, 150))
            else:
                return max(0, np.random.normal(100, 30))
        elif zone_type == 'residential':
            return max(0, np.random.normal(200, 50))
        else:
            return max(0, np.random.normal(300, 80))
    
    def get_system_report(self):
        """Generate comprehensive system report"""
        report = {
            'system_name': self.system_name,
            'total_zones': len(self.zones),
            'total_alerts': len(self.all_alerts),
            'critical_events': len([a for a in self.all_alerts if a['severity'] == 'critical']),
            'simulation_days': len(self.daily_statistics),
            'system_status': self.system_status,
            'avg_daily_alerts': np.mean([stat['total_alerts'] for stat in self.daily_statistics]) if self.daily_statistics else 0
        }
        return report


def generate_visualizations(system, daily_data):
    """Generate comprehensive visualizations for the report"""
    
    # 1. Gas Concentration Analysis
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('IoT-Based Gas Leakage Detection System - Gas Concentration Analysis', 
                 fontsize=16, fontweight='bold')
    
    # LPG concentration by hour
    lpg_by_hour = daily_data.groupby('hour')['lpg_level'].mean()
    axes[0, 0].plot(lpg_by_hour.index, lpg_by_hour.values, marker='o', linewidth=2, 
                    markersize=6, color='#FF6B6B', label='LPG Level')
    axes[0, 0].axhline(y=1000, color='red', linestyle='--', linewidth=2, label='LPG Threshold')
    axes[0, 0].fill_between(lpg_by_hour.index, lpg_by_hour.values, alpha=0.3, color='#FF6B6B')
    axes[0, 0].set_title('LPG Concentration by Hour', fontweight='bold')
    axes[0, 0].set_ylabel('Concentration (ppm)')
    axes[0, 0].set_xlabel('Hour of Day')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # CO concentration by hour
    co_by_hour = daily_data.groupby('hour')['co_level'].mean()
    axes[0, 1].plot(co_by_hour.index, co_by_hour.values, marker='s', linewidth=2, 
                    markersize=6, color='#4ECDC4', label='CO Level')
    axes[0, 1].axhline(y=35, color='orange', linestyle='--', linewidth=2, label='CO Threshold')
    axes[0, 1].fill_between(co_by_hour.index, co_by_hour.values, alpha=0.3, color='#4ECDC4')
    axes[0, 1].set_title('CO Concentration by Hour', fontweight='bold')
    axes[0, 1].set_ylabel('Concentration (ppm)')
    axes[0, 1].set_xlabel('Hour of Day')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Methane concentration by hour
    methane_by_hour = daily_data.groupby('hour')['methane_level'].mean()
    axes[1, 0].plot(methane_by_hour.index, methane_by_hour.values, marker='^', linewidth=2, 
                    markersize=6, color='#95E1D3', label='Methane Level')
    axes[1, 0].axhline(y=5000, color='darkgreen', linestyle='--', linewidth=2, label='Methane Threshold')
    axes[1, 0].fill_between(methane_by_hour.index, methane_by_hour.values, alpha=0.3, color='#95E1D3')
    axes[1, 0].set_title('Methane Concentration by Hour', fontweight='bold')
    axes[1, 0].set_ylabel('Concentration (ppm)')
    axes[1, 0].set_xlabel('Hour of Day')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Zone status distribution
    zone_status_counts = daily_data['zone_status'].value_counts()
    colors_status = {'safe': 'green', 'warning': 'yellow', 'alert': 'orange', 'critical': 'red'}
    colors = [colors_status.get(status, 'gray') for status in zone_status_counts.index]
    
    axes[1, 1].bar(zone_status_counts.index, zone_status_counts.values, color=colors, edgecolor='black')
    axes[1, 1].set_title('Zone Safety Status Distribution', fontweight='bold')
    axes[1, 1].set_ylabel('Frequency')
    axes[1, 1].set_xlabel('Zone Status')
    for i, v in enumerate(zone_status_counts.values):
        axes[1, 1].text(i, v + 10, str(v), ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/gas_detection_project/fig_gas_concentration.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_gas_concentration.png")
    plt.close()
    
    # 2. Alert Analysis
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Alert Analysis and Emergency Response', fontsize=16, fontweight='bold')
    
    # Alert types distribution
    alert_types = [a['gas_type'] for a in system.all_alerts]
    alert_counts = pd.Series(alert_types).value_counts()
    colors_map = {'LPG': '#FF6B6B', 'CO': '#4ECDC4', 'Methane': '#95E1D3'}
    colors = [colors_map.get(alert, 'gray') for alert in alert_counts.index]
    
    axes[0, 0].bar(alert_counts.index, alert_counts.values, color=colors, edgecolor='black')
    axes[0, 0].set_title('Alert Types Distribution', fontweight='bold')
    axes[0, 0].set_ylabel('Count')
    axes[0, 0].set_xlabel('Gas Type')
    for i, v in enumerate(alert_counts.values):
        axes[0, 0].text(i, v + 2, str(v), ha='center', fontweight='bold')
    
    # Alerts by hour
    alerts_by_hour = daily_data.groupby('hour')['active_alerts'].mean()
    axes[0, 1].bar(alerts_by_hour.index, alerts_by_hour.values, color='#FF6B6B', edgecolor='black', alpha=0.7)
    axes[0, 1].set_title('Average Active Alerts by Hour', fontweight='bold')
    axes[0, 1].set_ylabel('Number of Alerts')
    axes[0, 1].set_xlabel('Hour of Day')
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    
    # Alert severity distribution
    alert_severities = [a['severity'] for a in system.all_alerts]
    severity_counts = pd.Series(alert_severities).value_counts()
    colors_severity = {'low': 'yellow', 'medium': 'orange', 'high': 'red', 'critical': 'darkred'}
    colors = [colors_severity.get(sev, 'gray') for sev in severity_counts.index]
    
    axes[1, 0].pie(severity_counts.values, labels=severity_counts.index, autopct='%1.1f%%',
                   colors=colors, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
    axes[1, 0].set_title('Alert Severity Distribution', fontweight='bold')
    
    # Zone-wise alert count
    zone_alerts = daily_data.groupby('zone_name')['active_alerts'].sum()
    axes[1, 1].barh(zone_alerts.index, zone_alerts.values, color='#FF6B6B', edgecolor='black')
    axes[1, 1].set_title('Total Alerts by Zone', fontweight='bold')
    axes[1, 1].set_xlabel('Number of Alerts')
    for i, v in enumerate(zone_alerts.values):
        axes[1, 1].text(v + 2, i, str(int(v)), va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/gas_detection_project/fig_alert_analysis.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_alert_analysis.png")
    plt.close()
    
    # 3. System Architecture Diagram
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')
    
    ax.text(0.5, 0.95, 'IoT-Based Gas Leakage Detection System Architecture', 
            ha='center', fontsize=16, fontweight='bold', transform=ax.transAxes)
    
    components = [
        ('MQ-5 Sensor\n(LPG)', 0.15, 0.75),
        ('MQ-7 Sensor\n(CO)', 0.5, 0.75),
        ('MQ-4 Sensor\n(Methane)', 0.85, 0.75),
        ('IoT\nCommunication\nModule', 0.5, 0.55),
        ('Cloud\nServer', 0.15, 0.35),
        ('Alert\nManagement', 0.5, 0.35),
        ('Emergency\nNotifications', 0.85, 0.35),
    ]
    
    for label, x, y in components:
        bbox = dict(boxstyle='round,pad=0.6', facecolor='lightblue', edgecolor='black', linewidth=2)
        ax.text(x, y, label, ha='center', va='center', fontsize=11, fontweight='bold',
                transform=ax.transAxes, bbox=bbox)
    
    connections = [
        ((0.25, 0.75), (0.4, 0.75)),
        ((0.6, 0.75), (0.75, 0.75)),
        ((0.5, 0.65), (0.5, 0.60)),
        ((0.25, 0.65), (0.25, 0.60)),
        ((0.75, 0.65), (0.75, 0.60)),
    ]
    
    for start, end in connections:
        ax.annotate('', xy=end, xytext=start, transform=ax.transAxes,
                   arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    features_text = 'Key Features:\n• Real-time Gas Monitoring\n• Multi-gas Detection (LPG, CO, Methane)\n• Instant Emergency Alerts\n• Cloud-based Dashboard\n• 24/7 Safety Coverage'
    ax.text(0.5, 0.15, features_text, ha='center', va='top', fontsize=10,
            transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor='lightyellow', 
            edgecolor='black', linewidth=1.5))
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/gas_detection_project/fig_system_architecture.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_system_architecture.png")
    plt.close()
    
    # 4. Daily Performance
    fig, ax = plt.subplots(figsize=(12, 6))
    
    daily_stats = pd.DataFrame(system.daily_statistics)
    
    x = np.arange(len(daily_stats))
    width = 0.35
    
    ax.bar(x - width/2, daily_stats['total_alerts'], width, label='Total Alerts', 
           color='orange', edgecolor='black')
    ax2 = ax.twinx()
    ax2.bar(x + width/2, daily_stats['critical_events'], width, label='Critical Events', 
            color='red', alpha=0.7, edgecolor='black')
    
    ax.set_xlabel('Day', fontweight='bold')
    ax.set_ylabel('Total Alerts', fontweight='bold', color='orange')
    ax2.set_ylabel('Critical Events', fontweight='bold', color='red')
    ax.set_title('Daily System Performance', fontweight='bold', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Day {i+1}" for i in range(len(daily_stats))])
    ax.grid(True, alpha=0.3, axis='y')
    
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/gas_detection_project/fig_daily_performance.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_daily_performance.png")
    plt.close()
    
    # 5. Sensor Heatmap
    fig, ax = plt.subplots(figsize=(12, 6))
    
    sensor_activity = daily_data.pivot_table(values='active_alerts', index='zone_name', 
                                             columns='hour', aggfunc='mean', fill_value=0)
    
    sns.heatmap(sensor_activity, cmap='YlOrRd', annot=True, fmt='.1f', cbar_kws={'label': 'Avg Alerts'},
                ax=ax, linewidths=0.5, linecolor='gray')
    ax.set_title('Sensor Activity Heatmap - Alerts by Zone and Hour', fontweight='bold', fontsize=14)
    ax.set_xlabel('Hour of Day', fontweight='bold')
    ax.set_ylabel('Zone Name', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/gas_detection_project/fig_sensor_heatmap.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_sensor_heatmap.png")
    plt.close()


def main():
    """Main execution function"""
    print("=" * 70)
    print("IOT-BASED GAS LEAKAGE DETECTION AND EMERGENCY ALERT SYSTEM SIMULATION")
    print("=" * 70)
    
    # Initialize system
    system = GasDetectionSystem("IoT Gas Detection and Alert System")
    
    # Add monitoring zones
    zones_config = {
        'ZONE-001': {'name': 'Residential Kitchen', 'type': 'residential'},
        'ZONE-002': {'name': 'Industrial Warehouse', 'type': 'industrial'},
        'ZONE-003': {'name': 'Laboratory', 'type': 'laboratory'},
        'ZONE-004': {'name': 'Residential Bedroom', 'type': 'residential'},
        'ZONE-005': {'name': 'Industrial Plant', 'type': 'industrial'},
    }
    
    for zone_id, config in zones_config.items():
        system.add_zone(zone_id, config['name'], config['type'])
        zone = system.zones[zone_id]
        
        # Add sensors to each zone
        zone.add_sensor(f"{zone_id}-MQ5-01", config['name'], 'MQ-5')  # LPG
        zone.add_sensor(f"{zone_id}-MQ7-01", config['name'], 'MQ-7')  # CO
        zone.add_sensor(f"{zone_id}-MQ4-01", config['name'], 'MQ-4')  # Methane
    
    print(f"\nSystem initialized with {len(zones_config)} monitoring zones:")
    for zone_id, config in zones_config.items():
        print(f"  - {zone_id}: {config['name']} ({config['type']})")
    
    # Simulate 7 days
    print("\nSimulating 7 days of gas monitoring...")
    all_data = []
    
    for day in range(7):
        simulation_date = datetime.now().date() - timedelta(days=6-day)
        daily_data = system.simulate_day(simulation_date)
        all_data.append(daily_data)
        
        daily_stats = system.daily_statistics[-1]
        print(f"Day {day+1}: Alerts={daily_stats['total_alerts']}, "
              f"Critical={daily_stats['critical_events']}, "
              f"Status={daily_stats['system_status']}")
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    generate_visualizations(system, combined_data)
    
    # Generate report data
    report = system.get_system_report()
    
    print("\n" + "=" * 70)
    print("SYSTEM REPORT")
    print("=" * 70)
    print(f"System Name: {report['system_name']}")
    print(f"Total Monitoring Zones: {report['total_zones']}")
    print(f"Total Alerts Generated: {report['total_alerts']}")
    print(f"Critical Events Detected: {report['critical_events']}")
    print(f"Average Daily Alerts: {report['avg_daily_alerts']:.1f}")
    print(f"System Status: {report['system_status']}")
    print(f"Simulation Period: {report['simulation_days']} days")
    print("=" * 70)
    
    # Save data to CSV
    combined_data.to_csv('/home/ubuntu/gas_detection_project/simulation_data.csv', index=False)
    print("\nSimulation data saved to: simulation_data.csv")
    
    # Save report to JSON
    report_json = {
        'system_report': report,
        'zones': list(zones_config.keys()),
        'simulation_date': datetime.now().isoformat(),
        'daily_statistics': system.daily_statistics,
        'total_alerts': len(system.all_alerts)
    }
    
    with open('/home/ubuntu/gas_detection_project/system_report.json', 'w') as f:
        json.dump(report_json, f, indent=2, default=str)
    
    print("System report saved to: system_report.json")
    
    return system, combined_data


if __name__ == "__main__":
    system, data = main()
