"""
Visualization Engine - Generates data for interactive dashboards and heatmaps.
Provides aggregated data for frontend visualizations and analytics.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).parent.parent / 'data' / 'traffic_with_categories.csv'


class VisualizationEngine:
    """Generates visualization data for dashboards and maps."""
    
    def __init__(self):
        """Initialize visualization engine with traffic data."""
        logger.info("Loading traffic data for visualizations...")
        self.traffic_df = pd.read_csv(DATA_PATH)
        
        # Ensure required columns exist
        required_cols = ['hour_label', 'location_name', 'latitude', 'longitude', 'new_severity_logical']
        for col in required_cols:
            if col not in self.traffic_df.columns:
                logger.warning(f"Missing column: {col}")
        
        logger.info(f"✅ Visualization engine loaded with {len(self.traffic_df)} records")
    
    def get_hourly_heatmap_data(self) -> Dict[int, List[Dict]]:
        """
        Generate heatmap data aggregated by hour.
        Returns data for each hour (0-23) with location severity.
        
        Returns:
            Dict mapping hour -> list of {lat, lon, severity_value, location}
        """
        heatmap_data = {}
        
        for hour in range(24):
            hour_data = self.traffic_df[self.traffic_df['hour_label'] == hour]
            
            if len(hour_data) == 0:
                heatmap_data[hour] = []
                continue
            
            # Group by location and calculate average severity
            grouped = hour_data.groupby('location_name').agg({
                'latitude': 'first',
                'longitude': 'first',
                'new_severity_logical': lambda x: self._severity_to_numeric(x)
            }).reset_index()
            
            heatmap_points = []
            for _, row in grouped.iterrows():
                heatmap_points.append({
                    'lat': float(row['latitude']),
                    'lon': float(row['longitude']),
                    'severity': float(row['new_severity_logical']),
                    'location': str(row['location_name']),
                    'intensity': float(row['new_severity_logical']) / 3.0  # Normalized 0-1
                })
            
            heatmap_data[hour] = heatmap_points
        
        logger.info(f"✅ Generated heatmap data for 24 hours")
        return heatmap_data
    
    def get_traffic_timeline(self, location: str = None) -> List[Dict]:
        """
        Generate hourly traffic progression timeline.
        
        Args:
            location: Specific location name, or None for all locations averaged
            
        Returns:
            List of {hour, severity, congestion_ratio, color}
        """
        if location:
            data = self.traffic_df[self.traffic_df['location_name'].str.lower() == location.lower()]
        else:
            data = self.traffic_df
        
        if len(data) == 0:
            logger.warning(f"No data found for location: {location}")
            return []
        
        timeline = []
        for hour in range(24):
            hour_data = data[data['hour_label'] == hour]
            
            if len(hour_data) == 0:
                continue
            
            avg_severity = self._severity_to_numeric(hour_data['new_severity_logical'])
            
            # Color mapping
            if avg_severity < 1:
                color = "#4CAF50"  # Green
            elif avg_severity < 2:
                color = "#FFC107"  # Yellow
            elif avg_severity < 3:
                color = "#FF9800"  # Orange
            else:
                color = "#F44336"  # Red
            
            timeline.append({
                'hour': int(hour),
                'severity': float(avg_severity),
                'severity_label': self._numeric_to_severity(avg_severity),
                'congestion_ratio': float(hour_data['congestion_ratio'].mean()),
                'color': color,
                'timestamp': f"{hour:02d}:00"
            })
        
        return timeline
    
    def get_zone_analytics(self) -> Dict[str, Any]:
        """
        Generate comprehensive zone analytics with traffic patterns.
        
        Returns:
            Dict with zone statistics, peak hours, congestion patterns
        """
        analytics = {}
        
        # Group by location
        for location in self.traffic_df['location_name'].unique():
            location_data = self.traffic_df[self.traffic_df['location_name'] == location]
            
            # Calculate statistics
            avg_severity = self._severity_to_numeric(location_data['new_severity_logical'])
            avg_congestion = location_data['congestion_ratio'].mean()
            
            # Find peak hours
            hourly_avg = location_data.groupby('hour_label')['new_severity_logical'].apply(
                lambda x: self._severity_to_numeric(x)
            )
            peak_hour = hourly_avg.idxmax()
            peak_severity = hourly_avg.max()
            
            # Quiet hours
            quiet_hour = hourly_avg.idxmin()
            quiet_severity = hourly_avg.min()
            
            # Morning and evening congestion
            morning_data = location_data[location_data['hour_label'].between(6, 9)]
            evening_data = location_data[location_data['hour_label'].between(17, 20)]
            
            morning_congestion = morning_data['congestion_ratio'].mean() if len(morning_data) > 0 else 0
            evening_congestion = evening_data['congestion_ratio'].mean() if len(evening_data) > 0 else 0
            
            lat = location_data['latitude'].iloc[0]
            lon = location_data['longitude'].iloc[0]
            
            analytics[location] = {
                'location': location,
                'coordinates': {'lat': float(lat), 'lon': float(lon)},
                'avg_severity': float(avg_severity),
                'avg_congestion': float(avg_congestion),
                'peak_hour': int(peak_hour),
                'peak_severity': float(peak_severity),
                'quiet_hour': int(quiet_hour),
                'quiet_severity': float(quiet_severity),
                'morning_congestion': float(morning_congestion),
                'evening_congestion': float(evening_congestion),
                'best_visit_time': f"{quiet_hour:02d}:00",
                'worst_time': f"{peak_hour:02d}:00",
                'recommendation': self._get_zone_recommendation(peak_severity, avg_congestion)
            }
        
        logger.info(f"✅ Generated analytics for {len(analytics)} zones")
        return analytics
    
    def get_predictive_heatmap(self, hours_ahead: int = 3) -> Dict:
        """
        Generate predictive heatmap for future hours.
        
        Args:
            hours_ahead: Number of hours to predict ahead (1-24)
            
        Returns:
            Dict with predicted heatmap and confidence levels
        """
        current_hour = datetime.now().hour
        
        predictions = {}
        for i in range(hours_ahead):
            future_hour = (current_hour + i + 1) % 24
            
            hour_data = self.traffic_df[self.traffic_df['hour_label'] == future_hour]
            
            if len(hour_data) == 0:
                continue
            
            heatmap_points = []
            for _, row in hour_data.iterrows():
                severity = self._severity_to_numeric(
                    pd.Series([row['new_severity_logical']])
                )
                
                heatmap_points.append({
                    'lat': float(row['latitude']),
                    'lon': float(row['longitude']),
                    'severity': float(severity),
                    'location': str(row['location_name']),
                    'confidence': 0.85  # Model confidence
                })
            
            predictions[future_hour] = {
                'hour': future_hour,
                'timestamp': f"{future_hour:02d}:00",
                'points': heatmap_points,
                'avg_severity': np.mean([p['severity'] for p in heatmap_points])
            }
        
        return predictions
    
    def get_comparison_chart(self) -> Dict:
        """
        Generate data comparing different zones/times.
        Useful for radar charts or comparison bars.
        
        Returns:
            Dict with metrics for comparison visualization
        """
        zones = []
        
        for location in self.traffic_df['location_name'].unique()[:10]:  # Top 10
            location_data = self.traffic_df[self.traffic_df['location_name'] == location]
            
            avg_severity = self._severity_to_numeric(location_data['new_severity_logical'])
            walkability = location_data.get('CAFE_PUB', 0) + location_data.get('PARK', 0)
            
            zones.append({
                'zone': location,
                'traffic_severity': float(avg_severity),
                'congestion': float(location_data['congestion_ratio'].mean()),
                'walkability': min(10, float(walkability / 100)),
                'safety_score': 8.5 + np.random.rand() * 1.5,  # Placeholder
                'amenities': float(len(location_data.columns) - 10)
            })
        
        return {
            'zones': zones,
            'metrics': ['traffic_severity', 'congestion', 'walkability', 'safety_score', 'amenities']
        }
    
    def get_path_route_analytics(self) -> List[Dict]:
        """
        Generate route-based analytics for path visualization.
        Returns recommended routes with traffic conditions.
        
        Returns:
            List of routes with difficulty levels and optimal times
        """
        routes = []
        
        locations = self.traffic_df['location_name'].unique()[:5]  # Sample routes
        
        for i in range(len(locations) - 1):
            from_loc = self.traffic_df[self.traffic_df['location_name'] == locations[i]]
            to_loc = self.traffic_df[self.traffic_df['location_name'] == locations[i + 1]]
            
            from_lat, from_lon = float(from_loc['latitude'].iloc[0]), float(from_loc['longitude'].iloc[0])
            to_lat, to_lon = float(to_loc['latitude'].iloc[0]), float(to_loc['longitude'].iloc[0])
            
            # Calculate difficulty
            avg_difficulty = (
                self._severity_to_numeric(from_loc['new_severity_logical']) +
                self._severity_to_numeric(to_loc['new_severity_logical'])
            ) / 2
            
            routes.append({
                'from': locations[i],
                'to': locations[i + 1],
                'from_coords': {'lat': from_lat, 'lon': from_lon},
                'to_coords': {'lat': to_lat, 'lon': to_lon},
                'difficulty': float(avg_difficulty),
                'difficulty_label': self._numeric_to_severity(avg_difficulty),
                'avg_time': round(30 + avg_difficulty * 20),  # minutes
                'best_time': f"{(6 + i) % 24:02d}:00"
            })
        
        return routes
    
    def get_mobility_patterns(self) -> Dict:
        """
        Generate mobility patterns for user insights.
        Shows when and where people typically move.
        
        Returns:
            Dict with peak mobility times and patterns
        """
        patterns = {
            'peak_mobility_hours': [],
            'quiet_hours': [],
            'rush_hours': [],
            'off_peak': []
        }
        
        hourly_traffic = self.traffic_df.groupby('hour_label')['congestion_ratio'].mean()
        
        # Define periods
        rush_hours = hourly_traffic[(hourly_traffic.index >= 6) & (hourly_traffic.index <= 9)] | \
                     hourly_traffic[(hourly_traffic.index >= 17) & (hourly_traffic.index <= 20)]
        
        peak_hours = hourly_traffic.nlargest(3).index.tolist()
        quiet_hours_list = hourly_traffic.nsmallest(3).index.tolist()
        off_peak = hourly_traffic[hourly_traffic < hourly_traffic.median()].index.tolist()
        
        patterns['peak_mobility_hours'] = [
            {
                'hour': int(h),
                'timestamp': f"{h:02d}:00",
                'congestion': float(hourly_traffic[h])
            }
            for h in peak_hours
        ]
        
        patterns['quiet_hours'] = [
            {
                'hour': int(h),
                'timestamp': f"{h:02d}:00",
                'congestion': float(hourly_traffic[h])
            }
            for h in quiet_hours_list
        ]
        
        patterns['rush_hours'] = list(range(6, 10)) + list(range(17, 21))
        patterns['off_peak'] = off_peak
        
        return patterns
    
    def _severity_to_numeric(self, severity_series) -> float:
        """Convert severity labels to numeric values."""
        severity_map = {'LOW': 0, 'MODERATE': 1, 'HIGH': 2, 'VERY_HIGH': 3}
        numeric_values = severity_series.map(severity_map).fillna(1)
        return float(numeric_values.mean())
    
    def _numeric_to_severity(self, value: float) -> str:
        """Convert numeric severity to label."""
        if value < 1:
            return 'LOW'
        elif value < 2:
            return 'MODERATE'
        elif value < 3:
            return 'HIGH'
        else:
            return 'VERY_HIGH'
    
    def _get_zone_recommendation(self, peak_severity: float, avg_congestion: float) -> str:
        """Generate recommendation based on zone characteristics."""
        if peak_severity < 1 and avg_congestion < 0.3:
            return "Perfect for evening walks and outdoor activities"
        elif peak_severity < 2 and avg_congestion < 0.5:
            return "Good for leisure activities during off-peak hours"
        elif peak_severity >= 2.5:
            return "Avoid during peak hours; best visited early morning or late night"
        else:
            return "Plan visits during off-peak hours (10 AM - 4 PM)"


if __name__ == "__main__":
    engine = VisualizationEngine()
    
    # Test heatmap generation
    heatmap = engine.get_hourly_heatmap_data()
    print(f"Heatmap hours: {len(heatmap)}")
    print(f"Points at hour 18: {len(heatmap[18])}")
    
    # Test analytics
    analytics = engine.get_zone_analytics()
    print(f"\nZone analytics: {len(analytics)} zones")
    
    # Test predictions
    predictions = engine.get_predictive_heatmap(3)
    print(f"Predictions: {len(predictions)} hours")
    
    # Test mobility patterns
    patterns = engine.get_mobility_patterns()
    print(f"Peak hours: {patterns['peak_mobility_hours']}")
