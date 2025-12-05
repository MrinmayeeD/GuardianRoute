"""
FastAPI application for traffic prediction API (Hybrid version).
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import logging
from pathlib import Path
import os
import sys
from contextlib import asynccontextmanager
import math
from datetime import datetime, timedelta, timezone

# ✅ Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# ✅ CHANGED: Import Hybrid predictor
from src.hybrid_predictor import HybridTrafficPredictor
from src.chatbot_engine import ChatbotEngine
from src.reminder_scheduler import scheduler, Reminder, ReminderType, ReminderStatus
from src.whatsapp_service import whatsapp_service
from src.visualization_api import router as viz_router

# ✅ Import safe route models and calculator
from safety_models import (
    RouteRequest, RouteResponse, Route, RoutePoint, HealthCheck,
    Coordinates
)
from safety_calculator import SafetyCalculator, RouteOptimizer
from src.incident_analytics import IncidentAnalytics, get_analytics_instance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
predictor = None
chatbot_engine = None
safety_calculator = None
incident_analytics = None


def load_data():
    """Initialize hybrid predictor."""
    global predictor
    
    if predictor is None:
        logger.info("🔄 Initializing Hybrid predictor (KNN + RF)...")
        predictor = HybridTrafficPredictor(knn_weight=0.5, rf_weight=0.5)
        logger.info("✅ Hybrid predictor ready")


def load_chatbot():
    """Initialize chatbot engine."""
    global chatbot_engine
    if chatbot_engine is None:
        logger.info("🤖 Initializing chatbot engine...")
        chatbot_engine = ChatbotEngine()
        logger.info("✅ Chatbot ready")


def load_safety_calculator():
    """Initialize safety calculator for safe routes."""
    global safety_calculator
    if safety_calculator is None:
        logger.info("🛡️ Initializing safety calculator...")
        safety_calculator = SafetyCalculator("safety_data.json")
        logger.info(f"✅ Safety calculator loaded with {len(safety_calculator.danger_zones)} danger zones")


def load_incident_analytics():
    """Initialize incident analytics."""
    global incident_analytics
    if incident_analytics is None:
        logger.info("🚨 Initializing incident analytics...")
        incident_analytics = get_analytics_instance()
        logger.info("✅ Incident analytics loaded")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    try:
        load_data()
        load_incident_analytics()
        logger.info("API ready to serve predictions")
        await scheduler.start()
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")
    await scheduler.stop()


app = FastAPI(
    title="Traffic Severity Prediction API (Hybrid)",
    description="Predict hourly traffic severity using Hybrid model and generate urban insights",
    version="2.0.0",
    lifespan=lifespan
)

# ✅ Add CORS support for frontend
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# ✅ Include visualization API router
app.include_router(viz_router)




class PredictionRequest(BaseModel):
    location: str


class PredictionResponse(BaseModel):
    hourly_forecast: list
    insights: dict


class ChatRequest(BaseModel):
    question: str
    location: Optional[str] = None  # ✅ CHANGED: Now optional
    mode: Optional[str] = None
    time: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    confidence: float
    sources: list
    merged_insights: dict
    prediction: dict  # ✅ CHANGED: renamed from rf_prediction


class ReminderRequest(BaseModel):
    message: str
    recipient: str
    reminder_type: str
    scheduled_time: str


class ReminderResponse(BaseModel):
    reminder_id: str
    message: str
    recipient: str
    reminder_type: str
    scheduled_time: str
    status: str
    created_at: str


class SOSRequest(BaseModel):
    """SOS message request."""
    origin: str
    destination: str
    phone_numbers: List[str]
    current_location: Optional[dict] = None


class SOSResponse(BaseModel):
    """SOS message response."""
    success: bool
    message: str
    sent_to: List[str]
    failed: List[dict] = []


@app.post("/predict", response_model=PredictionResponse)
async def predict_traffic(request: PredictionRequest):
    """
    Predict hourly traffic severity using Hybrid model.
    
    Args:
        request: PredictionRequest with location name
        
    Returns:
        PredictionResponse with hourly forecast and insights
    """
    try:
        load_data()
        
        location_name = request.location
        
        # ✅ CHANGED: Use Hybrid predictor
        result = predictor.predict_location(location_name)
        
        logger.info(f"Prediction completed for: {location_name}")
        
        return PredictionResponse(
            hourly_forecast=result['hourly_forecast'],
            insights=result['insights']
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ============================================================================

def _assess_weather_impact(weather: dict) -> str:
    """Assess weather impact on traffic."""
    condition = weather.get('condition', '').lower()
    
    if 'rain' in condition or 'storm' in condition:
        return "HIGH - Rain increases congestion by 20-30%"
    elif 'fog' in condition or 'mist' in condition:
        return "MODERATE - Reduced visibility affects speed"
    elif 'clear' in condition or 'sunny' in condition:
        return "LOW - Clear weather, normal traffic flow"
    else:
        return "UNKNOWN - Weather impact unclear"


def _calculate_congestion(traffic_flow: dict) -> str:
    """Calculate congestion percentage from traffic flow."""
    current = traffic_flow.get('current_speed', 0)
    free_flow = traffic_flow.get('free_flow_speed', 0)
    
    if free_flow == 0:
        return "Unknown"
    
    congestion_ratio = 1 - (current / free_flow)
    congestion_pct = max(0, min(100, congestion_ratio * 100))
    
    return f"{congestion_pct:.0f}%"


def _calculate_delay_factor(traffic_flow: dict) -> float:
    """Calculate delay factor from traffic flow."""
    current = traffic_flow.get('current_speed', 0)
    free_flow = traffic_flow.get('free_flow_speed', 0)
    
    if current == 0 or free_flow == 0:
        return 1.0
    
    return free_flow / current


def _summarize_incident_severity(incidents: list) -> str:
    """Summarize incident severity distribution."""
    if not incidents:
        return "No active incidents"
    
    severity_counts = {}
    for inc in incidents:
        severity = inc.get('severity_label', 'Unknown')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    summary_parts = [f"{count} {severity}" for severity, count in severity_counts.items()]
    return ", ".join(summary_parts)


def _generate_llm_response(knowledge_base: dict) -> dict:
    """Generate natural language response using Groq LLM."""
    
    # Build concise prompt for LLM
    model_data = knowledge_base['model_predictions']
    zone = knowledge_base['zone_info']
    weather = knowledge_base['weather']
    traffic = knowledge_base['traffic_flow']
    incidents = knowledge_base['incidents']
    user = knowledge_base['user_query']
    
    prompt = f"""You are a traffic assistant AI. Answer the user's question based on this data:

        USER QUESTION: "{user['question']}"

        LOCATION: {model_data['location']}
        TRAVEL MODE: {user['mode']}
        CURRENT TIME: {user['time']}

        KNN MODEL PREDICTION:
        • Severity: {model_data['severity']}
        • Confidence: {model_data['confidence']:.0%}
        • Area Type: {zone.get('classification', {}).get('primary', 'Mixed')} - {zone.get('classification', {}).get('vibe', 'Urban')}

        CURRENT CONDITIONS:
        • Weather: {weather['condition']} ({weather['temperature']}°C) - Impact: {weather['impact']}
        • Traffic Speed: {traffic['current_speed']} km/h (normal: {traffic['free_flow_speed']} km/h)
        • Congestion: {traffic['congestion']}
        • Active Incidents: {incidents['count']} ({incidents['severity_summary']})

        AREA CHARACTERISTICS:
        • Walkability: {zone.get('scores', {}).get('walkability_score', 5):.1f}/10
        • Parking Ease: {zone.get('scores', {}).get('parking_ease_score', 5):.1f}/10
        • Safety: {zone.get('scores', {}).get('safety_score', 5):.1f}/10
        • Best For: {', '.join(zone.get('lifestyle', {}).get('best_for', ['General travel'])[:3])}

        TASK: Answer naturally in 2-3 sentences. Be helpful and actionable. Don't mention "models" or technical terms.

        Your response:"""

    try:
        from groq import Groq
        
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        
        answer = completion.choices[0].message.content.strip()
        
        return {
            "answer": answer,
            "confidence": model_data['confidence']
        }
        
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        
        # Fallback response
        severity = model_data['severity']
        location = model_data.get('location', 'the area')
        
        if severity in ['HIGH', 'VERY_HIGH']:
            answer = f"Traffic is currently heavy in {location} with {traffic['congestion']} congestion. Consider alternate routes or waiting for traffic to clear."
        elif severity == 'MODERATE':
            answer = f"Traffic is moderate in {location}. You'll experience some delays but it's manageable. Current speed is {traffic['current_speed']} km/h."
        else:
            answer = f"Traffic is light in {location}! Great time to travel with minimal congestion."
        
        return {
            "answer": answer,
            "confidence": model_data.get('confidence', 0.7)
        }


# ============================================================================
# API ROUTES
# ============================================================================

@app.post("/chat", response_model=ChatResponse)
async def chat_with_predictions(request: ChatRequest):
    """
    🤖 Conversational AI endpoint with KNN predictions + real-time data.
    
    Architecture:
    1. KNN Model → Traffic predictions from POI similarity
    2. Real-time APIs → Weather, Traffic Flow, Incidents
    3. LLM (Groq) → Natural language response generation
    
    Example requests:
    {
      "question": "Is it safe to drive to Koregaon Park right now?",
      "location": "Koregaon Park, Pune"
    }
    """
    try:
        load_chatbot()
        
        location_name = request.location
        mode = request.mode or "drive"
        
        if not location_name:
            raise HTTPException(400, "Location is required. Please specify where you want to travel.")
        
        # ✅ Step 1: Get KNN predictions ONLY (no hybrid)
        logger.info(f"🔵 [KNN] Getting predictions for: {location_name}")
        
        # Use KNN predictor directly from chatbot engine
        knn_result = chatbot_engine.predictor.predict(location_name)
        
        if not knn_result.get('success', False):
            raise HTTPException(400, f"Failed to get predictions for '{location_name}'")
        
        # Extract coordinates
        lat = knn_result['coordinates']['latitude']
        lon = knn_result['coordinates']['longitude']
        
        # ✅ Step 2: Fetch real-time data from external APIs
        logger.info(f"🌐 Fetching real-time data...")
        
        # Weather data
        weather = chatbot_engine.fetch_weather(lat, lon)
        
        # Traffic flow data
        traffic_flow = chatbot_engine.fetch_traffic_flow(lat, lon)
        
        # Incident data
        incidents = chatbot_engine.fetch_incidents(lat, lon)
        
        # ✅ Step 3: Build Knowledge Base for LLM
        logger.info(f"📚 Building knowledge base...")
        
        # Safe extraction with defaults
        prediction_data = knn_result.get('prediction', {})
        confidence = prediction_data.get('confidence', 0.7)  # ✅ Default to 0.7 if missing
        
        knowledge_base = {
            # KNN Model Predictions
            "model_predictions": {
                "location": knn_result.get('location', location_name),
                "coordinates": knn_result.get('coordinates', {'latitude': lat, 'longitude': lon}),
                "severity": prediction_data.get('severity', 'MODERATE'),
                "confidence": confidence,  # ✅ Use safe variable
                "probabilities": prediction_data.get('probabilities', {}),
                "hourly_forecast": knn_result.get('hourly_forecast', []),
                "similar_locations": knn_result.get('similar_locations', [])[:3]
            },
            
            # POI & Zone Information
            "zone_info": {
                "classification": knn_result.get('insights', {}).get('zone_classification', {}),
                "scores": knn_result.get('insights', {}).get('scores', {}),
                "lifestyle": knn_result.get('insights', {}).get('lifestyle_insights', {}),
                "poi_summary": knn_result.get('poi_summary', {})
            },
            
            # Real-time Weather
            "weather": {
                "condition": weather.get('condition', 'Unknown'),
                "temperature": weather.get('temp', 'N/A'),
                "humidity": weather.get('humidity', 'N/A'),
                "description": weather.get('description', ''),
                "impact": _assess_weather_impact(weather)  # ✅ Remove self.
            },
            
            # Real-time Traffic Flow
            "traffic_flow": {
                "current_speed": traffic_flow.get('current_speed', 0),
                "free_flow_speed": traffic_flow.get('free_flow_speed', 0),
                "congestion": _calculate_congestion(traffic_flow),  # ✅ Remove self.
                "delay_factor": _calculate_delay_factor(traffic_flow)  # ✅ Remove self.
            },
            
            # Real-time Incidents
            "incidents": {
                "count": len(incidents),
                "active": incidents[:5],
                "severity_summary": _summarize_incident_severity(incidents),  # ✅ Remove self.
                "types": list(set([inc.get('type', 'Unknown') for inc in incidents]))
            },
            
            # User Context
            "user_query": {
                "question": request.question,
                "mode": mode,
                "time": request.time or datetime.now().strftime("%H:%M")
            }
        }
        
        # ✅ Step 4: Generate LLM response using knowledge base
        logger.info(f"🤖 Generating conversational response with LLM...")
        
        llm_response = _generate_llm_response(knowledge_base)  # ✅ Remove self.

        # ✅ Step 5: Build response
        return ChatResponse(
            answer=llm_response['answer'],
            confidence=confidence,  # ✅ Use safe variable
            sources=[
                "KNN Model (POI Similarity)",
                "OpenWeatherMap API",
                "TomTom Traffic Flow API",
                "TomTom Incidents API"
            ],
            merged_insights=knowledge_base,
            prediction=knn_result
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(400, f"Invalid request: {str(e)}")
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(500, f"Internal error: {str(e)}")


# Helper methods for chat endpoint
def _assess_weather_impact(weather: dict) -> str:
    """Assess weather impact on traffic."""
    condition = weather.get('condition', '').lower()
    
    if 'rain' in condition or 'storm' in condition:
        return "HIGH - Rain increases congestion by 20-30%"
    elif 'fog' in condition or 'mist' in condition:
        return "MODERATE - Reduced visibility affects speed"
    elif 'clear' in condition or 'sunny' in condition:
        return "LOW - Clear weather, normal traffic flow"
    else:
        return "UNKNOWN - Weather impact unclear"


def _calculate_congestion(traffic_flow: dict) -> str:
    """Calculate congestion percentage from traffic flow."""
    current = traffic_flow.get('current_speed', 0)
    free_flow = traffic_flow.get('free_flow_speed', 0)
    
    if free_flow == 0:
        return "Unknown"
    
    congestion_ratio = 1 - (current / free_flow)
    congestion_pct = max(0, min(100, congestion_ratio * 100))
    
    return f"{congestion_pct:.0f}%"


def _calculate_delay_factor(traffic_flow: dict) -> float:
    """Calculate delay factor from traffic flow."""
    current = traffic_flow.get('current_speed', 0)
    free_flow = traffic_flow.get('free_flow_speed', 0)
    
    if current == 0 or free_flow == 0:
        return 1.0
    
    return free_flow / current


def _summarize_incident_severity(incidents: list) -> str:
    """Summarize incident severity distribution."""
    if not incidents:
        return "No active incidents"
    
    severity_counts = {}
    for inc in incidents:
        severity = inc.get('severity_label', 'Unknown')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    summary_parts = [f"{count} {severity}" for severity, count in severity_counts.items()]
    return ", ".join(summary_parts)


def _generate_llm_response(knowledge_base: dict) -> dict:
    """Generate natural language response using Groq LLM."""
    
    # Build concise prompt for LLM
    model_data = knowledge_base['model_predictions']
    zone = knowledge_base['zone_info']
    weather = knowledge_base['weather']
    traffic = knowledge_base['traffic_flow']
    incidents = knowledge_base['incidents']
    user = knowledge_base['user_query']
    
    prompt = f"""You are a traffic assistant AI. Answer the user's question based on this data:

    USER QUESTION: "{user['question']}"

    LOCATION: {model_data['location']}
    TRAVEL MODE: {user['mode']}
    CURRENT TIME: {user['time']}

    KNN MODEL PREDICTION:
    • Severity: {model_data['severity']}
    • Confidence: {model_data['confidence']:.0%}
    • Area Type: {zone.get('classification', {}).get('primary', 'Mixed')} - {zone.get('classification', {}).get('vibe', 'Urban')}

    CURRENT CONDITIONS:
    • Weather: {weather['condition']} ({weather['temperature']}°C) - Impact: {weather['impact']}
    • Traffic Speed: {traffic['current_speed']} km/h (normal: {traffic['free_flow_speed']} km/h)
    • Congestion: {traffic['congestion']}
    • Active Incidents: {incidents['count']} ({incidents['severity_summary']})

    AREA CHARACTERISTICS:
    • Walkability: {zone.get('scores', {}).get('walkability_score', 5):.1f}/10
    • Parking Ease: {zone.get('scores', {}).get('parking_ease_score', 5):.1f}/10
    • Safety: {zone.get('scores', {}).get('safety_score', 5):.1f}/10
    • Best For: {', '.join(zone.get('lifestyle', {}).get('best_for', ['General travel'])[:3])}

    TASK: Answer naturally in 2-3 sentences. Be helpful and actionable. Don't mention "models" or technical terms.

    Your response:"""

    try:
        from groq import Groq
        
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        
        answer = completion.choices[0].message.content.strip()
        
        return {
            "answer": answer,
            "confidence": model_data['confidence']
        }
        
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        
        # Fallback response
        severity = model_data['severity']
        location = model_data.get('location', 'the area')
        
        if severity in ['HIGH', 'VERY_HIGH']:
            answer = f"Traffic is currently heavy in {location} with {traffic['congestion']} congestion. Consider alternate routes or waiting for traffic to clear."
        elif severity == 'MODERATE':
            answer = f"Traffic is moderate in {location}. You'll experience some delays but it's manageable. Current speed is {traffic['current_speed']} km/h."
        else:
            answer = f"Traffic is light in {location}! Great time to travel with minimal congestion."
        
        return {
            "answer": answer,
            "confidence": model_data.get('confidence', 0.7)
        }


# ============================================================================
# API ROUTES
# ============================================================================

@app.post("/chat", response_model=ChatResponse)
async def chat_with_predictions(request: ChatRequest):
    """
    🤖 Conversational AI endpoint with KNN predictions + real-time data.
    
    Architecture:
    1. KNN Model → Traffic predictions from POI similarity
    2. Real-time APIs → Weather, Traffic Flow, Incidents
    3. LLM (Groq) → Natural language response generation
    
    Example requests:
    {
      "question": "Is it safe to drive to Koregaon Park right now?",
      "location": "Koregaon Park, Pune"
    }
    """
    try:
        load_chatbot()
        
        location_name = request.location
        mode = request.mode or "drive"
        
        if not location_name:
            raise HTTPException(400, "Location is required. Please specify where you want to travel.")
        
        # ✅ Step 1: Get KNN predictions ONLY (no hybrid)
        logger.info(f"🔵 [KNN] Getting predictions for: {location_name}")
        
        # Use KNN predictor directly from chatbot engine
        knn_result = chatbot_engine.predictor.predict(location_name)
        
        if not knn_result.get('success', False):
            raise HTTPException(400, f"Failed to get predictions for '{location_name}'")
        
        # Extract coordinates
        lat = knn_result['coordinates']['latitude']
        lon = knn_result['coordinates']['longitude']
        
        # ✅ Step 2: Fetch real-time data from external APIs
        logger.info(f"🌐 Fetching real-time data...")
        
        # Weather data
        weather = chatbot_engine.fetch_weather(lat, lon)
        
        # Traffic flow data
        traffic_flow = chatbot_engine.fetch_traffic_flow(lat, lon)
        
        # Incident data
        incidents = chatbot_engine.fetch_incidents(lat, lon)
        
        # ✅ Step 3: Build Knowledge Base for LLM
        logger.info(f"📚 Building knowledge base...")
        
        # Safe extraction with defaults
        prediction_data = knn_result.get('prediction', {})
        confidence = prediction_data.get('confidence', 0.7)  # ✅ Default to 0.7 if missing
        
        knowledge_base = {
            # KNN Model Predictions
            "model_predictions": {
                "location": knn_result.get('location', location_name),
                "coordinates": knn_result.get('coordinates', {'latitude': lat, 'longitude': lon}),
                "severity": prediction_data.get('severity', 'MODERATE'),
                "confidence": confidence,  # ✅ Use safe variable
                "probabilities": prediction_data.get('probabilities', {}),
                "hourly_forecast": knn_result.get('hourly_forecast', []),
                "similar_locations": knn_result.get('similar_locations', [])[:3]
            },
            
            # POI & Zone Information
            "zone_info": {
                "classification": knn_result.get('insights', {}).get('zone_classification', {}),
                "scores": knn_result.get('insights', {}).get('scores', {}),
                "lifestyle": knn_result.get('insights', {}).get('lifestyle_insights', {}),
                "poi_summary": knn_result.get('poi_summary', {})
            },
            
            # Real-time Weather
            "weather": {
                "condition": weather.get('condition', 'Unknown'),
                "temperature": weather.get('temp', 'N/A'),
                "humidity": weather.get('humidity', 'N/A'),
                "description": weather.get('description', ''),
                "impact": _assess_weather_impact(weather)  # ✅ Remove self.
            },
            
            # Real-time Traffic Flow
            "traffic_flow": {
                "current_speed": traffic_flow.get('current_speed', 0),
                "free_flow_speed": traffic_flow.get('free_flow_speed', 0),
                "congestion": _calculate_congestion(traffic_flow),  # ✅ Remove self.
                "delay_factor": _calculate_delay_factor(traffic_flow)  # ✅ Remove self.
            },
            
            # Real-time Incidents
            "incidents": {
                "count": len(incidents),
                "active": incidents[:5],
                "severity_summary": _summarize_incident_severity(incidents),  # ✅ Remove self.
                "types": list(set([inc.get('type', 'Unknown') for inc in incidents]))
            },
            
            # User Context
            "user_query": {
                "question": request.question,
                "mode": mode,
                "time": request.time or datetime.now().strftime("%H:%M")
            }
        }
        
        # ✅ Step 4: Generate LLM response using knowledge base
        logger.info(f"🤖 Generating conversational response with LLM...")
        
        llm_response = _generate_llm_response(knowledge_base)  # ✅ Remove self.

        # ✅ Step 5: Build response
        return ChatResponse(
            answer=llm_response['answer'],
            confidence=confidence,  # ✅ Use safe variable
            sources=[
                "KNN Model (POI Similarity)",
                "OpenWeatherMap API",
                "TomTom Traffic Flow API",
                "TomTom Incidents API"
            ],
            merged_insights=knowledge_base,
            prediction=knn_result
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(400, f"Invalid request: {str(e)}")
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(500, f"Internal error: {str(e)}")


# Helper methods for chat endpoint
def _assess_weather_impact(weather: dict) -> str:
    """Assess weather impact on traffic."""
    condition = weather.get('condition', '').lower()
    
    if 'rain' in condition or 'storm' in condition:
        return "HIGH - Rain increases congestion by 20-30%"
    elif 'fog' in condition or 'mist' in condition:
        return "MODERATE - Reduced visibility affects speed"
    elif 'clear' in condition or 'sunny' in condition:
        return "LOW - Clear weather, normal traffic flow"
    else:
        return "UNKNOWN - Weather impact unclear"


def _calculate_congestion(traffic_flow: dict) -> str:
    """Calculate congestion percentage from traffic flow."""
    current = traffic_flow.get('current_speed', 0)
    free_flow = traffic_flow.get('free_flow_speed', 0)
    
    if free_flow == 0:
        return "Unknown"
    
    congestion_ratio = 1 - (current / free_flow)
    congestion_pct = max(0, min(100, congestion_ratio * 100))
    
    return f"{congestion_pct:.0f}%"


def _calculate_delay_factor(traffic_flow: dict) -> float:
    """Calculate delay factor from traffic flow."""
    current = traffic_flow.get('current_speed', 0)
    free_flow = traffic_flow.get('free_flow_speed', 0)
    
    if current == 0 or free_flow == 0:
        return 1.0
    
    return free_flow / current


def _summarize_incident_severity(incidents: list) -> str:
    """Summarize incident severity distribution."""
    if not incidents:
        return "No active incidents"
    
    severity_counts = {}
    for inc in incidents:
        severity = inc.get('severity_label', 'Unknown')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    summary_parts = [f"{count} {severity}" for severity, count in severity_counts.items()]
    return ", ".join(summary_parts)


def _generate_llm_response(knowledge_base: dict) -> dict:
    """Generate natural language response using Groq LLM."""
    
    # Build concise prompt for LLM
    model_data = knowledge_base['model_predictions']
    zone = knowledge_base['zone_info']
    weather = knowledge_base['weather']
    traffic = knowledge_base['traffic_flow']
    incidents = knowledge_base['incidents']
    user = knowledge_base['user_query']
    
    prompt = f"""You are a traffic assistant AI. Answer the user's question based on this data:

        USER QUESTION: "{user['question']}"

        LOCATION: {model_data['location']}
        TRAVEL MODE: {user['mode']}
        CURRENT TIME: {user['time']}

        KNN MODEL PREDICTION:
        • Severity: {model_data['severity']}
        • Confidence: {model_data['confidence']:.0%}
        • Area Type: {zone.get('classification', {}).get('primary', 'Mixed')} - {zone.get('classification', {}).get('vibe', 'Urban')}

        CURRENT CONDITIONS:
        • Weather: {weather['condition']} ({weather['temperature']}°C) - Impact: {weather['impact']}
        • Traffic Speed: {traffic['current_speed']} km/h (normal: {traffic['free_flow_speed']} km/h)
        • Congestion: {traffic['congestion']}
        • Active Incidents: {incidents['count']} ({incidents['severity_summary']})

        AREA CHARACTERISTICS:
        • Walkability: {zone.get('scores', {}).get('walkability_score', 5):.1f}/10
        • Parking Ease: {zone.get('scores', {}).get('parking_ease_score', 5):.1f}/10
        • Safety: {zone.get('scores', {}).get('safety_score', 5):.1f}/10
        • Best For: {', '.join(zone.get('lifestyle', {}).get('best_for', ['General travel'])[:3])}

        TASK: Answer naturally in 2-3 sentences. Be helpful and actionable. Don't mention "models" or technical terms.

        Your response:"""

    try:
        from groq import Groq
        
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        
        answer = completion.choices[0].message.content.strip()
        
        return {
            "answer": answer,
            "confidence": model_data['confidence']
        }
        
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        
        # Fallback response
        severity = model_data['severity']
        location = model_data.get('location', 'the area')
        
        if severity in ['HIGH', 'VERY_HIGH']:
            answer = f"Traffic is currently heavy in {location} with {traffic['congestion']} congestion. Consider alternate routes or waiting for traffic to clear."
        elif severity == 'MODERATE':
            answer = f"Traffic is moderate in {location}. You'll experience some delays but it's manageable. Current speed is {traffic['current_speed']} km/h."
        else:
            answer = f"Traffic is light in {location}! Great time to travel with minimal congestion."
        
class IncidentRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = 10.0

class IncidentResponse(BaseModel):
    incidents: List[dict]
    analytics: dict
    count: int

@app.post("/api/incidents/analytics", response_model=IncidentResponse)
async def get_incident_analytics(request: IncidentRequest):
    try:
        load_incident_analytics()
        incidents = incident_analytics.fetch_incidents_for_region(
            request.latitude, request.longitude, request.radius_km
        )
        analytics = incident_analytics.generate_analytics(incidents)
        return IncidentResponse(incidents=incidents, analytics=analytics, count=len(incidents))
    except Exception as e:
        logger.error(f"Incident analytics error: {e}")
        raise HTTPException(500, detail=str(e))


@app.post("/sos", response_model=SOSResponse)
async def send_sos_alert(request: SOSRequest):
    """
    🆘 Send SOS alert to emergency contacts via WhatsApp.
    
    Example request:
    {
      "origin": "Koregaon Park, Pune",
      "destination": "Baner, Pune",
      "phone_numbers": ["+918767491689", "+919876543210"],
      "current_location": {"latitude": 18.5, "longitude": 73.8}
    }
    """
    try:
        sent_to = []
        failed = []
        
        for phone in request.phone_numbers:
            logger.info(f"📱 Sending SOS to {phone}")
            
            result = await whatsapp_service.send_sos_message(
                to_phone=phone,
                origin=request.origin,
                destination=request.destination,
                current_location=request.current_location
            )
            
            if result['success']:
                sent_to.append(phone)
            else:
                failed.append({
                    'phone': phone,
                    'error': result['error']
                })
        
        if sent_to:
            return SOSResponse(
                success=True,
                message=f"SOS alert sent to {len(sent_to)} contact(s)",
                sent_to=sent_to,
                failed=failed
            )
        else:
            raise HTTPException(500, f"Failed to send SOS to all contacts: {failed}")
            
    except Exception as e:
        logger.error(f"SOS endpoint error: {e}")
        raise HTTPException(500, f"Error sending SOS: {str(e)}")


@app.post("/reminders", response_model=ReminderResponse)
async def create_reminder(request: ReminderRequest):
    """📅 Schedule a reminder to be sent via WhatsApp, Email, or Both."""
    try:
        # Parse scheduled time
        try:
            scheduled_dt = datetime.fromisoformat(request.scheduled_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(400, "Invalid time format. Use ISO format like '2024-12-01T15:30:00'")
        
        # Validate reminder type
        try:
            reminder_type_enum = ReminderType(request.reminder_type.lower())
        except ValueError:
            raise HTTPException(400, f"Invalid reminder_type. Must be 'whatsapp', 'email', or 'both'")
        
        # Validate scheduled time is in the future
        # Make datetime.now() timezone-aware if scheduled_dt has timezone info
        now = datetime.now(timezone.utc) if scheduled_dt.tzinfo else datetime.now()
        if scheduled_dt <= now:
            raise HTTPException(400, "Scheduled time must be in the future")
        
        # Create the reminder
        reminder = scheduler.schedule_reminder(
            message=request.message,
            recipient=request.recipient,
            reminder_type=reminder_type_enum,
            scheduled_time=scheduled_dt
        )
        
        logger.info(f"✅ Created reminder {reminder.id} for {scheduled_dt}")
        
        return ReminderResponse(
            reminder_id=reminder.id,
            message=reminder.message,
            recipient=reminder.recipient,
            reminder_type=reminder.reminder_type.value,
            scheduled_time=reminder.scheduled_time.isoformat(),
            status=reminder.status.value,
            created_at=reminder.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating reminder: {e}")
        raise HTTPException(500, f"Failed to create reminder: {str(e)}")


@app.get("/reminders")
async def list_reminders(
    status: Optional[str] = None,
    reminder_type: Optional[str] = None
    ):
    """📋 List all reminders with optional filtering."""
    try:
        status_filter = ReminderStatus(status) if status else None
        type_filter = ReminderType(reminder_type) if reminder_type else None
        
        reminders = scheduler.list_reminders(status_filter, type_filter)
        
        return {
            "reminders": [
                {
                    "reminder_id": r.id,
                    "message": r.message,
                    "recipient": r.recipient,
                    "reminder_type": r.reminder_type.value,
                    "scheduled_time": r.scheduled_time.isoformat(),
                    "status": r.status.value,
                    "created_at": r.created_at.isoformat(),
                    "sent_at": r.sent_at.isoformat() if r.sent_at else None,
                    "error_message": r.error_message
                }
                for r in reminders
            ],
            "count": len(reminders)
        }
    except ValueError as e:
        raise HTTPException(400, f"Invalid filter value: {str(e)}")
    except Exception as e:
        logger.error(f"Error listing reminders: {e}")
        raise HTTPException(500, f"Failed to list reminders: {str(e)}")


@app.get("/reminders/stats")
async def get_reminder_stats():
    """📊 Get statistics about reminders."""
    try:
        stats = scheduler.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(500, f"Failed to get stats: {str(e)}")


@app.get("/reminders/{reminder_id}")
async def get_reminder(reminder_id: str):
    """🔍 Get details of a specific reminder."""
    try:
        reminder = scheduler.get_reminder(reminder_id)
        
        if not reminder:
            raise HTTPException(404, f"Reminder {reminder_id} not found")
        
        return {
            "reminder_id": reminder.id,
            "message": reminder.message,
            "recipient": reminder.recipient,
            "reminder_type": reminder.reminder_type.value,
            "scheduled_time": reminder.scheduled_time.isoformat(),
            "status": reminder.status.value,
            "created_at": reminder.created_at.isoformat(),
            "sent_at": reminder.sent_at.isoformat() if reminder.sent_at else None,
            "error_message": reminder.error_message,
            "metadata": reminder.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reminder: {e}")
        raise HTTPException(500, f"Failed to get reminder: {str(e)}")


@app.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str):
    """🗑️ Cancel or delete a reminder."""
    try:
        reminder = scheduler.get_reminder(reminder_id)
        
        if not reminder:
            raise HTTPException(404, f"Reminder {reminder_id} not found")
        
        if reminder.status == ReminderStatus.PENDING:
            cancelled = scheduler.cancel_reminder(reminder_id)
            if cancelled:
                return {
                    "message": "Reminder cancelled successfully",
                    "reminder_id": reminder_id,
                    "status": "cancelled"
                }
        
        deleted = scheduler.delete_reminder(reminder_id)
        if deleted:
            return {
                "message": "Reminder deleted successfully",
                "reminder_id": reminder_id,
                "status": "deleted"
            }
        
        raise HTTPException(500, "Failed to delete reminder")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting reminder: {e}")
        raise HTTPException(500, f"Failed to delete reminder: {str(e)}")


# ============================================================================
# SAFE ROUTE APIs
# ============================================================================

def generate_fallback_routes(source: Coordinates, destination: Coordinates) -> tuple:
    """
    Generate fallback mock routes when TomTom API is unavailable
    
    Returns tuple: (list of routes, distance_km, duration_minutes)
    """
    source_lat, source_lon = source.latitude, source.longitude
    dest_lat, dest_lon = destination.latitude, destination.longitude
    
    # Generate 3 different routes with slight variations
    # Route 1: Direct path with slight north deviation
    route1 = []
    for i in range(11):
        lat = source_lat + (dest_lat - source_lat) * (i / 10)
        lon = source_lon + (dest_lon - source_lon) * (i / 10)
        if i % 2 == 0:
            lat += 0.003  # Slight north deviation
        route1.append((lat, lon))
    
    # Route 2: Direct path with slight south deviation
    route2 = []
    for i in range(11):
        lat = source_lat + (dest_lat - source_lat) * (i / 10)
        lon = source_lon + (dest_lon - source_lon) * (i / 10)
        if i % 2 == 0:
            lat -= 0.003  # Slight south deviation
        route2.append((lat, lon))
    
    # Route 3: Longer path with more waypoints
    route3 = []
    for i in range(15):
        lat = source_lat + (dest_lat - source_lat) * (i / 14)
        lon = source_lon + (dest_lon - source_lon) * (i / 14)
        if i % 3 == 0:
            lon += 0.002  # East deviation
        else:
            lon -= 0.001  # West deviation
        route3.append((lat, lon))
    
    # Calculate distance and duration for fallback
    R = 6371  # Earth's radius in km
    phi1 = math.radians(source_lat)
    phi2 = math.radians(dest_lat)
    delta_phi = math.radians(dest_lat - source_lat)
    delta_lambda = math.radians(dest_lon - source_lon)
    
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance_km = R * c
    duration_minutes = (distance_km / 40) * 60
    
    return [route1, route2, route3], distance_km, duration_minutes


@app.get("/health", response_model=HealthCheck)
async def health_check_safe():
    """Health check endpoint for safe routes."""
    return HealthCheck(
        status="healthy",
        message="SafeRoute API is running"
    )


@app.post("/api/routes", response_model=RouteResponse)
async def calculate_safe_routes(request: RouteRequest):
    """
    Main endpoint to calculate 3 safest routes between source and destination.
    
    Args:
        request: RouteRequest with source, destination, and travel_mode
    
    Returns:
        RouteResponse with 3 routes ranked by safety
    """
    try:
        load_safety_calculator()
        
        # Validate coordinates
        if not (-90 <= request.source.latitude <= 90 and -180 <= request.source.longitude <= 180):
            raise HTTPException(status_code=400, detail="Invalid source coordinates")
        if not (-90 <= request.destination.latitude <= 90 and -180 <= request.destination.longitude <= 180):
            raise HTTPException(status_code=400, detail="Invalid destination coordinates")
        
        # Generate mock routes (fallback)
        mock_routes, distance_km, duration_minutes = generate_fallback_routes(
            request.source, 
            request.destination
        )
        
        # Process each route
        processed_routes = []
        for idx, route_points in enumerate(mock_routes):
            # Calculate danger index for this route
            danger_index, danger_points_count = safety_calculator.calculate_route_danger_index(route_points)
            
            # Get danger level and color
            danger_level, color_code = safety_calculator.get_danger_level_and_color(danger_index)
            
            # Convert points to RoutePoint objects
            route_points_objs = [RoutePoint(latitude=lat, longitude=lon) for lat, lon in route_points]
            
            # Create route object
            route = Route(
                route_id=idx,
                route_name=f"Route {idx + 1}",
                points=route_points_objs,
                distance=distance_km,
                duration=duration_minutes,
                danger_index=round(danger_index, 2),
                danger_level=danger_level,
                danger_points_count=danger_points_count,
                color_code=color_code
            )
            processed_routes.append(route.dict())
        
        # Sort routes by safety
        sorted_routes = RouteOptimizer.sort_routes_by_safety(processed_routes)
        
        # Convert back to Route objects
        final_routes = [Route(**route) for route in sorted_routes]
        
        logger.info(f"✅ Calculated {len(final_routes)} safe routes")
        
        # Return response
        return RouteResponse(
            source=request.source,
            destination=request.destination,
            routes=final_routes,
            travel_mode=request.travel_mode,
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Route calculation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/routes/safe", response_model=RouteResponse)
async def calculate_safe_routes_alt(request: RouteRequest):
    """
    Alternative endpoint for calculating safe routes (backwards compatibility)
    """
    return await calculate_safe_routes(request)