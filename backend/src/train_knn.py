"""
KNN Model training module for traffic severity prediction.
Replaces RandomForest with KNN approach.
"""

import pandas as pd
import numpy as np
import joblib
import logging
from pathlib import Path
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KNNTrainer:
    """Handles training of KNN models for traffic severity prediction."""
    
    def __init__(self, model_dir='models/knn'):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Default to new_severity_logical as specified
        self.target_column = 'new_severity_logical'
        
    def train_models(self, traffic_path='data/traffic_with_categories.csv'):
        """
        Train KNN models for traffic severity prediction.
        
        Args:
            traffic_path: Path to traffic data with categories
        """
        logger.info("="*80)
        logger.info("TRAINING KNN MODELS FOR TRAFFIC SEVERITY")
        logger.info("="*80)
        
        # Load data
        logger.info(f"\n📂 Loading data from {traffic_path}...")
        df = pd.read_csv(traffic_path)
        logger.info(f"✅ Loaded {len(df)} records")
        
        # Extract POI features (all columns starting from ACCESS_GATEWAY onwards)
        poi_start_idx = df.columns.get_loc('ACCESS_GATEWAY')
        poi_columns = df.columns[poi_start_idx:].tolist()
        
        # Remove target columns from features
        target_columns = ['new_severity', 'new_severity_logical', 'severity']
        poi_features = [col for col in poi_columns if col not in target_columns]
        
        logger.info(f"📊 Using {len(poi_features)} POI features")
        
        # Prepare features and target
        X = df[poi_features]
        y = df[self.target_column]
        
        logger.info(f"\n🎯 Target distribution ({self.target_column}):")
        for severity, count in y.value_counts().items():
            logger.info(f"   {severity}: {count} ({count/len(y)*100:.1f}%)")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"\n✂️ Split: {len(X_train)} train, {len(X_test)} test")
        
        # Scale features
        logger.info("\n⚖️ Scaling features...")
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train KNN classifier
        logger.info("\n🤖 Training KNN classifier (k=5)...")
        knn_classifier = KNeighborsClassifier(
            n_neighbors=5,
            weights='distance',
            metric='euclidean',
            n_jobs=-1
        )
        
        knn_classifier.fit(X_train_scaled, y_train)
        
        # Cross-validation
        logger.info("📊 Performing 5-fold cross-validation...")
        cv_scores = cross_val_score(
            knn_classifier, X_train_scaled, y_train,
            cv=5, scoring='accuracy', n_jobs=-1
        )
        
        logger.info(f"   CV Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        # Test evaluation
        y_pred = knn_classifier.predict(X_test_scaled)
        test_accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"\n✅ Test Accuracy: {test_accuracy:.3f}")
        logger.info("\n📋 Classification Report:")
        logger.info("\n" + classification_report(y_test, y_pred))
        
        # Save models
        logger.info("\n💾 Saving models...")
        
        joblib.dump(knn_classifier, self.model_dir / 'knn_classifier_logical.pkl')
        joblib.dump(scaler, self.model_dir / 'scaler_classifier.pkl')
        joblib.dump(poi_features, self.model_dir / 'poi_features.pkl')
        
        logger.info(f"   ✅ Saved to {self.model_dir}/")
        logger.info(f"      - knn_classifier_logical.pkl")
        logger.info(f"      - scaler_classifier.pkl")
        logger.info(f"      - poi_features.pkl")
        
        # Train similarity model for finding similar locations
        logger.info("\n🔍 Training similarity model...")
        self._train_similarity_model(df, poi_features)
        
        logger.info("\n" + "="*80)
        logger.info("✅ KNN TRAINING COMPLETE!")
        logger.info("="*80)
        
        return {
            'test_accuracy': test_accuracy,
            'cv_scores': cv_scores.tolist(),
            'features': poi_features
        }
    
    def _train_similarity_model(self, df, poi_features):
        """Train KNN model for finding similar locations."""
        
        # Create location-level aggregated data
        location_data = df.groupby('location_name').agg({
            'latitude': 'first',
            'longitude': 'first',
            self.target_column: lambda x: (x.isin(['HIGH', 'SEVERE'])).mean(),
            **{feat: 'sum' for feat in poi_features}
        }).reset_index()
        
        location_data.rename(columns={self.target_column: 'high_severity_ratio'}, inplace=True)
        location_data['total_pois'] = location_data[poi_features].sum(axis=1)
        
        # Features for similarity: total_pois + high_severity_ratio + top POI categories
        similarity_features = ['total_pois', 'high_severity_ratio'] + poi_features
        
        X_sim = location_data[similarity_features]
        
        # Scale
        scaler_sim = StandardScaler()
        X_sim_scaled = scaler_sim.fit_transform(X_sim)
        
        # Train KNN for similarity (k=10 to find similar locations)
        knn_similarity = KNeighborsClassifier(
            n_neighbors=10,
            weights='distance',
            metric='euclidean',
            n_jobs=-1
        )
        
        # Fit on location data (we'll use it for nearest neighbors search)
        knn_similarity.fit(X_sim_scaled, location_data['location_name'])
        
        # Save similarity model
        joblib.dump(knn_similarity, self.model_dir / 'knn_similarity.pkl')
        joblib.dump(scaler_sim, self.model_dir / 'scaler_similarity.pkl')
        joblib.dump(similarity_features, self.model_dir / 'knn_features.pkl')
        location_data.to_csv(self.model_dir / 'location_data.csv', index=False)
        
        logger.info(f"   ✅ Similarity model saved ({len(location_data)} reference locations)")


if __name__ == '__main__':
    trainer = KNNTrainer()
    metrics = trainer.train_models()
    
    print("\n" + "="*80)
    print("TRAINING SUMMARY")
    print("="*80)
    print(f"Test Accuracy: {metrics['test_accuracy']:.3f}")
    print(f"CV Scores: {metrics['cv_scores']}")
    print(f"Features: {len(metrics['features'])}")
    print("="*80)