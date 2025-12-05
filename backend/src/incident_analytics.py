"""
Real-time Traffic Incident Analytics Engine
Fetches and analyzes incidents from TomTom API
"""

import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any
from collections import Counter
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IncidentAnalytics:
    """Analyzes real-time traffic incidents and generates insights."""
    
    # Incident type mapping (TomTom codes)
    INCIDENT_TYPES = {
        0: "Unknown",
        1: "Accident",
        2: "Fog",
        3: "Dangerous Conditions",
        4: "Rain",
        5: "Ice",
        6: "Jam",
        7: "Lane Closed",
        8: "Road Closed",
        9: "Road Works",
        10: "Wind",
        11: "Flooding",
        14: "Broken Down Vehicle"
    }
    
    # Severity mapping
    SEVERITY_COLORS = {
        0: {"label": "Unknown", "color": "#808080"},
        1: {"label": "Minor", "color": "#4CAF50"},
        2: {"label": "Moderate", "color": "#FFC107"},
        3: {"label": "Major", "color": "#FF9800"},
        4: {"label": "Severe", "color": "#F44336"}
    }
    
    def __init__(self, api_key: str = None):
        """Initialize with TomTom API key."""
        self.api_key = api_key or os.getenv("TOMTOM_API_KEY")
        if not self.api_key:
            raise ValueError("TOMTOM_API_KEY not found")
        
        self.base_url = "https://api.tomtom.com/traffic/services/5/incidentDetails"
        logger.info("✅ IncidentAnalytics initialized")
    
    def fetch_incidents_for_region(
        self, 
        center_lat: float, 
        center_lon: float, 
        radius_km: float = 10
        ) -> List[Dict]:
        """
        Fetch all incidents within a radius from center point.
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_km: Radius in kilometers
            
        Returns:
            List of incident dictionaries
        """
        try:
            # Calculate bounding box (approximate)
            lat_delta = radius_km / 111.0  # 1 degree ≈ 111 km
            lon_delta = radius_km / (111.0 * abs(center_lat / 90.0))
            
            bbox = f"{center_lon - lon_delta},{center_lat - lat_delta}," \
                   f"{center_lon + lon_delta},{center_lat + lat_delta}"
            
            params = {
                "bbox": bbox,
                "key": self.api_key,
                "categoryFilter": "0,1,2,3,4,5,6,7,8,9,10,11,14",  # All incident types
                "timeValidityFilter": "present"
            }
            
            logger.info(f"🔍 Fetching incidents for region (radius: {radius_km}km)")
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            incidents = data.get("incidents", [])
            logger.info(f"✅ Found {len(incidents)} active incidents")
            
            return self._parse_incidents(incidents)
            
        except Exception as e:
            logger.error(f"❌ Error fetching incidents: {e}")
            return []
    
    def _parse_incidents(self, raw_incidents: List[Dict]) -> List[Dict]:
        """Parse raw TomTom incident data into structured format."""
        parsed = []
        
        for inc in raw_incidents:
            try:
                properties = inc.get("properties", {})
                geometry = inc.get("geometry", {})
                
                # Extract description (try multiple fields)
                description = "No description"
                if "events" in properties and properties["events"]:
                    description = properties["events"][0].get("description", "No description")
                elif "description" in properties:
                    description = properties.get("description", "No description")
                
                # Extract location info
                from_street = properties.get("from", "")
                to_street = properties.get("to", "")
                
                # Try alternative location fields if from/to are empty
                if not from_street and not to_street:
                    # Check for road name or street
                    from_street = properties.get("road", properties.get("street", ""))
                
                # Get coordinates
                coords = [[0, 0]]
                if geometry and "coordinates" in geometry:
                    coords = geometry["coordinates"]
                    if not coords or len(coords) == 0:
                        coords = [[0, 0]]
                
                # Extract delay (try multiple fields)
                delay_seconds = 0
                if "delay" in properties:
                    delay_seconds = properties.get("delay", 0)
                elif "delaySeconds" in properties:
                    delay_seconds = properties.get("delaySeconds", 0)
                
                # Extract severity
                severity = properties.get("magnitudeOfDelay", 0)
                if severity not in self.SEVERITY_COLORS:
                    severity = 0
                
                incident = {
                    "id": properties.get("id", f"INC_{len(parsed)}"),
                    "type_code": properties.get("iconCategory", 0),
                    "type": self.INCIDENT_TYPES.get(properties.get("iconCategory", 0), "Unknown"),
                    "description": description[:200] if description else "No description",
                    "severity": severity,
                    "severity_label": self.SEVERITY_COLORS[severity]["label"],
                    "delay_seconds": delay_seconds,
                    "delay_minutes": delay_seconds / 60,
                    "start_time": properties.get("startTime"),
                    "end_time": properties.get("endTime"),
                    "from_street": from_street,
                    "to_street": to_street,
                    "length_meters": properties.get("length", 0),
                    "length_km": properties.get("length", 0) / 1000,
                    "coordinates": coords[0] if isinstance(coords[0], list) else coords
                }
                
                parsed.append(incident)
                
            except Exception as e:
                logger.warning(f"⚠️ Error parsing incident: {e}")
                continue
        
        return parsed
    
    def generate_analytics(self, incidents: List[Dict]) -> Dict[str, Any]:
        """
        Generate comprehensive analytics from incidents.
        
        Returns:
            Dictionary with analytics data for visualization
        """
        if not incidents:
            return self._empty_analytics()
        
        # Basic stats
        total = len(incidents)
        
        # Type distribution
        type_counts = Counter([inc["type"] for inc in incidents])
        type_distribution = [
            {"type": type_name, "count": count, "percentage": (count/total)*100}
            for type_name, count in type_counts.most_common()
        ]
        
        # Severity distribution
        severity_counts = Counter([inc["severity"] for inc in incidents])
        severity_distribution = []
        for severity, count in sorted(severity_counts.items()):
            severity_info = self.SEVERITY_COLORS[severity]
            severity_distribution.append({
                "severity": severity,
                "label": severity_info["label"],
                "color": severity_info["color"],
                "count": count,
                "percentage": (count/total)*100
            })
        
        # Delay analysis
        total_delay_hours = sum([inc["delay_minutes"] for inc in incidents]) / 60
        avg_delay_minutes = sum([inc["delay_minutes"] for inc in incidents]) / total
        max_delay_incident = max(incidents, key=lambda x: x["delay_minutes"])
        
        # Top incidents by delay
        top_delayed = sorted(incidents, key=lambda x: x["delay_minutes"], reverse=True)[:5]
        
        # Geographic hotspots (simple clustering by coordinates)
        hotspots = self._identify_hotspots(incidents)
        
        # Time-based analysis (if timestamps available)
        time_analysis = self._analyze_time_patterns(incidents)
        
        return {
            "summary": {
                "total_incidents": total,
                "total_delay_hours": round(total_delay_hours, 2),
                "average_delay_minutes": round(avg_delay_minutes, 2),
                "most_common_type": type_distribution[0]["type"] if type_distribution else "None",
                "highest_severity_count": max(severity_counts.values()) if severity_counts else 0
            },
            "type_distribution": type_distribution,
            "severity_distribution": severity_distribution,
            "top_delayed_incidents": [
                {
                    "type": inc["type"],
                    "description": inc["description"][:100],
                    "delay_minutes": round(inc["delay_minutes"], 1),
                    "severity": inc["severity_label"],
                    "location": f"{inc['from_street']} → {inc['to_street']}" if inc['from_street'] else "Unknown"
                }
                for inc in top_delayed[:5]
            ],
            "hotspots": hotspots,
            "time_analysis": time_analysis,
            "timestamp": datetime.now().isoformat()
        }
    
    def _identify_hotspots(self, incidents: List[Dict]) -> List[Dict]:
        """Identify geographic hotspots with high incident concentration."""
        # Simple grid-based clustering
        grid_size = 0.01  # ~1km grid
        grid = {}
        
        for inc in incidents:
            coords = inc["coordinates"]
            grid_key = (
                round(coords[1] / grid_size) * grid_size,  # lat
                round(coords[0] / grid_size) * grid_size   # lon
            )
            
            if grid_key not in grid:
                grid[grid_key] = []
            grid[grid_key].append(inc)
        
        # Get top 5 hotspots
        hotspots = []
        for (lat, lon), incidents_in_cell in sorted(grid.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            hotspots.append({
                "latitude": lat,
                "longitude": lon,
                "incident_count": len(incidents_in_cell),
                "types": list(set([inc["type"] for inc in incidents_in_cell])),
                "avg_severity": sum([inc["severity"] for inc in incidents_in_cell]) / len(incidents_in_cell)
            })
        
        return hotspots
    
    def _analyze_time_patterns(self, incidents: List[Dict]) -> Dict:
        """Analyze time-based patterns in incidents."""
        now = datetime.now()
        
        # Calculate incident age
        ages = []
        for inc in incidents:
            if inc["start_time"]:
                try:
                    start = datetime.fromisoformat(inc["start_time"].replace("Z", "+00:00"))
                    age_minutes = (now - start).total_seconds() / 60
                    ages.append(age_minutes)
                except:
                    continue
        
        if ages:
            return {
                "average_age_minutes": round(sum(ages) / len(ages), 1),
                "oldest_incident_minutes": round(max(ages), 1),
                "newest_incident_minutes": round(min(ages), 1)
            }
        
        return {
            "average_age_minutes": 0,
            "oldest_incident_minutes": 0,
            "newest_incident_minutes": 0
        }
    
    def _empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure."""
        return {
            "summary": {
                "total_incidents": 0,
                "total_delay_hours": 0,
                "average_delay_minutes": 0,
                "most_common_type": "None",
                "highest_severity_count": 0
            },
            "type_distribution": [],
            "severity_distribution": [],
            "top_delayed_incidents": [],
            "hotspots": [],
            "time_analysis": {
                "average_age_minutes": 0,
                "oldest_incident_minutes": 0,
                "newest_incident_minutes": 0
            },
            "timestamp": datetime.now().isoformat()
        }


# Singleton instance
_analytics_instance = None

def get_analytics_instance():
    """Get or create analytics instance."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = IncidentAnalytics()
    return _analytics_instance