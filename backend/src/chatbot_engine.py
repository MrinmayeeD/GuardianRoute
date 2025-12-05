"""
Conversational chatbot engine - KNN predictions + real-time APIs + LLM.
"""

import os
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from groq import Groq
from src.predict_knn import KNNTrafficPredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatbotEngine:
    """KNN predictor + Real-time APIs + Groq LLM for conversational responses."""
    
    def __init__(self):
        """Initialize chatbot with KNN predictor and APIs."""
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"
        
        # Initialize KNN predictor
        logger.info("🔵 Loading KNN predictor...")
        self.predictor = KNNTrafficPredictor(model_type='new_severity_logical')
        
        # API keys for real-time data
        self.tomtom_key = os.getenv("TOMTOM_API_KEY")
        self.owm_key = os.getenv("OWM_API_KEY")
        
        logger.info("✅ ChatbotEngine initialized with KNN + Real-time APIs")
    
    def fetch_weather(self, lat: float, lon: float) -> Dict:
        """Fetch weather data from OpenWeatherMap."""
        if not self.owm_key:
            return {}
        
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.owm_key,
                "units": "metric"
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            return {
                "condition": data.get("weather", [{}])[0].get("main", "Unknown"),
                "description": data.get("weather", [{}])[0].get("description", ""),
                "temp": data.get("main", {}).get("temp"),
                "humidity": data.get("main", {}).get("humidity"),
                "pressure": data.get("main", {}).get("pressure")
            }
        except Exception as e:
            logger.warning(f"Weather API error: {e}")
            return {}
    
    def fetch_traffic_flow(self, lat: float, lon: float) -> Dict:
        """Fetch traffic flow data from TomTom."""
        if not self.tomtom_key:
            return {}
        
        try:
            url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
            params = {
                "point": f"{lat},{lon}",
                "key": self.tomtom_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            segment = data.get("flowSegmentData", {})
            return {
                "current_speed": segment.get("currentSpeed", 0),
                "free_flow_speed": segment.get("freeFlowSpeed", 0),
                "current_travel_time": segment.get("currentTravelTime", 0),
                "free_flow_travel_time": segment.get("freeFlowTravelTime", 0),
                "confidence": segment.get("confidence", 0)
            }
        except Exception as e:
            logger.warning(f"Traffic flow API error: {e}")
            return {}
    
    def fetch_incidents(self, lat: float, lon: float, delta: float = 0.02) -> list:
        """Fetch incidents from TomTom."""
        if not self.tomtom_key:
            return []
        
        try:
            url = "https://api.tomtom.com/traffic/services/5/incidentDetails"
            bbox = f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}"
            params = {
                "bbox": bbox,
                "key": self.tomtom_key,
                "fields": "{incidents{type,geometry{type,coordinates},properties{id,iconCategory,magnitudeOfDelay,delay,events{description},from,to}}}"
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            incidents = data.get("incidents", [])
            
            # Parse incidents
            parsed = []
            for inc in incidents:
                props = inc.get("properties", {})
                parsed.append({
                    "type": self._get_incident_type(props.get("iconCategory", 0)),
                    "severity": props.get("magnitudeOfDelay", 0),
                    "severity_label": self._get_severity_label(props.get("magnitudeOfDelay", 0)),
                    "delay": props.get("delay", 0),
                    "from": props.get("from", ""),
                    "to": props.get("to", ""),
                    "description": props.get("events", [{}])[0].get("description", "")
                })
            
            return parsed
            
        except Exception as e:
            logger.warning(f"Incidents API error: {e}")
            return []
    
    def _get_incident_type(self, code: int) -> str:
        """Map incident code to type."""
        types = {
            0: "Unknown", 1: "Accident", 2: "Fog", 3: "Dangerous Conditions",
            4: "Rain", 5: "Ice", 6: "Jam", 7: "Lane Closed",
            8: "Road Closed", 9: "Road Works", 10: "Wind",
            11: "Flooding", 14: "Broken Down Vehicle"
        }
        return types.get(code, "Unknown")
    
    def _get_severity_label(self, severity: int) -> str:
        """Map severity code to label."""
        labels = {
            0: "Unknown", 1: "Minor", 2: "Moderate",
            3: "Major", 4: "Severe"
        }
        return labels.get(severity, "Unknown")