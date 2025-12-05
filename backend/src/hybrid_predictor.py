"""
Hybrid Traffic Predictor - Combines KNN + RandomForest for superior accuracy
"""

import numpy as np
import pandas as pd
import joblib
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from src.predict_knn import KNNTrafficPredictor
from src.data_prep import DataPreprocessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridTrafficPredictor:
    """
    Ensemble predictor combining KNN (POI similarity) + RandomForest (traffic patterns).
    
    Strategy:
    - KNN: Good for new locations with similar POI profiles
    - RF: Good for known locations with traffic history
    - Ensemble: Weighted combination based on confidence scores
    """
    
    def __init__(self, knn_weight=0.5, rf_weight=0.5):
        """
        Initialize hybrid predictor.
        
        Args:
            knn_weight: Weight for KNN predictions (0-1)
            rf_weight: Weight for RF predictions (0-1)
        """
        self.knn_weight = knn_weight
        self.rf_weight = rf_weight
        
        # Initialize KNN predictor
        logger.info("🔵 Loading KNN predictor...")
        self.knn_predictor = KNNTrafficPredictor(model_type='new_severity_logical')
        
        # Load RF models
        logger.info("🟢 Loading RandomForest models...")
        self._load_rf_models()
        
        logger.info("✅ Hybrid predictor initialized")
        logger.info(f"   KNN weight: {knn_weight:.2f}")
        logger.info(f"   RF weight: {rf_weight:.2f}")
    
    def _load_rf_models(self):
        """Load RandomForest models and preprocessor from PKL."""
        model_path = Path(__file__).parent.parent / 'models' / 'traffic_predictor.pkl'
        
        if not model_path.exists():
            logger.warning("⚠️ RandomForest models not found - using KNN only")
            self.rf_models = None
            self.preprocessor = None
            return
        
        try:
            model_data = joblib.load(model_path)
            
            self.rf_models = model_data['models']
            
            # Initialize preprocessor
            self.preprocessor = DataPreprocessor()
            preprocessor_state = {
                'scaler': model_data['scaler'],
                'location_encoder': model_data['location_encoder'],
                'frc_encoder': model_data['frc_encoder'],
                'poi_columns': model_data['poi_columns'],
                'poi_min_max': model_data.get('poi_min_max', {}),
                'feature_column_order': model_data.get('feature_column_order', []),
                'is_fitted': True
            }
            self.preprocessor.set_preprocessor_state(preprocessor_state)
            
            logger.info(f"✅ Loaded {len(self.rf_models)} RF models")
            logger.info(f"   Targets: {list(self.rf_models.keys())}")
            
        except Exception as e:
            logger.error(f"❌ Error loading RF models: {e}")
            self.rf_models = None
            self.preprocessor = None
    
    def predict(self, location_name: str, radius: int = 1000) -> Dict:
        """
        Predict traffic using hybrid ensemble approach.
        
        Args:
            location_name: Name of location
            radius: POI search radius in meters
            
        Returns:
            dict: Hybrid prediction results
        """
        logger.info("="*80)
        logger.info(f"🎯 HYBRID PREDICTION FOR: {location_name}")
        logger.info("="*80)
        
        # Step 1: Get KNN prediction
        logger.info("\n🔵 Phase 1: KNN Prediction (POI Similarity)")
        knn_result = self.knn_predictor.predict(location_name, radius=radius)
        
        if not knn_result['success']:
            return knn_result
        
        knn_confidence = self._calculate_knn_confidence(knn_result)
        logger.info(f"   ✓ KNN Confidence: {knn_confidence:.2%}")
        
        # Step 2: Get RF prediction (if available)
        rf_result = None
        rf_confidence = 0.0
        
        if self.rf_models is not None:
            logger.info("\n🟢 Phase 2: RandomForest Prediction (Traffic Patterns)")
            rf_result = self._predict_with_rf(knn_result)
            
            if rf_result is not None:
                rf_confidence = self._calculate_rf_confidence(rf_result)
                logger.info(f"   ✓ RF Confidence: {rf_confidence:.2%}")
        else:
            logger.info("\n⚠️ Phase 2: RF models not available - using KNN only")
        
        # Step 3: Ensemble fusion
        logger.info("\n🔀 Phase 3: Ensemble Fusion")
        hybrid_result = self._fuse_predictions(
            knn_result, 
            rf_result, 
            knn_confidence, 
            rf_confidence
        )
        
        # Step 4: Generate enhanced insights
        logger.info("\n💡 Phase 4: Enhanced Insights")
        hybrid_result['insights'] = self._generate_hybrid_insights(
            knn_result, 
            rf_result, 
            hybrid_result
        )
        
        logger.info("\n✅ Hybrid prediction complete!")
        logger.info(f"   Final Severity: {hybrid_result['prediction']['severity']}")
        logger.info(f"   Ensemble Confidence: {hybrid_result['prediction']['ensemble_confidence']:.2%}")
        
        return hybrid_result
    
    def _predict_with_rf(self, knn_result: Dict) -> Optional[Dict]:
        """Make prediction using RandomForest models."""
        try:
            location_name = knn_result['location']
            lat = knn_result['coordinates']['latitude']
            lon = knn_result['coordinates']['longitude']
            poi_counts = knn_result['poi_summary']['top_categories']
            
            # Prepare input data for RF
            hourly_predictions = []
            
            for hour in range(6, 22):  # 6 AM - 9 PM
                # Create feature vector
                input_data = {
                    'location_name': location_name,
                    'latitude': lat,
                    'longitude': lon,
                    'hour': hour,
                    'frc': 'FRC3',  # Default functional road class
                }
                
                # Add POI features
                for poi, count in poi_counts:
                    input_data[poi] = count
                
                # Create DataFrame
                input_df = pd.DataFrame([input_data])
                
                # Preprocess
                X_processed = self.preprocessor.transform(input_df)
                
                # Predict with RF models
                prediction = {
                    'hour': hour,
                    'current_speed': float(self.rf_models['current_speed'].predict(X_processed)[0]),
                    'free_flow_speed': float(self.rf_models['free_flow_speed'].predict(X_processed)[0]),
                    'speed_reduction': float(self.rf_models['speed_reduction'].predict(X_processed)[0]),
                    'congestion_ratio': float(self.rf_models['congestion_ratio'].predict(X_processed)[0]),
                    'severity_encoded': float(self.rf_models['severity_encoded'].predict(X_processed)[0])
                }
                
                # Convert severity_encoded to category
                prediction['severity'] = self._encode_to_severity(prediction['severity_encoded'])
                
                hourly_predictions.append(prediction)
            
            return {
                'hourly_predictions': hourly_predictions,
                'location': location_name
            }
            
        except Exception as e:
            logger.error(f"❌ RF prediction failed: {e}")
            return None
    
    def _calculate_knn_confidence(self, knn_result: Dict) -> float:
        """Calculate confidence score for KNN prediction."""
        try:
            # Extract similarity distances
            # Lower distance = Higher confidence
            similar_locations = knn_result.get('similar_locations', [])
            
            if len(similar_locations) == 0:
                return 0.5  # Default medium confidence
            
            # In KNN, we stored the most similar city
            # We can approximate confidence based on POI diversity
            poi_summary = knn_result['poi_summary']
            total_pois = poi_summary.get('total_pois', 0)
            unique_categories = len(poi_summary.get('top_categories', []))
            
            # More POIs and categories = Higher confidence
            poi_confidence = min(1.0, total_pois / 100.0)
            diversity_confidence = min(1.0, unique_categories / 20.0)
            
            # Probability from prediction
            prob_dict = knn_result['prediction'].get('probabilities', {})
            max_prob = max(prob_dict.values()) if prob_dict else 0.5
            
            # Weighted combination
            confidence = (
                0.4 * max_prob +           # Prediction certainty
                0.3 * poi_confidence +      # POI density
                0.3 * diversity_confidence  # POI variety
            )
            
            return confidence
            
        except Exception as e:
            logger.warning(f"⚠️ KNN confidence calculation failed: {e}")
            return 0.5
    
    def _calculate_rf_confidence(self, rf_result: Dict) -> float:
        """Calculate confidence score for RF prediction."""
        try:
            hourly_preds = rf_result['hourly_predictions']
            
            # Check variance in predictions
            severities = [p['severity_encoded'] for p in hourly_preds]
            severity_std = np.std(severities)
            
            # Lower variance = More consistent = Higher confidence
            consistency_score = 1.0 / (1.0 + severity_std)
            
            # Check if speeds are realistic
            speeds = [p['current_speed'] for p in hourly_preds]
            speed_mean = np.mean(speeds)
            
            # Reasonable speed range: 10-80 km/h
            realism_score = 1.0 if 10 <= speed_mean <= 80 else 0.5
            
            # Combine
            confidence = 0.7 * consistency_score + 0.3 * realism_score
            
            return confidence
            
        except Exception as e:
            logger.warning(f"⚠️ RF confidence calculation failed: {e}")
            return 0.5
    
    def _fuse_predictions(
        self, 
        knn_result: Dict, 
        rf_result: Optional[Dict],
        knn_confidence: float,
        rf_confidence: float
    ) -> Dict:
        """Fuse KNN and RF predictions using weighted ensemble."""
        
        if rf_result is None:
            # RF not available - use KNN only
            logger.info("   Using KNN prediction only")
            knn_result['prediction']['ensemble_confidence'] = knn_confidence
            knn_result['prediction']['ensemble_method'] = 'KNN_ONLY'
            return knn_result
        
        # Calculate adaptive weights based on confidence
        total_confidence = knn_confidence + rf_confidence
        
        if total_confidence > 0:
            adaptive_knn_weight = knn_confidence / total_confidence
            adaptive_rf_weight = rf_confidence / total_confidence
        else:
            adaptive_knn_weight = 0.5
            adaptive_rf_weight = 0.5
        
        logger.info(f"   Adaptive weights: KNN={adaptive_knn_weight:.2%}, RF={adaptive_rf_weight:.2%}")
        
        # Fuse hourly forecasts
        knn_hourly = knn_result['hourly_forecast']
        rf_hourly = rf_result['hourly_predictions']
        
        fused_hourly = []
        
        for knn_hour, rf_hour in zip(knn_hourly, rf_hourly):
            # Weighted average for numeric values
            fused = {
                'hour': knn_hour['hour'],
                'current_speed': (
                    adaptive_knn_weight * knn_hour.get('current_speed', 0) +
                    adaptive_rf_weight * rf_hour['current_speed']
                ),
                'free_flow_speed': (
                    adaptive_knn_weight * knn_hour.get('free_flow_speed', 0) +
                    adaptive_rf_weight * rf_hour['free_flow_speed']
                ),
                'congestion_ratio': (
                    adaptive_knn_weight * knn_hour.get('congestion_ratio', 0) +
                    adaptive_rf_weight * rf_hour['congestion_ratio']
                )
            }
            
            # For severity (categorical), use higher confidence model
            if adaptive_rf_weight > adaptive_knn_weight:
                fused['severity'] = rf_hour['severity']
            else:
                fused['severity'] = knn_hour['severity']
            
            # Calculate combined confidence for this hour
            fused['confidence'] = (
                adaptive_knn_weight * knn_hour.get('confidence', knn_confidence) +
                adaptive_rf_weight * 0.9  # RF typically has high confidence
            )
            
            fused_hourly.append(fused)
        
        # Build hybrid result
        hybrid_result = knn_result.copy()
        hybrid_result['hourly_forecast'] = fused_hourly
        
        # Calculate overall severity
        severities = [h['severity'] for h in fused_hourly]
        from collections import Counter
        severity_counts = Counter(severities)
        overall_severity = severity_counts.most_common(1)[0][0]
        
        hybrid_result['prediction'] = {
            'severity': overall_severity,
            'severity_score': self._severity_to_score(overall_severity),
            'ensemble_confidence': (knn_confidence + rf_confidence) / 2,
            'knn_confidence': knn_confidence,
            'rf_confidence': rf_confidence,
            'knn_weight': adaptive_knn_weight,
            'rf_weight': adaptive_rf_weight,
            'ensemble_method': 'HYBRID_KNN_RF',
            'model_type': 'hybrid'
        }
        
        return hybrid_result
    
    def _generate_hybrid_insights(
        self,
        knn_result: Dict,
        rf_result: Optional[Dict],
        hybrid_result: Dict
    ) -> Dict:
        """Generate enhanced insights from both models."""
        
        # Start with KNN insights
        insights = knn_result['insights'].copy()
        
        # Add RF-specific insights if available
        if rf_result is not None:
            rf_hourly = rf_result['hourly_predictions']
            
            # Traffic pattern analysis from RF
            morning_speeds = [h['current_speed'] for h in rf_hourly if 6 <= h['hour'] <= 9]
            evening_speeds = [h['current_speed'] for h in rf_hourly if 17 <= h['hour'] <= 20]
            
            avg_morning_speed = np.mean(morning_speeds) if morning_speeds else 0
            avg_evening_speed = np.mean(evening_speeds) if evening_speeds else 0
            
            insights['traffic_patterns'] = {
                'morning_rush_avg_speed': round(avg_morning_speed, 1),
                'evening_rush_avg_speed': round(avg_evening_speed, 1),
                'speed_drop_evening': round(avg_morning_speed - avg_evening_speed, 1),
                'pattern_type': 'commuter' if abs(avg_morning_speed - avg_evening_speed) > 10 else 'steady'
            }
            
            # Congestion analysis
            congestion_ratios = [h['congestion_ratio'] for h in rf_hourly]
            insights['congestion_analysis'] = {
                'avg_congestion': round(np.mean(congestion_ratios), 2),
                'peak_congestion': round(max(congestion_ratios), 2),
                'congestion_variability': round(np.std(congestion_ratios), 2)
            }
        
        # Add ensemble metadata
        insights['model_info'] = {
            'ensemble_method': hybrid_result['prediction']['ensemble_method'],
            'knn_weight': round(hybrid_result['prediction'].get('knn_weight', 0.5), 2),
            'rf_weight': round(hybrid_result['prediction'].get('rf_weight', 0.5), 2),
            'ensemble_confidence': round(hybrid_result['prediction']['ensemble_confidence'], 2)
        }
        
        # Enhanced recommendations
        ensemble_conf = hybrid_result['prediction']['ensemble_confidence']
        
        if ensemble_conf > 0.8:
            insights['recommendation_confidence'] = "HIGH - Both models agree"
        elif ensemble_conf > 0.6:
            insights['recommendation_confidence'] = "MEDIUM - Models partially agree"
        else:
            insights['recommendation_confidence'] = "LOW - Models show divergence"
        
        return insights
    
    def _encode_to_severity(self, severity_encoded: float) -> str:
        """Convert encoded severity to category."""
        if severity_encoded < 0.3:
            return 'LOW'
        elif severity_encoded < 0.6:
            return 'MODERATE'
        elif severity_encoded < 0.85:
            return 'HIGH'
        else:
            return 'VERY_HIGH'
    
    def _severity_to_score(self, severity: str) -> float:
        """Convert severity category to numeric score."""
        severity_map = {
            'LOW': 0,
            'MODERATE': 1,
            'HIGH': 2,
            'VERY_HIGH': 3,
            'SEVERE': 3
        }
        return severity_map.get(severity, 1)
    
    def predict_location(self, location_name: str) -> Dict:
        """Alias for predict() for API compatibility."""
        return self.predict(location_name)


def main():
    """Test hybrid predictor."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python hybrid_predictor.py <location_name>")
        print("Example: python hybrid_predictor.py 'Andheri, Mumbai'")
        return
    
    location = ' '.join(sys.argv[1:])
    
    predictor = HybridTrafficPredictor(knn_weight=0.5, rf_weight=0.5)
    result = predictor.predict(location)
    
    if result['success']:
        print(f"\n✅ Hybrid Prediction for: {result['location']}")
        print(f"🚦 Severity: {result['prediction']['severity']}")
        print(f"📊 Confidence: {result['prediction']['ensemble_confidence']:.2%}")
        print(f"🔵 KNN Weight: {result['prediction']['knn_weight']:.2%}")
        print(f"🟢 RF Weight: {result['prediction']['rf_weight']:.2%}")
    else:
        print(f"\n❌ Error: {result['error']}")


if __name__ == "__main__":
    main()