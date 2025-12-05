"""
Complete Example: Using Visualization APIs in Your Application

This file demonstrates practical examples of how to use all visualization
endpoints in real-world scenarios.
"""

import requests
import json
from datetime import datetime, timedelta
import pandas as pd


class VisualizationClient:
    """Client for consuming visualization APIs."""
    
    def __init__(self, base_url="http://localhost:8000/api/viz"):
        self.base_url = base_url
        self.session = requests.Session()
    
    # ==================== HEATMAP EXAMPLES ====================
    
    def example_1_view_current_traffic_heatmap(self):
        """Example 1: Get and display current hour traffic heatmap."""
        print("\n" + "="*60)
        print("EXAMPLE 1: View Current Traffic Heatmap")
        print("="*60)
        
        current_hour = datetime.now().hour
        
        # Fetch heatmap for current hour
        response = self.session.get(f"{self.base_url}/heatmap/hourly/{current_hour}")
        data = response.json()
        
        print(f"\n📍 Heatmap for Hour: {data['timestamp']}")
        print(f"   Data points: {data['count']}")
        print(f"   Coverage: {len(data['points'])} zones")
        
        # Show top 3 hottest zones
        print(f"\n🔥 Top 3 Hottest Zones:")
        sorted_points = sorted(data['points'], key=lambda x: x['severity'], reverse=True)
        for i, point in enumerate(sorted_points[:3], 1):
            print(f"   {i}. {point['location']:20} - Severity: {point['severity']:.2f}/3.0")
    
    def example_2_compare_hours(self):
        """Example 2: Compare traffic across different hours."""
        print("\n" + "="*60)
        print("EXAMPLE 2: Compare Traffic Across Hours")
        print("="*60)
        
        hours_to_compare = [8, 12, 18, 22]  # Morning, noon, evening, night
        
        comparison_data = {}
        for hour in hours_to_compare:
            response = self.session.get(f"{self.base_url}/heatmap/hourly/{hour}")
            data = response.json()
            
            # Calculate statistics
            severities = [p['severity'] for p in data['points']]
            avg_severity = sum(severities) / len(severities) if severities else 0
            max_severity = max(severities) if severities else 0
            
            comparison_data[hour] = {
                'timestamp': data['timestamp'],
                'avg_severity': avg_severity,
                'max_severity': max_severity,
                'point_count': data['count']
            }
        
        # Display comparison
        print(f"\n📊 Hour Comparison:")
        print(f"{'Hour':<10} {'Avg Severity':<15} {'Max Severity':<15} {'Points':<10}")
        print("-" * 50)
        for hour, stats in comparison_data.items():
            print(f"{stats['timestamp']:<10} {stats['avg_severity']:<15.2f} {stats['max_severity']:<15.2f} {stats['point_count']:<10}")
    
    def example_3_find_best_time_to_travel(self):
        """Example 3: Find the best time to travel in a day."""
        print("\n" + "="*60)
        print("EXAMPLE 3: Find Best Time to Travel")
        print("="*60)
        
        # Get timeline for a specific location
        response = self.session.get(f"{self.base_url}/timeline?location=Koregaon%20Park")
        data = response.json()
        
        print(f"\n📍 Location: {data['location']}")
        print(f"   Peak Hour: {data['peak_hour']:02d}:00")
        print(f"   Quiet Hour: {data['quiet_hour']:02d}:00")
        
        # Find best 3 hours
        sorted_timeline = sorted(data['timeline'], key=lambda x: x['severity'])
        print(f"\n✅ Best 3 Times to Travel:")
        for i, entry in enumerate(sorted_timeline[:3], 1):
            print(f"   {i}. {entry['timestamp']} - Severity: {entry['severity_label']:10} - Congestion: {entry['congestion_ratio']:.0%}")
    
    # ==================== ZONE ANALYTICS EXAMPLES ====================
    
    def example_4_zone_deep_dive(self):
        """Example 4: Deep dive into a specific zone."""
        print("\n" + "="*60)
        print("EXAMPLE 4: Zone Deep Dive Analysis")
        print("="*60)
        
        # Get all zones
        response = self.session.get(f"{self.base_url}/zones/analytics")
        analytics = response.json()
        
        # Pick first zone and analyze deeply
        first_zone = list(analytics['zones'].values())[0]
        zone_name = first_zone['location']
        
        print(f"\n🔍 Zone: {zone_name}")
        print(f"   Coordinates: ({first_zone['coordinates']['lat']:.4f}, {first_zone['coordinates']['lon']:.4f})")
        
        print(f"\n📊 Traffic Statistics:")
        print(f"   Average Severity: {first_zone['avg_severity']:.2f}/3.0")
        print(f"   Average Congestion: {first_zone['avg_congestion']:.0%}")
        
        print(f"\n⏰ Peak Hours:")
        print(f"   Worst Hour: {first_zone['worst_time']} (Severity: {first_zone['peak_severity']:.2f})")
        print(f"   Best Hour: {first_zone['best_visit_time']} (Severity: {first_zone['quiet_severity']:.2f})")
        
        print(f"\n🌅 Rush Hour Analysis:")
        print(f"   Morning (6-9 AM): {first_zone['morning_congestion']:.0%}")
        print(f"   Evening (5-8 PM): {first_zone['evening_congestion']:.0%}")
        
        print(f"\n💡 Recommendation:")
        print(f"   {first_zone['recommendation']}")
    
    def example_5_find_best_zones(self):
        """Example 5: Find the best zones for different activities."""
        print("\n" + "="*60)
        print("EXAMPLE 5: Find Best Zones by Activity")
        print("="*60)
        
        response = self.session.get(f"{self.base_url}/zones/analytics")
        analytics = response.json()
        zones = list(analytics['zones'].values())
        
        # Find quietest zones (for work/study)
        quietest = sorted(zones, key=lambda x: x['quiet_severity'])[:3]
        print(f"\n📚 Best Zones for Work/Study (Quietest):")
        for i, zone in enumerate(quietest, 1):
            print(f"   {i}. {zone['location']:25} - Quiet Hour: {zone['best_visit_time']}")
        
        # Find zones with good evening activity (for dining/entertainment)
        best_evening = sorted(zones, key=lambda x: x['evening_congestion'], reverse=True)[:3]
        print(f"\n🎭 Best Zones for Evening Activities:")
        for i, zone in enumerate(best_evening, 1):
            print(f"   {i}. {zone['location']:25} - Evening Congestion: {zone['evening_congestion']:.0%}")
        
        # Find zones with lowest average severity (for safe travel)
        safest = sorted(zones, key=lambda x: x['avg_severity'])[:3]
        print(f"\n✅ Safest Zones (Lowest Severity):")
        for i, zone in enumerate(safest, 1):
            print(f"   {i}. {zone['location']:25} - Avg Severity: {zone['avg_severity']:.2f}/3.0")
    
    # ==================== PREDICTION EXAMPLES ====================
    
    def example_6_predict_future_traffic(self):
        """Example 6: Get traffic predictions for next few hours."""
        print("\n" + "="*60)
        print("EXAMPLE 6: Predict Future Traffic (Next 3 Hours)")
        print("="*60)
        
        response = self.session.get(f"{self.base_url}/predict/heatmap?hours_ahead=3")
        predictions = response.json()
        
        print(f"\n🔮 Traffic Predictions")
        print(f"   Current Hour: {predictions['current_hour']:02d}:00")
        print(f"   Model Confidence: {predictions['confidence']:.0%}")
        
        print(f"\n📈 Predicted Severity by Hour:")
        for hour, pred_data in predictions['predictions'].items():
            print(f"   {pred_data['timestamp']}: Avg Severity {pred_data['avg_severity']:.2f}/3.0")
        
        print(f"\n💡 Recommendation:")
        best_pred = min(predictions['predictions'].values(), key=lambda x: x['avg_severity'])
        worst_pred = max(predictions['predictions'].values(), key=lambda x: x['avg_severity'])
        print(f"   Best time to travel: {best_pred['timestamp']}")
        print(f"   Worst time to travel: {worst_pred['timestamp']}")
    
    # ==================== MOBILITY EXAMPLES ====================
    
    def example_7_understand_mobility_patterns(self):
        """Example 7: Understand city-wide mobility patterns."""
        print("\n" + "="*60)
        print("EXAMPLE 7: Understand Mobility Patterns")
        print("="*60)
        
        response = self.session.get(f"{self.base_url}/mobility/patterns")
        patterns = response.json()
        
        print(f"\n🚗 Peak Mobility Hours (High Traffic):")
        for pattern in patterns['peak_mobility_hours']:
            print(f"   {pattern['timestamp']} - Congestion: {pattern['congestion']:.0%}")
        
        print(f"\n🚶 Quiet Hours (Low Traffic):")
        for pattern in patterns['quiet_hours']:
            print(f"   {pattern['timestamp']} - Congestion: {pattern['congestion']:.0%}")
        
        print(f"\n⏰ Rush Hours (Standard Definition):")
        print(f"   {', '.join([f'{h:02d}:00' for h in patterns['rush_hours']])}")
        
        print(f"\n✨ Off-Peak Hours (Best for Non-urgent Travel):")
        off_peak_formatted = [f'{h:02d}:00' for h in patterns['off_peak']]
        print(f"   {', '.join(off_peak_formatted[:8])}...")
    
    # ==================== ROUTE EXAMPLES ====================
    
    def example_8_plan_optimal_route(self):
        """Example 8: Plan optimal routes with timing."""
        print("\n" + "="*60)
        print("EXAMPLE 8: Plan Optimal Route")
        print("="*60)
        
        response = self.session.get(f"{self.base_url}/routes/analytics")
        routes = response.json()['routes']
        
        print(f"\n🗺️  Available Routes: {len(routes)}")
        
        # Show all routes with difficulty
        print(f"\n📋 Route Recommendations:")
        for route in routes:
            difficulty_emoji = "🟢" if route['difficulty'] < 1.5 else "🟡" if route['difficulty'] < 2.5 else "🔴"
            print(f"   {route['from_location']} → {route['to_location']}")
            print(f"      {difficulty_emoji} Difficulty: {route['difficulty_label']}")
            print(f"      ⏱️  Est. Time: {route['avg_time']} min")
            print(f"      🕐 Best Time: {route['best_time']}")
        
        # Find easiest route
        easiest = min(routes, key=lambda x: x['difficulty'])
        print(f"\n✅ Easiest Route:")
        print(f"   {easiest['from_location']} → {easiest['to_location']}")
        print(f"   Travel Time: {easiest['avg_time']} minutes")
    
    # ==================== SUMMARY EXAMPLES ====================
    
    def example_9_dashboard_summary(self):
        """Example 9: Get complete dashboard summary."""
        print("\n" + "="*60)
        print("EXAMPLE 9: Dashboard Summary")
        print("="*60)
        
        response = self.session.get(f"{self.base_url}/summary")
        summary = response.json()
        
        print(f"\n📊 Overall Statistics:")
        print(f"   Zones Monitored: {summary['summary']['total_zones']}")
        print(f"   Avg Traffic Severity: {summary['summary']['avg_traffic_severity']:.2f}/3.0")
        print(f"   Data Points: {summary['summary']['heatmap_coverage']}")
        print(f"   Last Updated: {summary['summary']['data_updated']}")
        
        print(f"\n🔥 Top 3 Congested Zones:")
        for i, (name, zone) in enumerate(summary['top_5_congested_zones'][:3], 1):
            print(f"   {i}. {name}: {zone['avg_congestion']:.0%} congestion")
        
        print(f"\n✅ Best 3 Zones to Visit:")
        for i, (name, zone) in enumerate(summary['best_visit_zones'][:3], 1):
            print(f"   {i}. {name}: Best at {zone['best_visit_time']}")
    
    # ==================== COMPARISON EXAMPLES ====================
    
    def example_10_compare_zones_multidimensional(self):
        """Example 10: Compare zones across multiple dimensions."""
        print("\n" + "="*60)
        print("EXAMPLE 10: Multi-Dimensional Zone Comparison")
        print("="*60)
        
        response = self.session.get(f"{self.base_url}/comparison")
        comparison = response.json()
        
        print(f"\n📊 Comparing {len(comparison['zones'])} zones across {len(comparison['metrics'])} metrics")
        print(f"   Metrics: {', '.join(comparison['metrics'])}")
        
        print(f"\n📈 Top Zone Scores:")
        for zone in comparison['zones'][:5]:
            print(f"\n   {zone['zone']}:")
            print(f"      Traffic Severity: {zone['traffic_severity']:.2f}/3.0")
            print(f"      Congestion: {zone['congestion']:.0%}")
            print(f"      Walkability: {zone['walkability']:.1f}/10")
            print(f"      Safety: {zone['safety_score']:.1f}/10")
            print(f"      Amenities: {zone['amenities']:.1f}")
    
    # ==================== RUN ALL EXAMPLES ====================
    
    def run_all_examples(self):
        """Run all examples sequentially."""
        examples = [
            self.example_1_view_current_traffic_heatmap,
            self.example_2_compare_hours,
            self.example_3_find_best_time_to_travel,
            self.example_4_zone_deep_dive,
            self.example_5_find_best_zones,
            self.example_6_predict_future_traffic,
            self.example_7_understand_mobility_patterns,
            self.example_8_plan_optimal_route,
            self.example_9_dashboard_summary,
            self.example_10_compare_zones_multidimensional,
        ]
        
        for example in examples:
            try:
                example()
            except Exception as e:
                print(f"\n❌ Error in {example.__name__}: {str(e)}")
        
        print("\n" + "="*60)
        print("✅ All Examples Completed!")
        print("="*60)


