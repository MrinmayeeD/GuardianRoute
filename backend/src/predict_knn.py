"""
KNN Traffic Predictor - Uses pre-trained KNN models
Based on POI similarity and historical traffic patterns
"""

import requests
import pandas as pd
import numpy as np
import urllib.parse
import joblib
import os
import logging
from pathlib import Path
from sklearn.neighbors import NearestNeighbors

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.insight_generate import InsightEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TomTom API Configuration
API_KEY = os.getenv('TOMTOM_API_KEY', 'd5TWC3g2TRMlQr6VQvk0h5pfdQGrqCtA')
GEOCODE_BASE_URL = "https://api.tomtom.com/search/2/geocode"
PLACES_API_URL = "https://api.tomtom.com/search/2/nearbySearch/.json"

# Load the traffic data with categories
DATA_PATH = Path(__file__).parent.parent / 'data' / 'traffic_with_categories.csv'


class KNNTrafficPredictor:
    """KNN-based traffic predictor using POI similarity."""
    
    def __init__(self, api_key=None, model_type='new_severity_logical'):
        """
        Initialize KNN predictor
        
        Args:
            api_key: TomTom API key
            model_type: 'new_severity' or 'new_severity_logical'
        """
        self.api_key = api_key or API_KEY
        self.model_type = model_type
        self.geocode_base_url = GEOCODE_BASE_URL
        self.places_api_url = PLACES_API_URL
        
        # Initialize insight engine
        self.insight_engine = InsightEngine()
        
        # Load traffic data for similarity search
        logger.info(f"Loading traffic data from: {DATA_PATH}")
        self.traffic_df = pd.read_csv(DATA_PATH)
        
        # Get POI columns dynamically (from CAFE_PUB to raw_classifications)
        all_cols = self.traffic_df.columns.tolist()
        
        try:
            cafe_idx = all_cols.index('CAFE_PUB')
            raw_idx = all_cols.index('raw_classifications')
            
            self.poi_features = all_cols[cafe_idx:raw_idx]
            logger.info(f"✓ Found {len(self.poi_features)} POI features")
            
        except ValueError as e:
            logger.error(f"Could not find POI columns: {e}")
            raise
        
        # Build KNN models
        self._build_knn_models()
        
        logger.info(f"✅ KNN Predictor initialized ({model_type})")
        logger.info(f"   POI features: {len(self.poi_features)}")
        logger.info(f"   Training locations: {len(self.traffic_df['location_name'].unique())}")
    
    def _build_knn_models(self):
        """Build KNN models from traffic data."""
        # Prepare POI features from traffic data
        # Group by location and take first values for POI features
        agg_dict = {poi: 'first' for poi in self.poi_features}
        agg_dict.update({
            'latitude': 'first',
            'longitude': 'first'
        })
        
        unique_locations = self.traffic_df.groupby('location_name').agg(agg_dict).reset_index()
        
        X_similarity = unique_locations[self.poi_features].fillna(0).values
        
        # Build similarity KNN (for finding similar locations)
        from sklearn.preprocessing import StandardScaler
        self.scaler_similarity = StandardScaler()
        X_scaled = self.scaler_similarity.fit_transform(X_similarity)
        
        self.knn_similarity = NearestNeighbors(n_neighbors=5, metric='cosine')
        self.knn_similarity.fit(X_scaled)
        
        # Store location reference data
        self.location_reference = unique_locations
        
        logger.info("✓ KNN similarity model built successfully")
        logger.info(f"✓ Reference database: {len(unique_locations)} unique locations")
    
    def get_coordinates_from_location(self, location_name):
        """Get latitude and longitude from location name."""
        encoded_location = urllib.parse.quote(location_name)
        url = f"{self.geocode_base_url}/{encoded_location}.json"
        params = {'key': self.api_key, 'limit': 1}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results') and len(data['results']) > 0:
                position = data['results'][0]['position']
                return position['lat'], position['lon']
            else:
                logger.warning(f"No coordinates found for {location_name}")
                return None, None
        except Exception as e:
            logger.error(f"Error geocoding {location_name}: {str(e)}")
            return None, None
    
    def get_nearby_places(self, lat, lon, radius=1000, limit=100):
        """Fetch nearby places from TomTom Places API."""
        params = {
            'lat': lat,
            'lon': lon,
            'key': self.api_key,
            'radius': radius,
            'limit': limit
        }
        
        try:
            response = requests.get(self.places_api_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API Error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}")
            return None
    
    def extract_poi_categories(self, api_response):
        """Extract and count POI categories from API response."""
        category_counts = {cat: 0 for cat in self.poi_features}
        
        if not api_response or 'results' not in api_response:
            return category_counts
        
        for result in api_response['results']:
            if 'poi' in result and 'classifications' in result['poi']:
                for classification in result['poi']['classifications']:
                    code = classification.get('code', '').upper().strip()
                    
                    if code and code in category_counts:
                        category_counts[code] += 1
        
        return category_counts
    
    def find_similar_locations(self, poi_counts, k=5):
        """Find k most similar locations based on POI features."""
        # Create feature vector
        feature_vector = np.array([[poi_counts.get(feat, 0) for feat in self.poi_features]])
        
        # Scale and find neighbors
        X_scaled = self.scaler_similarity.transform(feature_vector)
        distances, indices = self.knn_similarity.kneighbors(X_scaled, n_neighbors=k)
        
        # Create results DataFrame
        similar_locations = self.location_reference.iloc[indices[0]].copy()
        similar_locations['similarity_distance'] = distances[0]
        
        return similar_locations
    
    def predict_severity(self, poi_counts, similar_locations):
        """Predict traffic severity based on similar locations."""
        # Get full traffic data for similar locations
        similar_city_names = similar_locations['location_name'].tolist()
        similar_traffic = self.traffic_df[
            self.traffic_df['location_name'].isin(similar_city_names)
        ].copy()
        
        # Map severity to numeric values
        severity_map = {'LOW': 0, 'MODERATE': 1, 'HIGH': 2, 'VERY_HIGH': 3}
        similar_traffic['severity_numeric'] = similar_traffic[self.model_type].map(severity_map)
        
        # Calculate weighted average severity for each location
        location_severities = similar_traffic.groupby('location_name')['severity_numeric'].mean()
        
        # Use distance-based weights
        weights = 1 / (similar_locations['similarity_distance'] + 1e-6)
        weights = weights / weights.sum()
        
        # Calculate weighted severity
        severity_score = 0
        for loc, weight in zip(similar_locations['location_name'], weights):
            if loc in location_severities:
                severity_score += location_severities[loc] * weight
        
        # Map to category
        severity_categories = ['LOW', 'MODERATE', 'HIGH', 'VERY_HIGH']
        severity_idx = int(round(severity_score))
        severity_category = severity_categories[min(severity_idx, len(severity_categories)-1)]
        
        # ✅ Calculate confidence based on similarity distances
        # Lower average distance = higher confidence
        avg_distance = similar_locations['similarity_distance'].mean()
        confidence = max(0.5, min(1.0, 1.0 - avg_distance))  # Scale between 0.5 and 1.0
        
        # Generate probability distribution
        probabilities = {}
        for i, cat in enumerate(severity_categories):
            prob = max(0, 1 - abs(severity_score - i) / 2)
            probabilities[cat] = prob
        
        # Normalize probabilities
        total = sum(probabilities.values())
        if total > 0:
            probabilities = {k: v/total for k, v in probabilities.items()}
        
        # ✅ Return confidence as well
        return severity_category, severity_score, probabilities, confidence
    
    def predict(self, location_name, radius=1000, k_similar=5):
        """
        Complete prediction pipeline for a location.
        
        Args:
            location_name: Name of the location/city
            radius: Search radius in meters for POI search
            k_similar: Number of similar locations to find
        
        Returns:
            dict: Prediction results with insights
        """
        logger.info("="*80)
        logger.info(f"🔍 KNN TRAFFIC PREDICTION FOR: {location_name}")
        logger.info(f"   Model Type: {self.model_type}")
        logger.info("="*80)
        
        # Step 1: Get coordinates
        logger.info(f"\n📍 Step 1: Geocoding location...")
        lat, lon = self.get_coordinates_from_location(location_name)
        
        if lat is None or lon is None:
            return {
                'success': False,
                'error': f'Location not found: {location_name}'
            }
        
        logger.info(f"   ✓ Coordinates: ({lat:.6f}, {lon:.6f})")
        
        # Step 2: Get nearby POIs
        logger.info(f"\n🏢 Step 2: Fetching nearby POIs (radius: {radius}m)...")
        api_response = self.get_nearby_places(lat, lon, radius=radius)
        
        if not api_response:
            return {
                'success': False,
                'error': 'Failed to fetch POI data'
            }
        
        total_pois = api_response.get('summary', {}).get('totalResults', 0)
        fetched_pois = api_response.get('summary', {}).get('numResults', 0)
        logger.info(f"   ✓ Found {total_pois} POIs (fetched {fetched_pois})")
        
        # Step 3: Extract POI categories
        logger.info(f"\n📊 Step 3: Extracting POI categories...")
        poi_counts = self.extract_poi_categories(api_response)
        
        non_zero_pois = {k: v for k, v in poi_counts.items() if v > 0}
        logger.info(f"   ✓ Found {len(non_zero_pois)} different POI categories")
        
        # Step 4: Find similar locations
        logger.info(f"\n🔍 Step 4: Finding {k_similar} most similar locations...")
        similar_locations = self.find_similar_locations(poi_counts, k=k_similar)
        
        logger.info(f"   ✓ Similar locations found!")
        logger.info(f"\n   Top 3 Similar Locations:")
        for i, row in similar_locations.head(3).iterrows():
            logger.info(f"      {i+1}. {row['location_name']}")
        
        # Step 5: Predict severity
        logger.info(f"\n🔮 Step 5: Predicting traffic severity...")
        severity_category, severity_score, probabilities, confidence = self.predict_severity(poi_counts, similar_locations)
        
        logger.info(f"   ✓ Predicted Severity: {severity_category} (score: {severity_score:.2f})")
        logger.info(f"   ✓ Confidence: {confidence:.2%}")
        
        # Step 6: Get hourly traffic flow from most similar city
        most_similar_city = similar_locations.iloc[0]['location_name']
        city_traffic = self.traffic_df[
            self.traffic_df['location_name'] == most_similar_city
        ].copy()
        
        # Filter for hours 6-21
        city_traffic = city_traffic[
            (city_traffic['hour_label'] >= 6) & 
            (city_traffic['hour_label'] <= 21)
        ].sort_values('hour_label')
        
        # Add numeric severity for calculations
        severity_map = {'LOW': 0, 'MODERATE': 1, 'HIGH': 2, 'VERY_HIGH': 3}
        city_traffic['severity_numeric'] = city_traffic[self.model_type].map(severity_map)
        
        # Build hourly forecast
        hourly_forecast = []
        for _, row in city_traffic.iterrows():
            hourly_forecast.append({
                'hour': int(row['hour_label']),
                'severity': row[self.model_type],
                'current_speed': float(row['current_speed']),
                'free_flow_speed': float(row['free_flow_speed']),
                'congestion_ratio': float(row['congestion_ratio']),
                'confidence': float(row.get('confidence', 0.8))
            })
        
        # Step 7: Generate insights
        insights = self.insight_engine.generate_insights(
            location_name=location_name,
            poi_counts=poi_counts,
            city_traffic_df=city_traffic
        )
        
        # Build result
        result = {
            'success': True,
            'location': location_name,
            'coordinates': {'latitude': lat, 'longitude': lon},
            'prediction': {
                'severity': severity_category,
                'severity_score': float(severity_score),
                'confidence': float(confidence),  # ✅ ADD THIS LINE
                'model_type': self.model_type,
                'probabilities': {str(k): float(v) for k, v in probabilities.items()}
            },
            'poi_summary': {
                'total_pois': total_pois,
                'top_categories': sorted(
                    [(k, v) for k, v in non_zero_pois.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            },
            'similar_locations': similar_locations['location_name'].tolist(),
            'most_similar_city': most_similar_city,
            'hourly_forecast': hourly_forecast,
            'insights': insights
        }
        
        return result
    
    def predict_location(self, location_name):
        """
        Simplified prediction method for API compatibility.
        
        Args:
            location_name: Name of the location
        
        Returns:
            dict: Prediction results
        """
        return self.predict(location_name)


def predict_traffic_flow(input_data):
    """
    Predict traffic flow for given input data.
    
    Args:
        input_data: Dict with 'location' key
        
    Returns:
        dict: Prediction results
    """
    predictor = KNNTrafficPredictor(model_type='new_severity_logical')
    location = input_data.get('location', '')
    
    if not location:
        return {'success': False, 'error': 'Location name is required'}
    
    return predictor.predict(location)


