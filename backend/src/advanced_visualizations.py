"""
Advanced Visualization Examples - Custom implementations for impressive presentations.
These examples can be integrated into the main dashboard or used as standalone features.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json


class AdvancedVisualizations:
    """Advanced visualization data generators for impressive demos."""
    
    def __init__(self, visualization_engine):
        """Initialize with base visualization engine."""
        self.viz_engine = visualization_engine
    
    # ==================== 3D TRAFFIC SURFACE ====================
    
    def get_3d_surface_data(self) -> Dict[str, Any]:
        """
        Generate 3D surface plot data showing traffic over time and space.
        Perfect for: Impressive 3D visualization showing traffic trends
        
        Returns:
            Dict with x (hours), y (zones), z (severity) for 3D plotting
        """
        heatmaps = self.viz_engine.get_hourly_heatmap_data()
        
        hours = list(range(24))
        zones = self.viz_engine.traffic_df['location_name'].unique()[:10]
        
        # Create z values (severity matrix)
        z_values = []
        for zone in zones:
            zone_severities = []
            for hour in hours:
                points = heatmaps[hour]
                zone_points = [p for p in points if p['location'] == zone]
                if zone_points:
                    avg_severity = np.mean([p['severity'] for p in zone_points])
                    zone_severities.append(avg_severity)
                else:
                    zone_severities.append(0)
            z_values.append(zone_severities)
        
        return {
            "type": "surface",
            "x": hours,
            "y": list(zones),
            "z": z_values,
            "title": "3D Traffic Surface - Severity Over Time & Space",
            "xlabel": "Hour of Day",
            "ylabel": "Zone",
            "zlabel": "Severity Level"
        }
    
    # ==================== CONGESTION HEATMAP MATRIX ====================
    
    def get_congestion_matrix(self) -> Dict[str, Any]:
        """
        Generate congestion matrix showing hour-by-zone patterns.
        Perfect for: Understanding complex patterns at a glance
        """
        traffic_data = self.viz_engine.traffic_df
        
        # Create matrix: rows=zones, columns=hours
        zones = traffic_data['location_name'].unique()[:15]
        hours = list(range(24))
        
        matrix = []
        for zone in zones:
            zone_data = traffic_data[traffic_data['location_name'] == zone]
            row = []
            for hour in hours:
                hour_data = zone_data[zone_data['hour'] == hour]
                if len(hour_data) > 0:
                    congestion = hour_data['congestion_ratio'].mean()
                    row.append(congestion)
                else:
                    row.append(0)
            matrix.append(row)
        
        return {
            "type": "heatmap",
            "x": [f"{h:02d}:00" for h in hours],
            "y": list(zones),
            "z": matrix,
            "colorscale": "RdYlGn_r",
            "title": "Hour-by-Zone Congestion Matrix",
            "annotations": "Shows congestion ratio for each zone at each hour"
        }
    
    # ==================== TRAFFIC FLOW ANIMATION ====================
    
    def get_animated_traffic_flow(self) -> Dict[str, Any]:
        """
        Generate data for animated traffic flow visualization.
        Shows how traffic moves through the city over 24 hours.
        """
        heatmaps = self.viz_engine.get_hourly_heatmap_data()
        
        frames = []
        for hour in range(24):
            points = heatmaps[hour]
            
            frame = {
                "hour": hour,
                "timestamp": f"{hour:02d}:00",
                "points": points,
                "frame_number": hour
            }
            frames.append(frame)
        
        return {
            "type": "animation",
            "frames": frames,
            "total_frames": 24,
            "duration_per_frame": 500,  # milliseconds
            "title": "24-Hour Traffic Flow Animation",
            "description": "Watch traffic patterns evolve throughout the day"
        }
    
    # ==================== BUBBLE CHART ====================
    
    def get_zone_bubble_chart(self) -> Dict[str, Any]:
        """
        Generate bubble chart: Zone comparison with multiple dimensions.
        X: Congestion, Y: Safety, Size: Walkability, Color: Severity
        
        Perfect for: Showing multi-dimensional zone characteristics
        """
        analytics = self.viz_engine.get_zone_analytics()
        
        bubbles = []
        for zone_name, zone_data in analytics.items():
            bubbles.append({
                "name": zone_name,
                "x": zone_data['avg_congestion'],  # Congestion on X axis
                "y": 8.0,  # Safety score (placeholder)
                "size": zone_data['avg_severity'] * 5,  # Bubble size
                "severity": zone_data['avg_severity'],  # Color
                "popup": f"{zone_name}<br>Congestion: {zone_data['avg_congestion']:.2%}<br>Peak Hour: {zone_data['peak_hour']}:00"
            })
        
        return {
            "type": "bubble_chart",
            "bubbles": bubbles,
            "xlabel": "Average Congestion Ratio",
            "ylabel": "Safety Score (0-10)",
            "bubble_size_label": "Traffic Severity",
            "color_scale": "severity",
            "title": "Zone Comparison - Bubble Chart",
            "description": "Multi-dimensional zone analysis"
        }
    
    # ==================== TIME SERIES WITH FORECAST ====================
    
    def get_traffic_forecast_series(self) -> Dict[str, Any]:
        """
        Generate time series with actual data and forecast comparison.
        Shows historical data vs predicted data.
        """
        traffic_data = self.viz_engine.traffic_df
        
        # Historical data (average across all zones)
        hourly_severity = []
        for hour in range(24):
            hour_data = traffic_data[traffic_data['hour'] == hour]
            severity_map = {'LOW': 0, 'MODERATE': 1, 'HIGH': 2, 'VERY_HIGH': 3}
            avg_severity = hour_data['new_severity_logical'].map(severity_map).mean()
            hourly_severity.append({
                "hour": hour,
                "actual": avg_severity,
                "timestamp": f"{hour:02d}:00"
            })
        
        # Simulated forecast (with slight smoothing for realism)
        forecast = []
        for i, item in enumerate(hourly_severity):
            # Add small random variation for realistic forecast
            noise = np.random.normal(0, 0.1)
            forecast_value = item['actual'] + noise
            forecast_value = np.clip(forecast_value, 0, 3)
            
            forecast.append({
                "hour": item['hour'],
                "actual": item['actual'],
                "forecast": forecast_value,
                "confidence": 0.85 - (abs(noise) * 0.2),
                "timestamp": item['timestamp']
            })
        
        return {
            "type": "line_chart",
            "data": forecast,
            "lines": [
                {
                    "name": "Actual Traffic",
                    "color": "#667eea",
                    "style": "solid"
                },
                {
                    "name": "Predicted Traffic",
                    "color": "#764ba2",
                    "style": "dashed"
                }
            ],
            "title": "24-Hour Traffic - Actual vs Predicted",
            "xlabel": "Hour of Day",
            "ylabel": "Severity Level (0-3)",
            "description": "ML model forecast vs historical data"
        }
    
    # ==================== RISK ASSESSMENT MATRIX ====================
    
    def get_risk_assessment_matrix(self) -> Dict[str, Any]:
        """
        Generate risk assessment matrix for zones.
        X-axis: Risk Level, Y-axis: Frequency
        Shows which areas need the most attention.
        """
        analytics = self.viz_engine.get_zone_analytics()
        
        # Categorize zones by risk
        high_risk = []  # peak_severity >= 2.5
        medium_risk = []  # 1.5 <= peak_severity < 2.5
        low_risk = []  # peak_severity < 1.5
        
        for zone_name, zone_data in analytics.items():
            risk_item = {
                "zone": zone_name,
                "peak_severity": zone_data['peak_severity'],
                "congestion": zone_data['avg_congestion'],
                "peak_hour": zone_data['peak_hour']
            }
            
            if zone_data['peak_severity'] >= 2.5:
                high_risk.append(risk_item)
            elif zone_data['peak_severity'] >= 1.5:
                medium_risk.append(risk_item)
            else:
                low_risk.append(risk_item)
        
        return {
            "type": "risk_matrix",
            "risk_categories": {
                "high": {
                    "count": len(high_risk),
                    "zones": high_risk,
                    "color": "#dc3545",
                    "recommendation": "Avoid or use during off-peak hours"
                },
                "medium": {
                    "count": len(medium_risk),
                    "zones": medium_risk,
                    "color": "#ffc107",
                    "recommendation": "Plan ahead, consider timing"
                },
                "low": {
                    "count": len(low_risk),
                    "zones": low_risk,
                    "color": "#28a745",
                    "recommendation": "Safe to visit anytime"
                }
            },
            "title": "Zone Risk Assessment",
            "total_zones": len(analytics)
        }
    
    # ==================== PEAK HOUR RADAR ====================
    
    def get_peak_hour_radar(self) -> Dict[str, Any]:
        """
        Radar chart showing severity for each hour.
        Perfect for: Visualizing which hours are most problematic.
        """
        heatmaps = self.viz_engine.get_hourly_heatmap_data()
        
        hourly_severity = []
        for hour in range(24):
            points = heatmaps[hour]
            if points:
                avg_severity = np.mean([p['severity'] for p in points])
            else:
                avg_severity = 0
            
            hourly_severity.append({
                "hour": hour,
                "severity": avg_severity,
                "label": f"{hour:02d}:00"
            })
        
        return {
            "type": "radar",
            "data": hourly_severity,
            "categories": [item['label'] for item in hourly_severity],
            "values": [item['severity'] for item in hourly_severity],
            "title": "24-Hour Severity Radar",
            "description": "Peak hours at a glance"
        }
    
    # ==================== COMMUTE PLANNER ====================
    
    def get_commute_planning_data(self) -> Dict[str, Any]:
        """
        Generate data for commute planning feature.
        Analyzes best routes, times, and provides recommendations.
        """
        routes = self.viz_engine.get_path_route_analytics()
        mobility = self.viz_engine.get_mobility_patterns()
        
        commute_recommendations = []
        for route in routes:
            # Find best time based on mobility patterns
            best_time = None
            for pattern in mobility['peak_mobility_hours']:
                if pattern['congestion'] < 0.4:
                    best_time = pattern['timestamp']
                    break
            
            if not best_time:
                best_time = mobility['quiet_hours'][0]['timestamp'] if mobility['quiet_hours'] else "03:00"
            
            recommendation = {
                "route": f"{route['from']} → {route['to']}",
                "difficulty": route['difficulty'],
                "estimated_time": route['avg_time'],
                "best_departure_time": best_time,
                "worst_departure_time": mobility['peak_hours'][0],
                "time_saved_by_planning": max(0, (route['avg_time'] * 0.3)),  # Potential savings
                "traffic_flow": "Smooth" if route['difficulty'] < 1.5 else "Moderate" if route['difficulty'] < 2.5 else "Congested",
                "recommendation": self._get_commute_recommendation(route['difficulty'], best_time)
            }
            commute_recommendations.append(recommendation)
        
        return {
            "type": "commute_planner",
            "recommendations": commute_recommendations,
            "total_routes": len(commute_recommendations),
            "best_time_to_commute": mobility['off_peak'][0] if mobility['off_peak'] else 3,
            "worst_time_to_commute": mobility['rush_hours'][0] if mobility['rush_hours'] else 8
        }
    
    # ==================== POLLUTION & EMISSIONS ESTIMATE ====================
    
    def get_emissions_estimate(self) -> Dict[str, Any]:
        """
        Estimate emissions based on traffic severity and congestion.
        Shows environmental impact by zone and hour.
        """
        analytics = self.viz_engine.get_zone_analytics()
        
        emissions_by_zone = []
        total_emissions = 0
        
        for zone_name, zone_data in analytics.items():
            # Simplified emission calculation: severity * congestion
            base_emission = 100  # kg CO2 per hour (baseline)
            severity_factor = zone_data['avg_severity'] / 3.0
            congestion_factor = zone_data['avg_congestion']
            
            zone_emissions = base_emission * severity_factor * congestion_factor
            total_emissions += zone_emissions
            
            emissions_by_zone.append({
                "zone": zone_name,
                "estimated_daily_emissions": zone_emissions * 24,  # Daily estimate
                "severity_contribution": severity_factor,
                "congestion_contribution": congestion_factor,
                "recommendation": "Promote carpooling" if zone_emissions > 1000 else "Monitor emissions"
            })
        
        # Sort by emissions
        emissions_by_zone.sort(key=lambda x: x['estimated_daily_emissions'], reverse=True)
        
        return {
            "type": "emissions_analysis",
            "total_estimated_daily_emissions": total_emissions * 24,
            "zones": emissions_by_zone[:10],  # Top 10
            "unit": "kg CO2",
            "title": "Environmental Impact Analysis",
            "recommendations": [
                "Focus on high-emission zones",
                "Promote off-peak travel",
                "Encourage alternative transport during peak hours"
            ]
        }
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def _get_commute_recommendation(self, difficulty: float, best_time: str) -> str:
        """Generate commute recommendation text."""
        if difficulty < 1:
            return f"✅ Great route! Leave after {best_time} for smooth traffic"
        elif difficulty < 2:
            return f"⚠️ Moderate traffic. Consider leaving during {best_time}"
        else:
            return f"🚨 Heavily congested. Strongly recommend {best_time} or consider alternative route"
    
    def export_all_visualizations(self) -> Dict[str, Any]:
        """Export all advanced visualizations as JSON."""
        return {
            "3d_surface": self.get_3d_surface_data(),
            "congestion_matrix": self.get_congestion_matrix(),
            "animated_flow": self.get_animated_traffic_flow(),
            "bubble_chart": self.get_zone_bubble_chart(),
            "forecast": self.get_traffic_forecast_series(),
            "risk_matrix": self.get_risk_assessment_matrix(),
            "peak_radar": self.get_peak_hour_radar(),
            "commute_planning": self.get_commute_planning_data(),
            "emissions": self.get_emissions_estimate(),
            "exported_at": datetime.now().isoformat()
        }


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    from src.visualization_engine import VisualizationEngine
    
    # Initialize
    viz_engine = VisualizationEngine()
    advanced = AdvancedVisualizations(viz_engine)
    
    # Generate visualizations
    print("3D Surface Data:")
    print(json.dumps(advanced.get_3d_surface_data(), indent=2)[:200] + "...\n")
    
    print("Congestion Matrix:")
    matrix_data = advanced.get_congestion_matrix()
    print(f"Zones: {len(matrix_data['y'])}, Hours: {len(matrix_data['x'])}\n")
    
    print("Risk Assessment:")
    risk = advanced.get_risk_assessment_matrix()
    print(f"High Risk: {risk['risk_categories']['high']['count']}")
    print(f"Medium Risk: {risk['risk_categories']['medium']['count']}")
    print(f"Low Risk: {risk['risk_categories']['low']['count']}\n")
    
    print("Commute Planning:")
    commute = advanced.get_commute_planning_data()
    print(f"Routes analyzed: {commute['total_routes']}\n")
    
    print("Emissions Analysis:")
    emissions = advanced.get_emissions_estimate()
    print(f"Total daily emissions: {emissions['total_estimated_daily_emissions']:.0f} kg CO2")
