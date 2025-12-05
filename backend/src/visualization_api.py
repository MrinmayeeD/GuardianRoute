"""
Visualization API endpoints for heatmap and zone analytics.
Provides REST API endpoints for traffic visualization.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import visualization engine and KNN predictor
from src.visualization_engine import VisualizationEngine
from src.predict_knn import KNNTrafficPredictor

# Initialize router
router = APIRouter(prefix="/api/viz", tags=["Visualizations"])

# Initialize visualization engine globally
viz_engine = None
knn_predictor = None


def get_viz_engine():
    """Lazy load visualization engine."""
    global viz_engine
    if viz_engine is None:
        logger.info("Initializing VisualizationEngine...")
        viz_engine = VisualizationEngine()
    return viz_engine


def get_knn_predictor():
    """Lazy load KNN predictor."""
    global knn_predictor
    if knn_predictor is None:
        logger.info("Initializing KNN Predictor...")
        knn_predictor = KNNTrafficPredictor()
    return knn_predictor


# ========================= PYDANTIC MODELS =========================

class HeatmapPoint(BaseModel):
    """Represents a single point on the heatmap."""
    lat: float
    lon: float
    severity: float
    location: str
    intensity: float


class HeatmapResponse(BaseModel):
    """Response for hourly heatmap data."""
    hour: int
    timestamp: str
    points: List[HeatmapPoint]
    count: int


class ZoneAnalytics(BaseModel):
    """Analytics data for a specific zone."""
    location: str
    coordinates: Dict[str, float]
    avg_severity: float
    avg_congestion: float
    peak_hour: int
    peak_severity: float
    quiet_hour: int
    quiet_severity: float
    morning_congestion: float
    evening_congestion: float
    best_visit_time: str
    worst_time: str
    recommendation: str


class ZoneAnalyticsResponse(BaseModel):
    """Response for all zones analytics."""
    zones: Dict[str, ZoneAnalytics]
    count: int
    generated_at: str


class PredictivePoint(BaseModel):
    """Represents a predicted point on the heatmap."""
    lat: float
    lon: float
    severity: float
    location: str
    confidence: float


class PredictiveHeatmap(BaseModel):
    """Predicted heatmap for a specific hour."""
    hour: int
    timestamp: str
    points: List[PredictivePoint]
    avg_severity: float


class PredictiveResponse(BaseModel):
    """Response for predictive heatmap."""
    predictions: Dict[int, PredictiveHeatmap]
    hours_ahead: int
    current_hour: int
    confidence: float


class SimilarLocation(BaseModel):
    """Represents a similar location."""
    location_name: str
    latitude: float
    longitude: float
    similarity_distance: float
    similarity_score: float  # Normalized similarity (0-100)


class SimilarLocationsResponse(BaseModel):
    """Response for similar locations."""
    input_location: str
    total_similar: int
    similar_locations: List[SimilarLocation]
    generated_at: str


# ========================= ENDPOINTS =========================

@router.get("/heatmap/hourly/{hour}", response_model=HeatmapResponse)
async def get_hourly_heatmap(hour: int = Path(..., ge=0, le=23)):
    """
    Get heatmap data for a specific hour.
    
    Args:
        hour: Hour of day (0-23)
        
    Returns:
        HeatmapResponse with lat/lon/severity points for visualization
        
    Example:
        GET /api/viz/heatmap/hourly/18 - Get evening traffic heatmap
    """
    try:
        engine = get_viz_engine()
        all_heatmaps = engine.get_hourly_heatmap_data()
        
        if hour not in all_heatmaps:
            raise HTTPException(status_code=404, detail=f"No data for hour {hour}")
        
        points = all_heatmaps[hour]
        
        return HeatmapResponse(
            hour=hour,
            timestamp=f"{hour:02d}:00",
            points=points,
            count=len(points)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Heatmap retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/zones/analytics", response_model=ZoneAnalyticsResponse)
async def get_zone_analytics():
    """
    Get comprehensive analytics for all zones.
    
    Returns:
        Dict of zone names -> detailed analytics with peak hours, 
        quiet hours, and recommendations
        
    Perfect for:
        - Zone comparison dashboards
        - Area recommendation cards
        - Best time to visit suggestions
    """
    try:
        engine = get_viz_engine()
        analytics = engine.get_zone_analytics()
        
        zones_data = {}
        for zone_name, zone_info in analytics.items():
            zones_data[zone_name] = ZoneAnalytics(**zone_info)
        
        return ZoneAnalyticsResponse(
            zones=zones_data,
            count=len(zones_data),
            generated_at=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Zone analytics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/zones/{zone_name}")
async def get_zone_detail(zone_name: str = Path(...)):
    """
    Get detailed analytics for a specific zone.
    
    Args:
        zone_name: Name of the zone/location
        
    Returns:
        Detailed zone information with all metrics
        
    Example:
        GET /api/viz/zones/Koregaon%20Park
    """
    try:
        engine = get_viz_engine()
        analytics = engine.get_zone_analytics()
        
        if zone_name not in analytics:
            raise HTTPException(status_code=404, detail=f"Zone not found: {zone_name}")
        
        return analytics[zone_name]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Zone detail retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/heatmap", response_model=PredictiveResponse)
async def get_predictive_heatmap(hours_ahead: int = Query(3, ge=1, le=24)):
    """
    Get predicted heatmap for future hours.
    
    Args:
        hours_ahead: Number of hours to predict ahead (1-24, default 3)
        
    Returns:
        PredictiveResponse with future hour predictions
        
    Use for:
        - "Traffic in next 2 hours" feature
        - Route planning with future conditions
        - Animated forecast visualization
        
    Example:
        GET /api/viz/predict/heatmap?hours_ahead=2
    """
    try:
        engine = get_viz_engine()
        predictions = engine.get_predictive_heatmap(hours_ahead)
        
        predictive_data = {}
        for hour, pred_info in predictions.items():
            predictive_data[hour] = PredictiveHeatmap(**pred_info)
        
        return PredictiveResponse(
            predictions=predictive_data,
            hours_ahead=hours_ahead,
            current_hour=datetime.now().hour,
            confidence=0.85
        )
    except Exception as e:
        logger.error(f"Predictive heatmap retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar-locations/{location_name}", response_model=SimilarLocationsResponse)
async def get_similar_locations(location_name: str = Path(...), top_n: int = Query(3, ge=1, le=5)):
    """
    Get top similar locations based on POI features for a given location.
    
    Args:
        location_name: Name of the location/city to find similar locations for
        top_n: Number of similar locations to return (1-5, default 3)
        
    Returns:
        SimilarLocationsResponse with top similar locations and their data
        
    Use for:
        - Visualizing similar traffic patterns
        - Finding comparable locations
        - Cross-location traffic analysis
        
    Example:
        GET /api/viz/similar-locations/Pune?top_n=3
        
    Response includes:
        - Input location name
        - List of similar locations with coordinates
        - Similarity distance scores (lower = more similar)
        - Normalized similarity scores (0-100, higher = more similar)
    """
    try:
        knn = get_knn_predictor()
        viz_engine = get_viz_engine()
        
        # Get all available locations from traffic data
        traffic_df = viz_engine.traffic_df
        all_locations = traffic_df['location_name'].unique().tolist()
        
        # Find exact or partial match for the location
        location_match = None
        for loc in all_locations:
            if loc.lower() == location_name.lower():
                location_match = loc
                break
        
        # If exact match not found, try partial match
        if location_match is None:
            for loc in all_locations:
                if location_name.lower() in loc.lower():
                    location_match = loc
                    break
        
        if location_match is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Location not found: {location_name}. Available locations: {all_locations[:10]}"
            )
        
        # Get POI features for the input location from traffic data
        location_data = traffic_df[traffic_df['location_name'] == location_match]
        
        if len(location_data) == 0:
            raise HTTPException(status_code=404, detail=f"No traffic data for location: {location_match}")
        
        # Extract POI features as dictionary
        poi_features = knn.poi_features
        first_row = location_data.iloc[0]
        
        # Create POI dictionary from the location data
        poi_dict = {}
        for poi_feat in poi_features:
            if poi_feat in first_row.index:
                poi_dict[poi_feat] = float(first_row[poi_feat])
            else:
                poi_dict[poi_feat] = 0.0
        
        # Find similar locations
        similar_locs = knn.find_similar_locations(poi_dict, k=top_n + 1)  # +1 because first is itself
        
        # Filter out the input location itself and prepare response
        similar_locations = []
        max_distance = 1.0  # For normalization
        
        for idx, row in similar_locs.iterrows():
            loc_name = row['location_name']
            
            # Skip the input location itself
            if loc_name == location_match:
                continue
            
            distance = float(row['similarity_distance'])
            
            # Normalize distance to similarity score (0-100)
            # Lower distance = higher similarity
            similarity_score = max(0, 100 * (1 - distance / max_distance))
            
            similar_locations.append(
                SimilarLocation(
                    location_name=loc_name,
                    latitude=float(row['latitude']),
                    longitude=float(row['longitude']),
                    similarity_distance=distance,
                    similarity_score=similarity_score
                )
            )
            
            if len(similar_locations) >= top_n:
                break
        
        logger.info(f"Found {len(similar_locations)} similar locations for {location_match}")
        
        return SimilarLocationsResponse(
            input_location=location_match,
            total_similar=len(similar_locations),
            similar_locations=similar_locations,
            generated_at=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similar locations retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
