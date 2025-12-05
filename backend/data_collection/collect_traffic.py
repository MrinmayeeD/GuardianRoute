"""
Traffic Data Collection Script
Collects real-time traffic data from TomTom Traffic API for 18 hours (6 AM to 12 AM)
Saves data to CSV format only.
"""

import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime
import os
from pathlib import Path
import json

# Configuration
API_KEY = "d5TWC3g2TRMlQr6VQvk0h5pfdQGrqCtA"  # Replace with your API key
TRAFFIC_API_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

# API Parameters
API_PARAMS = {
    'unit': 'KMPH',
    'thickness': 10,
    'openLr': False
}

# Paths
DATA_DIR = Path(__file__).parent / 'data'
LOCATIONS_FILE = Path(__file__).parent / 'data_collection' / '100_locations_with_coords.csv'
OUTPUT_FILE = DATA_DIR / 'traffic.csv'


def get_traffic_flow(lat, lon):
    """
    Fetch real-time traffic flow data from TomTom Traffic API
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        JSON response from API or None if error
    """
    params = {
        'key': API_KEY,
        'point': f'{lat},{lon}',
        **API_PARAMS
    }
    
    try:
        response = requests.get(TRAFFIC_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  ✗ API Error: {str(e)}")
        return None
    except Exception as e:
        print(f"  ✗ Unexpected Error: {str(e)}")
        return None


def calculate_traffic_severity(traffic_data):
    """
    Improved severity calculation using speed reduction + travel delay + congestion ratio
    Uses composite scoring approach for more accurate severity classification.
    
    Args:
        traffic_data: JSON response from Traffic API
    
    Returns:
        Dictionary with traffic metrics and severity
    """
    if not traffic_data or 'flowSegmentData' not in traffic_data:
        return {
            'severity': 'UNKNOWN',
            'congestion_ratio': 0,
            'speed_reduction': 0,
            'travel_delay_pct': 0,
            'current_speed': 0,
            'free_flow_speed': 0,
            'road_closure': False,
            'current_travel_time': 0,
            'free_flow_travel_time': 0,
            'confidence': 0,
            'frc': 'UNKNOWN'
        }

    fd = traffic_data["flowSegmentData"]
    current_speed = fd.get("currentSpeed", 0)
    free_flow_speed = fd.get("freeFlowSpeed", 1)
    road_closure = fd.get("roadClosure", False)

    current_tt = fd.get("currentTravelTime", 1)
    free_tt = fd.get("freeFlowTravelTime", 1)

    # Derived metrics
    congestion_ratio = current_speed / free_flow_speed if free_flow_speed > 0 else 0
    speed_reduction = (1 - congestion_ratio) * 100            # % slowdown
    travel_delay_pct = ((current_tt - free_tt) / free_tt) * 100 if free_tt > 0 else 0

    # Composite score (0–3 scale)
    score = 0
    if speed_reduction > 20: 
        score += 1
    if travel_delay_pct > 25: 
        score += 1
    if congestion_ratio < 0.6: 
        score += 1

    # Severity classification
    if road_closure:
        severity = "CLOSED"
    elif score == 0:
        severity = "LOW"
    elif score == 1:
        severity = "MODERATE"
    elif score == 2:
        severity = "HIGH"
    else:  # score == 3
        severity = "SEVERE"

    return {
        'severity': severity,
        'congestion_ratio': round(congestion_ratio, 2),
        'speed_reduction': round(speed_reduction, 2),
        'travel_delay_pct': round(travel_delay_pct, 2),
        'current_speed': current_speed,
        'free_flow_speed': free_flow_speed,
        'road_closure': road_closure,
        'current_travel_time': current_tt,
        'free_flow_travel_time': free_tt,
        'confidence': fd.get("confidence", 0),
        'frc': fd.get("frc", "UNKNOWN")
    }


def collect_18hour_traffic_data(locations_df, output_csv=None, start_hour=6):
    """
    Collect real-time traffic data for all locations every hour for 18 hours (6 AM to 12 AM)
    Saves to CSV format only.
    
    Args:
        locations_df: DataFrame with location data
        output_csv: Output CSV filename (default: data/traffic.csv)
        start_hour: Starting hour (default 6 for 6 AM)
    
    Returns:
        DataFrame with traffic data for all locations across 18 hours
    """
    if output_csv is None:
        output_csv = OUTPUT_FILE
    
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize or load existing data from CSV
    if output_csv.exists():
        print(f"⚠️  File {output_csv} already exists. Loading existing data...")
        try:
            existing_df = pd.read_csv(output_csv)
            completed_hours = existing_df['hour_label'].unique().tolist()
            all_results = existing_df.to_dict('records')
            print(f"   Loaded {len(existing_df)} existing records")
            print(f"   Completed hours: {sorted(completed_hours)}")
        except Exception as e:
            print(f"   Error loading existing data: {str(e)}")
            all_results = []
            completed_hours = []
    else:
        all_results = []
        completed_hours = []
    
    print(f"\n🚀 Starting 18-hour traffic data collection")
    print(f"   Start hour: {start_hour} AM")
    print(f"   End hour: 12 AM (midnight)")
    print(f"   Output file: {output_csv}")
    print(f"   Total hours: 18 (6 AM to 12 AM)")
    print(f"=" * 80)
    
    # Collection time tracking
    collection_start = datetime.now()
    
    # Collect data for 18 hours (6 AM to 12 AM = hours 6 to 23)
    for hour_index in range(18):
        current_hour_label = (start_hour + hour_index) % 24
        
        # Skip if already collected
        if current_hour_label in completed_hours:
            print(f"\n⏭️  Hour {current_hour_label} already collected. Skipping...")
            continue
        
        print(f"\n{'='*80}")
        print(f"📊 HOUR {current_hour_label} ({hour_index + 1}/18)")
        print(f"   Collection started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        hour_results = []
        locations_processed = 0
        locations_failed = 0
        api_error_detected = False
        
        # Collect data for all locations for this hour
        for idx, row in locations_df.iterrows():
            location_name = row['location_name']
            lat = row.get('latitude')
            lon = row.get('longitude')
            
            # Skip if no coordinates
            if pd.isna(lat) or pd.isna(lon):
                print(f"⚠️  [{idx+1}/{len(locations_df)}] Skipping {location_name} - no coordinates")
                locations_failed += 1
                continue
            
            print(f"🚗 [{idx+1}/{len(locations_df)}] {location_name}")
            
            try:
                # Fetch traffic data
                traffic_response = get_traffic_flow(lat, lon)
                
                # Check for None response (403 or other errors)
                if traffic_response is None:
                    print(f"\n{'='*80}")
                    print(f"🛑 CRITICAL ERROR: API request failed (possibly 403 Forbidden)")
                    print(f"   Stopping data collection for Hour {current_hour_label}")
                    print(f"   Previous hours' data is preserved in the CSV file")
                    print(f"   Please check your API key or quota")
                    print(f"{'='*80}")
                    api_error_detected = True
                    break
                
                # Check for API errors in response
                if 'detailedError' in traffic_response:
                    error_code = traffic_response['detailedError'].get('code', 'Unknown')
                    error_msg = traffic_response['detailedError'].get('message', 'Unknown error')
                    
                    print(f"\n{'='*80}")
                    print(f"🛑 API ERROR: {error_code} - {error_msg}")
                    print(f"   Stopping data collection for Hour {current_hour_label}")
                    print(f"   Previous hours' data is preserved")
                    print(f"{'='*80}")
                    api_error_detected = True
                    break
                
                # Calculate traffic metrics
                traffic_metrics = calculate_traffic_severity(traffic_response)
                
                # Prepare row data with hour label and timestamp
                row_data = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'hour_label': current_hour_label,
                    'location_name': location_name,
                    'latitude': lat,
                    'longitude': lon,
                    **traffic_metrics
                }
                
                hour_results.append(row_data)
                locations_processed += 1
                
                # Print summary with new metrics
                print(f"   ✓ {traffic_metrics['severity']:8s} | "
                      f"Speed: {traffic_metrics['current_speed']:3.0f}/{traffic_metrics['free_flow_speed']:3.0f} km/h | "
                      f"Reduction: {traffic_metrics['speed_reduction']:5.1f}% | "
                      f"Delay: {traffic_metrics['travel_delay_pct']:5.1f}%")
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ✗ Unexpected error: {str(e)}")
                locations_failed += 1
                continue
        
        # Handle API error - discard this hour's data and stop
        if api_error_detected:
            print(f"\n❌ Hour {current_hour_label} data DISCARDED due to API error")
            print(f"   {locations_processed} locations were processed before error")
            print(f"   Previous data is safe in: {output_csv}")
            print(f"\n🛑 Stopping collection. Please resolve API issues before continuing.")
            break
        
        # Add this hour's results to all results (IN MEMORY) - only if no errors
        if hour_results:
            all_results.extend(hour_results)
            
            # Now save the COMPLETE dataset to CSV
            try:
                # Create DataFrame with ALL accumulated data
                complete_df = pd.DataFrame(all_results)
                
                print(f"\n💾 Saving complete dataset to CSV...")
                print(f"   Records for hour {current_hour_label}: {len(hour_results)}")
                print(f"   Total records in memory: {len(complete_df)}")
                
                # Save to CSV
                complete_df.to_csv(output_csv, index=False)
                
                print(f"✅ CSV file saved successfully!")
                print(f"   Locations processed this hour: {locations_processed}/{len(locations_df)}")
                print(f"   Locations failed: {locations_failed}")
                print(f"   Total records in CSV file: {len(complete_df)}")
                print(f"   Hours completed: {sorted(complete_df['hour_label'].unique())}")
                
            except Exception as e:
                print(f"\n❌ Error saving data to CSV for hour {current_hour_label}: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"\n⚠️  No data collected for hour {current_hour_label}")
        
        # Wait for next hour (except for last iteration)
        if hour_index < 17 and not api_error_detected:
            next_hour = (current_hour_label + 1) % 24
            print(f"\n⏳ Waiting for next hour...")
            print(f"   Next collection: Hour {next_hour}")
            time.sleep(3600)  # Wait 1 hour
    
    # Final summary
    print(f"\n{'='*80}")
    if api_error_detected:
        print(f"⚠️  DATA COLLECTION STOPPED DUE TO API ERROR")
    else:
        print(f"✅ 18-HOUR DATA COLLECTION COMPLETE")
    print(f"{'='*80}")
    
    if output_csv.exists():
        final_df = pd.read_csv(output_csv)
        total_records = len(final_df)
        hours_collected = final_df['hour_label'].nunique()
        
        print(f"   Total records: {total_records}")
        print(f"   Hours collected: {hours_collected}/18")
        print(f"   Hours: {sorted(final_df['hour_label'].unique())}")
        print(f"   File: {output_csv}")
        print(f"   Collection time: {(datetime.now() - collection_start).total_seconds() / 3600:.1f} hours")
        
        if api_error_detected:
            print(f"\n⚠️  Note: Collection stopped early due to API error")
            print(f"   Data for completed hours is safely saved")
        
        # Save summary report as JSON
        save_summary_report(final_df, output_csv.parent / 'traffic_collection_summary.json')
        
        return final_df
    else:
        print(f"   ⚠️  No data file created")
        return None


def save_summary_report(df, output_file):
    """Save collection summary as JSON"""
    summary_report = {
        'collection_details': {
            'total_records': len(df),
            'total_locations': int(df['location_name'].nunique()),
            'hours_collected': int(df['hour_label'].nunique()),
            'hours': sorted(df['hour_label'].unique().tolist()),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        'speed_metrics': {
            'avg_current_speed': round(df['current_speed'].mean(), 1),
            'avg_free_flow_speed': round(df['free_flow_speed'].mean(), 1),
            'avg_congestion_ratio': round(df['congestion_ratio'].mean(), 2),
            'avg_speed_reduction': round(df['speed_reduction'].mean(), 1),
            'avg_travel_delay_pct': round(df['travel_delay_pct'].mean(), 1)
        },
        'severity_distribution': df['severity'].value_counts().to_dict(),
        'records_per_hour': df.groupby('hour_label').size().to_dict()
    }
    
    with open(output_file, 'w') as f:
        json.dump(summary_report, f, indent=2)
    
    print(f"\n✅ Summary report saved to: {output_file}")


def analyze_traffic_data(csv_file=None):
    """
    Analyze collected traffic data and display summary statistics
    
    Args:
        csv_file: Path to traffic CSV file (default: data/traffic.csv)
    """
    if csv_file is None:
        csv_file = OUTPUT_FILE
    
    csv_file = Path(csv_file)
    
    if not csv_file.exists():
        print(f"❌ File not found: {csv_file}")
        return None
    
    df = pd.read_csv(csv_file)
    
    print("📈 18-HOUR TRAFFIC DATA SUMMARY")
    print("="*80)
    
    # Overall statistics
    print(f"\n📊 Collection Details:")
    print(f"  Total records: {len(df)}")
    print(f"  Total locations: {df['location_name'].nunique()}")
    print(f"  Hours collected: {sorted(df['hour_label'].unique())}")
    
    # Records per hour
    print(f"\n📊 Records per Hour:")
    records_per_hour = df.groupby('hour_label').size().sort_index()
    for hour, count in records_per_hour.items():
        print(f"  Hour {hour:2d}: {count:3d} records")
    
    # Traffic severity distribution
    severity_counts = df['severity'].value_counts()
    print(f"\n🚦 Overall Traffic Severity Distribution:")
    for severity, count in severity_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {severity:10s}: {count:5d} records ({percentage:5.1f}%)")
    
    # Speed statistics by hour
    print(f"\n⚡ Average Metrics by Hour:")
    hourly_stats = df.groupby('hour_label').agg({
        'current_speed': 'mean',
        'free_flow_speed': 'mean',
        'speed_reduction': 'mean',
        'travel_delay_pct': 'mean',
        'congestion_ratio': 'mean'
    }).round(1)
    print(hourly_stats.to_string())
    
    # Peak congestion hours
    print(f"\n🔴 Peak Congestion Hours (by avg speed reduction):")
    peak_hours = hourly_stats.nlargest(5, 'speed_reduction')
    for hour, row in peak_hours.iterrows():
        print(f"  Hour {hour:2d}: {row['speed_reduction']:5.1f}% reduction | "
              f"Speed: {row['current_speed']:.1f}/{row['free_flow_speed']:.1f} km/h | "
              f"Delay: {row['travel_delay_pct']:.1f}%")
    
    print("\n" + "="*80)
    
    return df


def main():
    """Main function to run traffic data collection"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect 18-hour traffic data from TomTom API')
    parser.add_argument('--start-hour', type=int, default=6, 
                       help='Starting hour (0-23), default: 6 (6 AM)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output CSV file path (default: data/traffic.csv)')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Only analyze existing data without collection')
    parser.add_argument('--api-key', type=str, default=None,
                       help='TomTom API key (overrides default)')
    
    args = parser.parse_args()
    
    # Override API key if provided
    if args.api_key:
        global API_KEY
        API_KEY = args.api_key
    
    # Analyze mode
    if args.analyze_only:
        print("📊 Analyzing existing traffic data...\n")
        analyze_traffic_data(args.output)
        return
    
    # Check if locations file exists
    if not LOCATIONS_FILE.exists():
        print(f"❌ Locations file not found: {LOCATIONS_FILE}")
        print(f"   Please ensure '100_locations_with_coords.csv' exists in data_collection folder")
        return
    
    # Load locations
    print(f"📍 Loading locations from: {LOCATIONS_FILE}")
    locations_df = pd.read_csv(LOCATIONS_FILE)
    print(f"✅ Loaded {len(locations_df)} locations\n")
    
    # Run collection
    print(f"⚠️  IMPORTANT:")
    print(f"   - This will run for approximately 18 hours")
    print(f"   - Data is saved to CSV after each hour")
    print(f"   - If interrupted, you can restart and it will skip completed hours")
    print(f"   - Press Ctrl+C to stop collection")
    print(f"\nStarting in 5 seconds...")
    time.sleep(5)
    
    try:
        traffic_df = collect_18hour_traffic_data(
            locations_df=locations_df,
            output_csv=args.output,
            start_hour=args.start_hour
        )
        
        if traffic_df is not None:
            print("\n✅ Collection completed successfully!")
            print(f"\n📊 Final Summary:")
            analyze_traffic_data(args.output)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
        print("   Existing data is preserved in CSV file")
        if OUTPUT_FILE.exists():
            print(f"   Resume by running the script again")


if __name__ == "__main__":
    main()