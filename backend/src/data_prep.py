"""
Data preparation module for traffic and POI data processing.
Handles merging, feature engineering, and data preprocessing.
CSV-only version.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Handles data loading, merging, and feature engineering."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.location_encoder = LabelEncoder()
        self.frc_encoder = LabelEncoder()
        self.poi_columns = []
        self.poi_min_max = {}
        self.is_fitted = False
        
    def load_data(self, traffic_path='data/traffic.csv', pois_path='data/pois.csv'):
        """
        Load traffic and POI datasets (CSV only).
        
        Args:
            traffic_path: Path to traffic CSV file
            pois_path: Path to POI CSV file
            
        Returns:
            Tuple of (traffic_df, pois_df)
        """
        logger.info(f"Loading traffic data from {traffic_path}")
        traffic_df = self._read_csv(traffic_path)
        
        logger.info(f"Loading POI data from {pois_path}")
        pois_df = self._read_csv(pois_path)
        
        logger.info(f"Traffic data shape: {traffic_df.shape}")
        logger.info(f"POI data shape: {pois_df.shape}")
        
        return traffic_df, pois_df
    
    def _read_csv(self, file_path):
        """
        Read CSV file with multiple encoding attempts.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")
        
        # Try multiple encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(path, encoding=encoding)
                logger.info(f"Successfully read CSV with encoding: {encoding}")
                return df
            except (UnicodeDecodeError, pd.errors.ParserError) as e:
                if encoding == encodings[-1]:
                    raise ValueError(
                        f"Failed to read {path} with any encoding. "
                        f"Please ensure the file is a valid CSV."
                    )
                continue
    
    def merge_data(self, traffic_df, pois_df):
        """
        Merge traffic and POI data on location_name.
        
        Args:
            traffic_df: Traffic DataFrame
            pois_df: POI DataFrame
            
        Returns:
            Merged DataFrame
        """
        logger.info("Merging traffic and POI data...")
        
        # Clean column names
        pois_df.columns = pois_df.columns.str.strip()
        traffic_df.columns = traffic_df.columns.str.strip()
        
        # Identify POI category columns
        location_info_cols = [
            'location_name', 'latitude', 'longitude', 
            'total_pois', 'pois_fetched', 'ACCESS_LOCATION',
            'raw_classifications', 'unique_classifications', 'non_zero_categories'
        ]
        
        self.poi_columns = [col for col in pois_df.columns 
                           if col not in location_info_cols]
        
        logger.info(f"Found {len(self.poi_columns)} POI category columns")
        logger.info(f"POI columns sample: {self.poi_columns[:5]}")
        
        # Merge on location_name
        merged_df = traffic_df.merge(
            pois_df[['location_name'] + self.poi_columns],
            on='location_name',
            how='left'
        )
        
        logger.info(f"Merged data shape: {merged_df.shape}")
        
        return merged_df
    
    def engineer_features(self, df):
        """
        Perform feature engineering on merged dataset.
        
        Args:
            df: Merged DataFrame
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Engineering features...")
        
        df = df.copy()
        
        # Encode severity as numeric
        severity_mapping = {
            'LOW': 0, 'MODERATE': 1, 'HIGH': 2, 
            'SEVERE': 3, 'CLOSED': 4, 'UNKNOWN': -1
        }
        if 'severity' in df.columns:
            df['severity_encoded'] = df['severity'].map(severity_mapping).fillna(-1)
        
        # Cyclical encoding for hour
        hour_col = 'hour_label' if 'hour_label' in df.columns else 'hour'
        if hour_col in df.columns:
            df['hour_sin'] = np.sin(2 * np.pi * df[hour_col] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df[hour_col] / 24)
            if hour_col == 'hour_label' and 'hour' not in df.columns:
                df['hour'] = df['hour_label']
        
        # One-hot encode frc
        if 'frc' in df.columns:
            df['frc_encoded'] = self.frc_encoder.fit_transform(df['frc'].astype(str))
            frc_dummies = pd.get_dummies(df['frc'], prefix='frc')
            df = pd.concat([df, frc_dummies], axis=1)
        
        # Normalize POI values
        normalized_cols = {}
        
        for col in self.poi_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                col_max = df[col].max()
                col_min = df[col].min()
                
                self.poi_min_max[col] = {'min': float(col_min), 'max': float(col_max)}
                
                if col_max > col_min:
                    normalized_cols[f'{col}_normalized'] = (df[col] - col_min) / (col_max - col_min)
                else:
                    normalized_cols[f'{col}_normalized'] = 0.0
                    self.poi_min_max[col] = {'min': 0.0, 'max': 1.0}
        
        if normalized_cols:
            normalized_df = pd.DataFrame(normalized_cols, index=df.index)
            df = pd.concat([df, normalized_df], axis=1)
        
        # Derived features
        poi_sum_cols = [col for col in self.poi_columns if col in df.columns]
        if poi_sum_cols:
            df['total_poi_count'] = df[poi_sum_cols].sum(axis=1)
            df['poi_diversity'] = (df[poi_sum_cols] > 0).sum(axis=1)
        
        df = df.fillna(0)
        
        logger.info("Feature engineering complete")
        logger.info(f"Total features after engineering: {df.shape[1]}")
        
        return df
    
    def prepare_training_data(self, df, target_columns=None):
        """
        Prepare feature and target matrices for training.
        
        Args:
            df: DataFrame with engineered features
            target_columns: List of target column names
            
        Returns:
            Tuple of (X_scaled, targets_df, feature_names)
        """
        logger.info("Preparing training data...")
        
        if target_columns is None:
            target_columns = [
                'current_speed',
                'free_flow_speed',
                'speed_reduction',
                'congestion_ratio',
                'severity_encoded'
            ]
        
        # Encode location names
        df['location_encoded'] = self.location_encoder.fit_transform(df['location_name'])
        
        # Select feature columns
        feature_cols = ['location_encoded', 'hour', 'hour_sin', 'hour_cos']
        
        # Add normalized POI columns
        normalized_poi_cols = [f'{col}_normalized' for col in self.poi_columns 
                              if f'{col}_normalized' in df.columns]
        feature_cols.extend(normalized_poi_cols)
        
        # Add derived features
        if 'total_poi_count' in df.columns:
            feature_cols.append('total_poi_count')
        if 'poi_diversity' in df.columns:
            feature_cols.append('poi_diversity')
        
        # Add frc one-hot columns
        frc_cols = [col for col in df.columns if col.startswith('frc_')]
        feature_cols.extend(frc_cols)
        
        self.feature_column_order = feature_cols
        
        # Create feature matrix
        X = df[feature_cols].values
        
        # Create target matrix
        missing_targets = [col for col in target_columns if col not in df.columns]
        if missing_targets:
            raise ValueError(f"Missing target columns: {missing_targets}")
        
        targets_df = df[target_columns].copy()
        
        # Fill NaN values
        X = np.nan_to_num(X, nan=0.0)
        targets_df = targets_df.fillna(0.0)
        
        # Fit scaler
        X_scaled = self.scaler.fit_transform(X)
        self.is_fitted = True
        
        logger.info(f"Feature matrix shape: {X_scaled.shape}")
        logger.info(f"Targets shape: {targets_df.shape}")
        
        return X_scaled, targets_df, feature_cols
    
    def get_preprocessor_state(self):
        """Get preprocessor state for saving"""
        return {
            'scaler': self.scaler,
            'location_encoder': self.location_encoder,
            'frc_encoder': self.frc_encoder,
            'poi_columns': self.poi_columns,
            'poi_min_max': self.poi_min_max,
            'feature_column_order': getattr(self, 'feature_column_order', []),
            'is_fitted': self.is_fitted
        }
    
    def set_preprocessor_state(self, state):
        """Restore preprocessor state"""
        self.scaler = state['scaler']
        self.location_encoder = state['location_encoder']
        self.frc_encoder = state['frc_encoder']
        self.poi_columns = state['poi_columns']
        self.poi_min_max = state.get('poi_min_max', {})
        self.feature_column_order = state.get('feature_column_order', [])
        self.is_fitted = state['is_fitted']
        logger.info(f"Preprocessor state restored")

