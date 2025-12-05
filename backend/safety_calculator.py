import math
import json
from typing import List, Tuple, Dict
from datetime import datetime, timedelta
from safety_models import DangerZone, RoutePoint


class SafetyCalculator:
    """Calculate safety metrics for routes using comprehensive data"""
    
    def __init__(self, data_file: str = "safety_data.json"):
        """Initialize with danger zone data"""
        self.danger_zones = []
        self.safe_zones = []
        self.load_data(data_file)
    
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
    
    def calculate_route_danger_index(self, route_points: List[Tuple[float, float]], 
                                     threshold: float = 150) -> Tuple[float, int]:
        """
        Calculate danger index for a route using comprehensive metrics
        
        Returns:
            (danger_index: float [0-1], danger_points_count: int)
        """
        total_danger = 0.0
        danger_count = 0
        processed_zones = set()
        
        for lat, lon in route_points:
            is_near, zone_data, distance = self.is_point_near_danger_zone(lat, lon, threshold)
            
            if is_near:
                zone_key = (zone_data['latitude'], zone_data['longitude'])
                if zone_key not in processed_zones:
                    # Use comprehensive danger index instead of just magnitude
                    danger_score = self.calculate_comprehensive_danger_index(zone_data)
                    total_danger += danger_score
                    danger_count += 1
                    processed_zones.add(zone_key)
        
        if danger_count > 0:
            danger_index = total_danger / danger_count
        else:
            danger_index = 0.0
        
        return round(danger_index, 3), danger_count
    
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
    """Optimize and rank routes by comprehensive safety metrics"""
    
    @staticmethod
    def sort_routes_by_safety(routes: List[Dict]) -> List[Dict]:
        """
        Sort routes by danger index
        Returns routes sorted from safest to most dangerous
        """
        sorted_routes = sorted(routes, key=lambda x: x['danger_index'])
        
        route_names = ["Safest Route", "Moderate Route", "Risky Route"]
        danger_levels_map = ["green", "yellow", "red"]
        
        for idx, route in enumerate(sorted_routes):
            route['route_id'] = idx + 1
            route['route_name'] = route_names[idx] if idx < len(route_names) else f"Route {idx + 1}"
            route['danger_level'] = danger_levels_map[idx] if idx < len(danger_levels_map) else "red"
        
        return sorted_routes