# ==================== USAGE ====================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║   Visualization API Examples - Urban Traffic Analytics      ║
    ║   Run this to see all visualization endpoints in action     ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Make sure API server is running
    print("⏳ Connecting to API server at http://localhost:8000/api/viz...")
    
    try:
        client = VisualizationClient()
        
        # Quick health check
        response = requests.get("http://localhost:8000/api/viz/health")
        if response.status_code == 200:
            print("✅ API server is running!\n")
            
            # Run examples
            choice = input("Select option:\n1. Run all examples\n2. Run specific example\n\nChoice (1 or 2): ").strip()
            
            if choice == "1":
                client.run_all_examples()
            elif choice == "2":
                examples = [
                    client.example_1_view_current_traffic_heatmap,
                    client.example_2_compare_hours,
                    client.example_3_find_best_time_to_travel,
                    client.example_4_zone_deep_dive,
                    client.example_5_find_best_zones,
                    client.example_6_predict_future_traffic,
                    client.example_7_understand_mobility_patterns,
                    client.example_8_plan_optimal_route,
                    client.example_9_dashboard_summary,
                    client.example_10_compare_zones_multidimensional,
                ]
                
                for i, ex in enumerate(examples, 1):
                    print(f"{i}. {ex.__doc__}")
                
                ex_choice = int(input("\nEnter example number: "))
                examples[ex_choice - 1]()
        else:
            print("❌ API server not responding. Start it with:")
            print("   python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nMake sure the API server is running!")
