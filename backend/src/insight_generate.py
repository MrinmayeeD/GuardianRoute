"""
Enhanced insight generation module with comprehensive lifestyle recommendations.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InsightEngine:
    """Generates comprehensive urban insights from POI data and traffic predictions."""
    
    def __init__(self, poi_importance=None):
        self.severity_mapping = {
            0: 'LOW', 1: 'MODERATE', 2: 'HIGH', 
            3: 'SEVERE', 4: 'CLOSED', -1: 'UNKNOWN'
        }
        self.poi_importance = poi_importance or {}
    
    def identify_area_type(self, poi_data, traffic_stats):
        """Identify area type using POI composition and traffic patterns."""
        
        # Calculate POI scores
        scores = {}
        for category, value in poi_data.items():
            weight = self.poi_importance.get(category, 0.1)
            scores[category] = value * weight
        
        top_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        logger.info(f"🔍 Top 3 influential POI categories:")
        for cat, score in top_categories:
            logger.info(f"   {cat}: {score:.4f}")
        
        # Traffic context
        avg_congestion = traffic_stats.get('avg_congestion', 0)
        evening_congestion = traffic_stats.get('evening_congestion', 0)
        
        dominant_category = top_categories[0][0] if top_categories else 'MIXED'
        dominant_score = top_categories[0][1] if top_categories else 0
        second_score = top_categories[1][1] if len(top_categories) > 1 else 0
        
        dominance_ratio = dominant_score / second_score if second_score > 0 else 2.0
        is_dominant = dominance_ratio > 1.5
        
        logger.info(f"   Dominant: {dominant_category} (ratio: {dominance_ratio:.2f})")
        
        # Area type classification
        if dominant_category in ['RESIDENTIAL_ACCOMMODATION', 'HOTEL_MOTEL', 'RESIDENTIAL']:
            if poi_data.get('PARK', 0) > 0.1 and avg_congestion < 0.5:
                return {
                    'primary': 'Quiet Residential Zone',
                    'sub_category': 'Family-Friendly',
                    'vibe': '🌳 Peaceful & Green'
                }
            return {
                'primary': 'Residential Zone',
                'sub_category': 'Primarily Residential',
                'vibe': '🏠 Calm & Settled'
            }
        
        elif dominant_category in ['RESTAURANT', 'CAFE_PUB', 'ENTERTAINMENT', 'NIGHTLIFE']:
            if evening_congestion > 0.7 or is_dominant:
                return {
                    'primary': 'Hyper-Active Hub',
                    'sub_category': 'Nightlife & Entertainment',
                    'vibe': '🔥 Buzzing & Energetic'
                }
            return {
                'primary': 'Entertainment Zone',
                'sub_category': 'Dining & Events',
                'vibe': '🎭 Lively & Social'
            }
        
        elif dominant_category in ['SHOP', 'SHOPPING_CENTER', 'MARKET', 'RETAIL']:
            return {
                'primary': 'Shopping District',
                'sub_category': 'Retail & Commerce',
                'vibe': '🛍️ Consumer Hub'
            }
        
        elif dominant_category in ['COMPANY', 'BUSINESS_PARK', 'COMMERCIAL_BUILDING', 'OFFICE']:
            if is_dominant:
                return {
                    'primary': 'Business District',
                    'sub_category': 'IT Park / Corporate Hub',
                    'vibe': '💼 Work-Focused'
                }
            return {
                'primary': 'Commercial Zone',
                'sub_category': 'Mixed Commercial',
                'vibe': '🏢 Business Activities'
            }
        
        elif dominant_category in ['INDUSTRIAL_BUILDING', 'MANUFACTURING_FACILITY', 'INDUSTRIAL']:
            return {
                'primary': 'Industrial Zone',
                'sub_category': 'Freight & Logistics',
                'vibe': '🏭 Commercial Operations'
            }
        
        # Multi-category analysis
        office_score = scores.get('OFFICE', 0) + scores.get('COMPANY', 0)
        retail_score = scores.get('RETAIL', 0) + scores.get('SHOP', 0)
        residential_score = scores.get('RESIDENTIAL', 0)
        
        if office_score > 0.005 and retail_score > 0.005:
            return {
                'primary': 'Commercial Zone',
                'sub_category': 'Mixed Commercial',
                'vibe': '🏢 Business Hub'
            }
        
        if residential_score > 0.005 and retail_score > 0.005:
            return {
                'primary': 'Balanced Neighborhood',
                'sub_category': 'Residential + Retail',
                'vibe': '🏘️ Community Living'
            }
        
        return {
            'primary': 'Mixed-Use Area',
            'sub_category': 'General Urban',
            'vibe': '🌆 Diverse Activities'
        }
    
    def generate_lifestyle_insights(self, zone_classification, poi_data, traffic_stats, city_traffic_df):
        """Generate comprehensive lifestyle recommendations from traffic data."""
        zone_type = zone_classification['primary']
        
        # Extract traffic patterns by time of day
        morning_traffic = city_traffic_df[
            (city_traffic_df['hour_label'] >= 6) & 
            (city_traffic_df['hour_label'] < 12)
        ]
        afternoon_traffic = city_traffic_df[
            (city_traffic_df['hour_label'] >= 12) & 
            (city_traffic_df['hour_label'] < 18)
        ]
        evening_traffic = city_traffic_df[
            (city_traffic_df['hour_label'] >= 18) & 
            (city_traffic_df['hour_label'] < 22)
        ]
        
        morning_cong = morning_traffic['congestion_ratio'].mean() if len(morning_traffic) > 0 else 0
        afternoon_cong = afternoon_traffic['congestion_ratio'].mean() if len(afternoon_traffic) > 0 else 0
        evening_cong = evening_traffic['congestion_ratio'].mean() if len(evening_traffic) > 0 else 0
        
        # Get high severity hours - handle both string and numeric severity
        if 'new_severity_logical' in city_traffic_df.columns:
            high_severity_hours = city_traffic_df[
                city_traffic_df['new_severity_logical'].isin(['HIGH', 'VERY_HIGH', 'SEVERE'])
            ]['hour_label'].tolist()
        else:
            high_severity_hours = []
        
        insights = {
            'best_for': [],
            'avoid_if': [],
            'ideal_times': [],
            'activities': [],
            'parking_difficulty': 'Unknown',
            'walkability': 'Unknown',
            'safety_score': 0,
            'noise_level': 'Unknown'
        }
        
        # Zone-specific recommendations
        if zone_type == 'Quiet Residential Zone':
            insights.update({
                'best_for': [
                    '👨‍👩‍👧‍👦 Families with children',
                    '👴 Senior citizens',
                    '🏃 Evening walks and jogging',
                    '🧘 Peaceful living',
                    '🐕 Pet-friendly walks'
                ],
                'avoid_if': [
                    '❌ You need nightlife options',
                    '❌ You want 24/7 dining',
                    '❌ You prefer urban hustle'
                ],
                'ideal_times': [
                    f'🌅 Morning walks: 6-9 AM (congestion: {morning_cong:.0%})',
                    f'🌆 Evening strolls: 6-8 PM (congestion: {evening_cong:.0%})',
                    '🌙 Night calm after 10 PM'
                ],
                'activities': [
                    '🏞️ Park visits',
                    '🚴 Cycling',
                    '📚 Reading outdoors',
                    '🎨 Community events'
                ],
                'parking_difficulty': 'Easy',
                'walkability': 'High',
                'safety_score': 8.5,
                'noise_level': 'Low'
            })
        
        elif zone_type == 'Hyper-Active Hub':
            insights.update({
                'best_for': [
                    '🎉 Nightlife enthusiasts',
                    '🍽️ Food delivery partners',
                    '🎭 Event organizers',
                    '📸 Content creators',
                    '🎵 Live music lovers'
                ],
                'avoid_if': [
                    '❌ You prefer quiet evenings',
                    '❌ You have early morning commitments',
                    '❌ You need easy parking after 7 PM',
                    '❌ You dislike crowds'
                ],
                'ideal_times': [
                    f'🌅 Quiet mornings: 6-11 AM (congestion: {morning_cong:.0%})',
                    f'🔥 Peak nightlife: 8 PM-1 AM (congestion: {evening_cong:.0%})',
                    '⚠️ Avoid dinner rush: 7-9 PM' if evening_cong > 0.7 else '✅ Manageable evening traffic'
                ],
                'activities': [
                    '🍸 Bar hopping',
                    '🍕 Late-night dining',
                    '🎤 Karaoke nights',
                    '🎬 Movie premieres',
                    '🛒 Late shopping'
                ],
                'parking_difficulty': 'Very Hard (post 7 PM)',
                'walkability': 'Medium',
                'safety_score': 7.0,
                'noise_level': 'High (evenings)'
            })
        
        elif 'Industrial' in zone_type:
            insights.update({
                'best_for': [
                    '🚚 Logistics operations',
                    '🏭 Manufacturing',
                    '📦 Warehouse storage',
                    '🔧 Industrial services'
                ],
                'avoid_if': [
                    '❌ Residential needs',
                    '❌ Retail shopping',
                    '❌ Family outings'
                ],
                'ideal_times': [
                    f'⚠️ AVOID morning rush: 6-10 AM (congestion: {morning_cong:.0%})',
                    f'✅ Afternoon access: 2-5 PM (congestion: {afternoon_cong:.0%})',
                    '🌙 Calm post-8 PM'
                ],
                'activities': ['🏗️ Commercial operations', '🚚 Freight delivery'],
                'parking_difficulty': 'Easy (except morning rush)',
                'walkability': 'Low',
                'safety_score': 6.0,
                'noise_level': 'High (daytime)'
            })
        
        elif zone_type == 'Business District':
            insights.update({
                'best_for': [
                    '💼 Working professionals',
                    '🏢 Corporate offices',
                    '🤝 Business meetings',
                    '☕ Co-working spaces'
                ],
                'avoid_if': [
                    '❌ Weekend activities (ghost town)',
                    '❌ Evening entertainment'
                ],
                'ideal_times': [
                    f'⚠️ Morning rush: 8-10 AM (congestion: {morning_cong:.0%})',
                    f'✅ Lunch hours: 12-2 PM (congestion: {afternoon_cong:.0%})',
                    f'⚠️ Evening exit: 5-8 PM (congestion: {evening_cong:.0%})'
                ],
                'activities': ['🍴 Business lunches', '☕ Coffee meetings', '📊 Conferences'],
                'parking_difficulty': 'Hard (9 AM-6 PM)',
                'walkability': 'Medium',
                'safety_score': 8.0,
                'noise_level': 'Moderate (daytime only)'
            })
        
        elif zone_type == 'Shopping District':
            insights.update({
                'best_for': [
                    '🛍️ Shoppers',
                    '👗 Fashion enthusiasts',
                    '🍽️ Food courts',
                    '👨‍👩‍👧 Weekend family outings'
                ],
                'avoid_if': [
                    '❌ Weekends (very crowded)',
                    '❌ Sale seasons'
                ],
                'ideal_times': [
                    f'✅ Weekday mornings: 10 AM-12 PM (congestion: {morning_cong:.0%})',
                    f'⚠️ Afternoon crowds: 2-6 PM (congestion: {afternoon_cong:.0%})',
                    '🌙 Late evening: post-8 PM (shops closing)'
                ],
                'activities': ['🛒 Retail therapy', '🍕 Food court dining', '🎬 Movies', '☕ Café hopping'],
                'parking_difficulty': 'Hard (weekends)',
                'walkability': 'Medium',
                'safety_score': 7.5,
                'noise_level': 'Moderate-High'
            })
        
        elif zone_type == 'Balanced Neighborhood':
            insights.update({
                'best_for': [
                    '🏡 Families',
                    '🏫 Parents with school kids',
                    '🏥 Healthcare access',
                    '🛒 Daily shopping'
                ],
                'avoid_if': ['❌ You want nightlife'],
                'ideal_times': [
                    f'✅ Morning errands: 8-11 AM (congestion: {morning_cong:.0%})',
                    f'🛒 Afternoon shopping: 2-5 PM (congestion: {afternoon_cong:.0%})',
                    f'🌆 Calm evenings post-7 PM (congestion: {evening_cong:.0%})'
                ],
                'activities': ['🏫 School drop-offs', '🛒 Grocery shopping', '🏥 Medical visits', '🍽️ Family dining'],
                'parking_difficulty': 'Moderate',
                'walkability': 'High',
                'safety_score': 8.5,
                'noise_level': 'Low-Moderate'
            })
        
        else:
            insights.update({
                'best_for': [f'🏙️ {zone_type} activities'],
                'ideal_times': [
                    f'Morning: {morning_cong:.0%} congestion',
                    f'Afternoon: {afternoon_cong:.0%} congestion',
                    f'Evening: {evening_cong:.0%} congestion'
                ],
                'parking_difficulty': 'Moderate',
                'walkability': 'Medium',
                'safety_score': 7.0,
                'noise_level': 'Moderate'
            })
        
        return insights
    
    def calculate_comprehensive_scores(self, poi_counts, city_traffic_df):
        """Calculate lifestyle scores from POI data and traffic patterns."""
        
        avg_congestion = city_traffic_df['congestion_ratio'].mean()
        traffic_factor = 1 - avg_congestion
        
        # Normalize POI counts
        park_norm = min(1.0, poi_counts.get('PARK_RECREATION_AREA', 0) / 5)
        restaurant_norm = min(1.0, poi_counts.get('RESTAURANT', 0) / 20)
        retail_norm = min(1.0, poi_counts.get('SHOP', 0) / 30)
        entertainment_norm = min(1.0, poi_counts.get('ENTERTAINMENT', 0) / 10)
        office_norm = min(1.0, poi_counts.get('COMPANY', 0) / 20)
        healthcare_norm = min(1.0, poi_counts.get('HOSPITAL_POLYCLINIC', 0) / 5)
        education_norm = min(1.0, poi_counts.get('SCHOOL', 0) / 5)
        
        scores = {
            'walkability_score': round((park_norm * 0.3 + restaurant_norm * 0.2 + retail_norm * 0.15 + traffic_factor * 0.35) * 10, 1),
            'nightlife_score': round((entertainment_norm * 0.6 + restaurant_norm * 0.4) * 10, 1),
            'parking_ease_score': round(traffic_factor * 10, 1),
            'quiet_score': round((1 - min(1.0, (office_norm + retail_norm + entertainment_norm) / 3)) * 10, 1),
            'commute_friendliness': round(traffic_factor * 10, 1),
            'dining_options': round(min(10.0, restaurant_norm * 10), 1),
            'shopping_score': round(min(10.0, retail_norm * 10), 1),
            'healthcare_access': round(min(10.0, healthcare_norm * 10), 1),
            'education_access': round(min(10.0, education_norm * 10), 1),
            'family_friendliness': round((park_norm * 0.3 + education_norm * 0.3 + healthcare_norm * 0.2 + traffic_factor * 0.2) * 10, 1),
            'business_suitability': round(min(10.0, office_norm * 10), 1)
        }
        
        return scores
    
    def generate_summary(self, city_traffic_df, zone_classification):
        """Generate natural language summary."""
        zone_type = zone_classification['primary']
        
        morning_traffic = city_traffic_df[(city_traffic_df['hour_label'] >= 6) & (city_traffic_df['hour_label'] < 12)]
        evening_traffic = city_traffic_df[(city_traffic_df['hour_label'] >= 18) & (city_traffic_df['hour_label'] < 22)]
        
        morning_avg_cong = morning_traffic['congestion_ratio'].mean() if len(morning_traffic) > 0 else 0
        evening_avg_cong = evening_traffic['congestion_ratio'].mean() if len(evening_traffic) > 0 else 0
        
        # Count high severity hours
        if 'new_severity_logical' in city_traffic_df.columns:
            high_traffic_hours = len(city_traffic_df[city_traffic_df['new_severity_logical'].isin(['HIGH', 'VERY_HIGH', 'SEVERE'])])
        else:
            high_traffic_hours = 0
        
        summaries = {
            'Quiet Residential Zone': f"🌳 This peaceful residential area maintains low traffic throughout the day. Morning: {morning_avg_cong:.0%}, Evening: {evening_avg_cong:.0%}. Ideal for families seeking tranquility.",
            'Business District': f"💼 Office-heavy district with rush hour peaks. Morning: {morning_avg_cong:.0%}, Evening: {evening_avg_cong:.0%}. {high_traffic_hours}h of high traffic during commute.",
            'Hyper-Active Hub': f"🔥 Hyper-active hub with {high_traffic_hours}h of heavy traffic. Evening peak: {evening_avg_cong:.0%}. Nightlife hotspot - parking very limited post-7PM.",
            'Shopping District': f"🛍️ Retail-focused area peaking during afternoons. {high_traffic_hours} busy hours. Evening: {evening_avg_cong:.0%}.",
            'Balanced Neighborhood': f"🏘️ Balanced area with residential, retail, and offices. Morning: {morning_avg_cong:.0%}, Evening: {evening_avg_cong:.0%}. Good walkability."
        }
        
        return summaries.get(zone_type, f"This {zone_type} has moderate urban activity with {high_traffic_hours}h increased traffic.")
    
    def generate_insights(self, location_name, poi_counts, city_traffic_df):
        """Generate COMPREHENSIVE insights for a location."""
        logger.info(f"🎯 Generating comprehensive insights for {location_name}...")
        
        # Normalize POI data
        max_vals = {'PARK': 10, 'RESTAURANT': 50, 'SHOP': 100, 'COMPANY': 50, 
                   'ENTERTAINMENT': 20, 'RESIDENTIAL': 50, 'INDUSTRIAL': 15}
        
        poi_normalized = {}
        for key, value in poi_counts.items():
            max_val = max_vals.get(key, 50)
            poi_normalized[key] = min(1.0, value / max_val)
        
        # Traffic statistics
        traffic_stats = {
            'avg_congestion': city_traffic_df['congestion_ratio'].mean(),
            'morning_congestion': city_traffic_df[
                (city_traffic_df['hour_label'] >= 6) & 
                (city_traffic_df['hour_label'] < 12)
            ]['congestion_ratio'].mean(),
            'evening_congestion': city_traffic_df[
                (city_traffic_df['hour_label'] >= 18) & 
                (city_traffic_df['hour_label'] < 22)
            ]['congestion_ratio'].mean()
        }
        
        zone_classification = self.identify_area_type(poi_normalized, traffic_stats)
        lifestyle_insights = self.generate_lifestyle_insights(zone_classification, poi_normalized, traffic_stats, city_traffic_df)
        comprehensive_scores = self.calculate_comprehensive_scores(poi_counts, city_traffic_df)
        summary = self.generate_summary(city_traffic_df, zone_classification)
        
        logger.info(f"✅ Classification: {zone_classification['primary']} ({zone_classification['vibe']})")
        
        return {
            'zone_classification': zone_classification,
            'summary': summary,
            'lifestyle_insights': lifestyle_insights,
            'scores': comprehensive_scores,
            'poi_breakdown': poi_counts,
            'traffic_stats': {k: round(v, 3) for k, v in traffic_stats.items()}
        }


# For testing
if __name__ == "__main__":
    # Test with sample data
    poi_counts = {
        'SHOP': 15,
        'RESTAURANT': 20,
        'PARK': 5,
        'PUBLIC_TRANSPORT_STOP': 10,
        'HOSPITAL_POLYCLINIC': 2
    }
    
    # Mock traffic data
    city_traffic_df = pd.DataFrame({
        'location_name': ['Location A', 'Location B'],
        'hour_label': [8, 9],
        'congestion_ratio': [0.5, 0.6],
        'new_severity_logical': ['LOW', 'MODERATE']
    })
    
    engine = InsightEngine()
    insights = engine.generate_insights('Test Location', poi_counts, city_traffic_df)
    
    print("Zone:", insights['zone_classification'])
    print("Summary:", insights['summary'])
    print("Scores:", insights['scores'])
