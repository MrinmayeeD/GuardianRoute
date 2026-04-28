import math
import json
from typing import List, Tuple, Dict
from datetime import datetime, timedelta
from safety_models import DangerZone, RoutePoint
import joblib
import numpy as np
import math
from datetime import datetime

class SafetyCalculator:
    """Calculate safety metrics for routes using comprehensive data"""
    
    # def __init__(self, data_file: str = "safety_data.json"):
    #     """Initialize with danger zone data"""
    #     self.danger_zones = []
    #     self.safe_zones = []
    #     self.load_data(data_file)
    def __init__(self):
        self.model = joblib.load("models/best_model.pkl")
        self.kmeans = joblib.load("models/kmeans.pkl")
        self.scaler = joblib.load("models/scaler.pkl")
        self.hourly_counts = joblib.load("models/hourly_counts.pkl")
        self.daily_counts = joblib.load("models/daily_counts.pkl")
        self.monthly_violent = joblib.load("models/monthly_violent.pkl")
        self.hotspot_coords = joblib.load("models/hotspot_coords.pkl")
        clean_hotspots = []

        for h in self.hotspot_coords:
            try:
                lat = float(h[0])
                lon = float(h[1])
                clean_hotspots.append((lat, lon))
            except (ValueError, TypeError):
                print("❌ Skipping invalid hotspot:", h)

        self.hotspot_coords = clean_hotspots 
        print("🔥 Using MY ML SafetyCalculator 🔥")
    
    def load_data(self, data_file: str):
        """Load danger zones with comprehensive safety data"""
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
                self.danger_zones = [DangerZone(**zone) for zone in data.get('danger_zones', [])]
                self.safe_zones = data.get('safe_zones', [])
        except FileNotFoundError:
            print(f"Warning: {data_file} not found. Using empty danger zones.")
            self.danger_zones = []
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in meters"""
        R = 6371000  # Earth's radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def calculate_incident_severity_weight(self, zone_dict: dict) -> float:
        """
        Calculate weighted severity based on recent incidents
        Recent incidents have higher weight
        """
        incidents = zone_dict.get('historical_incidents', [])
        if not incidents:
            return 1.0
        
        total_weight = 0.0
        current_date = datetime.now()
        
        for incident in incidents:
            try:
                incident_date = datetime.strptime(incident['date'], '%Y-%m-%d')
                days_ago = (current_date - incident_date).days
                
                # Recent incidents (0-30 days) = 1.0x weight
                # 31-60 days = 0.7x weight
                # 61-90 days = 0.4x weight
                if days_ago <= 30:
                    weight = 1.0
                elif days_ago <= 60:
                    weight = 0.7
                else:
                    weight = 0.4
                
                severity = incident.get('severity', 2)
                total_weight += (severity / 5.0) * weight
            except ValueError:
                continue
        
        return min(total_weight / len(incidents) if incidents else 0, 1.0)
    
    def calculate_comprehensive_danger_index(self, zone_dict: dict) -> float:
        """
        Calculate danger index using multiple factors:
        - Crime density (40%)
        - Accident rate (30%)
        - Trending (20%)
        - Recent incident severity (10%)
        """
        crime_data = zone_dict.get('crime_data', {})
        accident_data = zone_dict.get('accident_data', {})
        
        # Crime component (40%) - normalize to 0-1 scale
        crime_density = min(crime_data.get('crime_density', 0) / 5.0, 1.0)
        
        # Accident component (30%) - normalize to 0-1 scale
        accident_rate = min(accident_data.get('accident_rate', 0) / 3.0, 1.0)
        
        # Trending component (20%)
        trending = crime_data.get('trending', 'stable')
        trending_factor = {
            'increasing': 1.0,
            'stable': 0.5,
            'decreasing': 0.2
        }.get(trending, 0.5)
        
        # Historical incident component (10%)
        incident_weight = self.calculate_incident_severity_weight(zone_dict)
        
        # Weighted calculation
        danger_index = (
            crime_density * 0.4 +
            accident_rate * 0.3 +
            trending_factor * 0.2 +
            incident_weight * 0.1
        )
        
        return round(danger_index, 3)
    
    def is_point_near_danger_zone(self, lat: float, lon: float, threshold: float = 150) -> Tuple[bool, dict, float]:
        """
        Check if a point is near a danger zone (within threshold meters)
        Returns: (is_near, zone_data_dict, distance)
        """
        for zone in self.danger_zones:
            distance = self.haversine_distance(lat, lon, zone.latitude, zone.longitude)
            if distance <= threshold:
                # Return zone as dictionary with all fields
                return True, zone.__dict__, distance
        return False, {}, float('inf')


    def calculate_route_danger_index(self, route_points):

        if not route_points:
            return 0.0, 0

        now = datetime.now()
        hour = now.hour
        day_of_week = now.weekday()
        month = now.month

        # Convert all points to numpy array at once
        coords = []
        for point in route_points:
            try:
                lat = float(point[0])
                lon = float(point[1])
                coords.append([lat, lon])
            except (ValueError, TypeError):
                continue

        if not coords:
            return 0.0, 0

        coords = np.array(coords)

        # 1️⃣ Predict clusters for ALL points at once
        clusters = self.kmeans.predict(coords)

        crimes_hour = self.hourly_counts.get(hour, 0)
        crimes_weekday = self.daily_counts.get(day_of_week, 0)
        crimes_month = self.monthly_violent.get(month, 0)

        # 2️⃣ Compute hotspot distances (vectorized)
        if self.hotspot_coords:
            hotspots = np.array(self.hotspot_coords)
            dists = np.sqrt(
                (coords[:, None, 0] - hotspots[:, 0]) ** 2 +
                (coords[:, None, 1] - hotspots[:, 1]) ** 2
            )
            hotspot_dist = dists.min(axis=1)
        else:
            hotspot_dist = np.zeros(len(coords))

        # 3️⃣ Build feature matrix for ALL points
        features = np.column_stack([
            coords[:, 0],  # lat
            coords[:, 1],  # lon
            np.full(len(coords), hour),
            np.full(len(coords), day_of_week),
            np.full(len(coords), month),
            clusters,
            np.full(len(coords), crimes_hour),
            np.full(len(coords), crimes_weekday),
            hotspot_dist,
            np.full(len(coords), crimes_month)
        ])

        # 4️⃣ Scale once
        features_scaled = self.scaler.transform(features)

        # 5️⃣ Predict probabilities for ALL points at once
        probs = self.model.predict_proba(features_scaled)[:, 1]

        avg_danger = float(np.mean(probs))

        return round(avg_danger, 3), len(coords)
    
    def get_danger_level_and_color(self, danger_index: float) -> Tuple[str, str]:
        """
        Map danger index to danger level and color
        
        Returns:
            (danger_level: str, color_code: str)
        """
        if danger_index <= 0.25:
            return "green", "#00AA00"      # Safe
        elif danger_index <= 0.50:
            return "yellow", "#FFFF00"    # Moderate
        elif danger_index <= 0.75:
            return "orange", "#FFA500"    # High
        else:
            return "red", "#FF0000"       # Dangerous
    
    def get_zone_safety_details(self, lat: float, lon: float) -> Dict:
        """Get detailed safety information for a location"""
        is_near, zone_data, distance = self.is_point_near_danger_zone(lat, lon, 300)
        
        if is_near:
            return {
                'zone_name': zone_data.get('name', 'Unknown'),
                'distance_m': round(distance, 1),
                'crime_incidents': zone_data.get('crime_data', {}).get('annual_crimes', 0),
                'accidents_yearly': zone_data.get('accident_data', {}).get('annual_accidents', 0),
                'safety_score': zone_data.get('safety_score', 50),
                'pedestrian_risk': zone_data.get('pedestrian_risk', 'medium'),
                'trending': zone_data.get('crime_data', {}).get('trending', 'stable')
            }
        return {}


class RouteOptimizer:

    @staticmethod
    def sort_routes_by_safety(routes: List[Dict]) -> List[Dict]:

        if not routes:
            return []

        # Sort by danger index (lowest first)
        sorted_routes = sorted(routes, key=lambda x: x['danger_index'])

        safest_route = sorted_routes[0]

        safest_route['route_id'] = 1
        safest_route['route_name'] = "Safest Route"
        safest_route['danger_level'] = "green"

        # 🔥 Return only ONE route
        return [safest_route]