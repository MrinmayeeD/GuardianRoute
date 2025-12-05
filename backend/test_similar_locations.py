#!/usr/bin/env python
"""
Test script for Similar Locations API
Run this to verify the API is working correctly
"""

import requests
import json
from typing import Dict, List

API_BASE_URL = "http://localhost:8000/api/viz"

def test_similar_locations():
    """Test the similar locations endpoint."""
    
    test_cases = [
        ("Pune", 3),
        ("Mumbai", 2),
        ("Delhi", 4),
        ("Bangalore", 5),
    ]
    
    print("=" * 80)
    print("🧪 TESTING SIMILAR LOCATIONS API")
    print("=" * 80)
    
    for location, top_n in test_cases:
        print(f"\n📍 Test: Finding {top_n} similar locations for '{location}'")
        print("-" * 80)
        
        try:
            # Make API request
            url = f"{API_BASE_URL}/similar-locations/{location}"
            params = {"top_n": top_n}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Display results
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Input Location: {data['input_location']}")
            print(f"📈 Similar Locations Found: {data['total_similar']}")
            print(f"⏰ Generated At: {data['generated_at']}")
            
            print(f"\n🗺️  Similar Locations:")
            for idx, loc in enumerate(data['similar_locations'], 1):
                print(f"\n   #{idx}: {loc['location_name']}")
                print(f"       Similarity Score: {loc['similarity_score']:.2f}%")
                print(f"       Coordinates: ({loc['latitude']:.4f}, {loc['longitude']:.4f})")
                print(f"       Distance: {loc['similarity_distance']:.6f}")
            
            print("\n" + "=" * 80)
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Error: Could not connect to API at {API_BASE_URL}")
            print("   Make sure the server is running:")
            print("   python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000")
            break
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"   Response: {e.response.json()}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 80)
    print("✅ Tests Complete!")
    print("=" * 80)


def test_error_cases():
    """Test error handling."""
    
    print("\n" + "=" * 80)
    print("🧪 TESTING ERROR CASES")
    print("=" * 80)
    
    error_cases = [
        ("InvalidLocation123", 3, "404 - Location not found"),
        ("Pune", 10, "400 - Invalid top_n value"),
    ]
    
    for location, top_n, expected_error in error_cases:
        print(f"\n❌ Test: {expected_error}")
        print(f"   Location: '{location}', Top N: {top_n}")
        print("-" * 80)
        
        try:
            url = f"{API_BASE_URL}/similar-locations/{location}"
            params = {"top_n": top_n}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"✅ Got expected error status: {response.status_code}")
                print(f"   Error details: {response.json()}")
            else:
                print(f"⚠️  Unexpected success (expected error)")
                
        except Exception as e:
            print(f"   Exception: {str(e)}")


def compare_endpoints():
    """Compare with other visualization endpoints."""
    
    print("\n" + "=" * 80)
    print("📊 COMPARING ALL VISUALIZATION ENDPOINTS")
    print("=" * 80)
    
    endpoints = [
        ("GET /heatmap/hourly/18", "Heatmap for hour 18"),
        ("GET /zones/analytics", "All zones analytics"),
        ("GET /zones/Pune", "Analytics for Pune"),
        ("GET /predict/heatmap?hours_ahead=3", "Predictions for 3 hours"),
        ("GET /similar-locations/Pune?top_n=3", "Similar locations for Pune"),
    ]
    
    for endpoint, description in endpoints:
        method, path = endpoint.split(" ")
        full_url = f"{API_BASE_URL}/{path.lstrip('/')}"
        
        try:
            response = requests.get(full_url, timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint:45s} → Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint:45s} → Error: Connection failed")


if __name__ == "__main__":
    import sys
    
    print("\n🚀 Similar Locations API Test Suite")
    print("=" * 80)
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/heatmap/hourly/18", timeout=5)
        print("✅ API Server is running!")
    except:
        print("❌ API Server is not running!")
        print("\nTo start the server, run:")
        print("  cd C:\\PROJECT\\ML Projects\\Katalyst_TOMTOM\\Katathon-Hackathon")
        print("  python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # Run tests
    print("\n" + "=" * 80)
    test_similar_locations()
    test_error_cases()
    compare_endpoints()
    
    print("\n" + "=" * 80)
    print("🎉 All tests completed!")
    print("=" * 80)
