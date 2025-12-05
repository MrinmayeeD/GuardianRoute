import requests
import pandas as pd
import urllib.parse
import time

class CoordinateExtractor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.geocode_base_url = "https://api.tomtom.com/search/2/geocode"
    
    def get_coordinates_from_location(self, location_name):
        """Get latitude and longitude from location name"""
        # URL encode the location name
        encoded_location = urllib.parse.quote(location_name)
        url = f"{self.geocode_base_url}/{encoded_location}.json"
        params = {'key': self.api_key, 'limit': 1}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results') and len(data['results']) > 0:
                position = data['results'][0]['position']
                return position['lat'], position['lon']
            else:
                print(f"No coordinates found for {location_name}")
                return None, None
        except Exception as e:
            print(f"Error geocoding {location_name}: {str(e)}")
            return None, None
    
    def load_locations_from_csv(self, csv_path='100_locations.csv'):
        """Load locations from CSV file"""
        try:
            df = pd.read_csv(csv_path)
            
            # Get location names from the CSV
            if 'location_name' in df.columns:
                locations = df['location_name'].tolist()
                print(f"✓ Loaded {len(locations)} locations from {csv_path}")
                return locations
            else:
                print(f"❌ Error: 'location_name' column not found in {csv_path}")
                return None
                
        except FileNotFoundError:
            print(f"❌ Error: {csv_path} not found")
            return None
        except Exception as e:
            print(f"❌ Error reading CSV: {str(e)}")
            return None
    
    def create_csv_with_coordinates(self, input_csv='100_locations.csv', output_csv='100_locations_with_coords.csv'):
        """Create CSV file with locations and their coordinates"""
        print("🚀 Creating locations CSV with coordinates...")
        print(f"   Input file: {input_csv}")
        print(f"   Output file: {output_csv}\n")
        
        # Load locations from CSV
        locations = self.load_locations_from_csv(input_csv)
        
        if locations is None:
            print("❌ Failed to load locations. Exiting...")
            return None
        
        print(f"✓ Loaded {len(locations)} locations\n")
        
        # Geocode each location
        data = []
        for idx, location in enumerate(locations):
            print(f"📍 Geocoding {idx+1}/{len(locations)}: {location}")
            lat, lon = self.get_coordinates_from_location(location)
            
            data.append({
                'location_name': location,
                'latitude': lat,
                'longitude': lon
            })
            
            if lat and lon:
                print(f"   ✓ Coordinates: ({lat}, {lon})")
            else:
                print(f"   ✗ Failed to get coordinates")
            
            time.sleep(0.5)  # Rate limiting
        
        # Create DataFrame and save
        df = pd.DataFrame(data)
        df.to_csv(output_csv, index=False)
        
        # Summary
        successful = df[df['latitude'].notna()].shape[0]
        failed = df[df['latitude'].isna()].shape[0]
        
        print(f"\n{'='*60}")
        print(f"✅ CSV file created: {output_csv}")
        print(f"   Total locations: {len(locations)}")
        print(f"   Successfully geocoded: {successful}")
        print(f"   Failed: {failed}")
        print(f"{'='*60}\n")
        
        return df


if __name__ == "__main__":
    # TomTom API Key
    API_KEY = "d5TWC3g2TRMlQr6VQvk0h5pfdQGrqCtA"
    
    # Create extractor and generate CSV
    extractor = CoordinateExtractor(API_KEY)
    df = extractor.create_csv_with_coordinates(
        input_csv='100_locations.csv',
        output_csv='100_locations_with_coords.csv'
    )
    
    if df is not None:
        print("✓ Done! You can now use this CSV file in your main data collection.")
    else:
        print("❌ Failed to create coordinates CSV. Please check the input file.")