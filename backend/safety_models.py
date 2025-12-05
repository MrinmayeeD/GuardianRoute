from pydantic import BaseModel, field_validator
from typing import List, Optional


class Coordinates(BaseModel):
    """Model for latitude and longitude"""
    latitude: float
    longitude: float


class RouteRequest(BaseModel):
    """Request model for route calculation - supports both nested and flat formats"""
    source: Optional[Coordinates] = None
    destination: Optional[Coordinates] = None
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    end_latitude: Optional[float] = None
    end_longitude: Optional[float] = None
    travel_mode: Optional[str] = "DRIVING"  # DRIVING, WALKING, TRANSIT
    
    @field_validator('source', 'destination', mode='before')
    @classmethod
    def validate_coordinates(cls, v, info):
        """Convert flat format to nested Coordinates object"""
        if v is None:
            # Check if we're validating source or destination
            field_name = info.field_name
            if field_name == 'source':
                if 'start_latitude' in info.data and 'start_longitude' in info.data:
                    return Coordinates(
                        latitude=info.data['start_latitude'],
                        longitude=info.data['start_longitude']
                    )
            elif field_name == 'destination':
                if 'end_latitude' in info.data and 'end_longitude' in info.data:
                    return Coordinates(
                        latitude=info.data['end_latitude'],
                        longitude=info.data['end_longitude']
                    )
            raise ValueError(f"{field_name} coordinates are required")
        return v


class DangerZone(BaseModel):
    """Model for danger zone data"""
    latitude: float
    longitude: float
    magnitude: int  # 0-4 scale
    type: str
    name: Optional[str] = None


class SafeZone(BaseModel):
    """Model for safe zone data"""
    latitude: float
    longitude: float
    type: str
    name: Optional[str] = None


class RoutePoint(BaseModel):
    """Model for individual route point"""
    latitude: float
    longitude: float


class Route(BaseModel):
    """Model for a single route with safety info"""
    route_id: int
    route_name: str  # "Safest", "Moderate", "Dangerous"
    points: List[RoutePoint]
    distance: float  # in kilometers
    duration: float  # in minutes
    danger_index: float
    danger_level: str  # "green", "yellow", "red"
    danger_points_count: int
    color_code: str  # hex color


class RouteResponse(BaseModel):
    """Response model for route calculation"""
    source: Coordinates
    destination: Coordinates
    routes: List[Route]
    travel_mode: str
    timestamp: str


class HealthCheck(BaseModel):
    """Model for health check response"""
    status: str
    message: str
