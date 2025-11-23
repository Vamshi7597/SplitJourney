"""
Google Places API Integration.
Provides functions to search places and get place details using Google Places API.
"""
import requests
import os
from typing import List, Dict, Optional

# Load API key from environment variable
# Set this in your .env file: GOOGLE_PLACES_API_KEY=your_api_key_here
GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')

# API endpoints
AUTOCOMPLETE_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


def search_places(query: str) -> List[Dict]:
    """
    Searches for places using Google Places Autocomplete API.
    
    Args:
        query: Search query (e.g., "Olive Garden", "hotels near me")
        
    Returns:
        List of place suggestions, each containing:
        - place_id: Google place ID
        - name: Main text (place name)
        - address: Secondary text (address/location)
        
    Example:
        results = search_places("Starbucks")
        # [
        #     {'place_id': 'ChIJ...', 'name': 'Starbucks', 'address': '123 Main St'},
        #     ...
        # ]
    """
    if not GOOGLE_API_KEY:
        print("Warning: GOOGLE_PLACES_API_KEY not set")
        return []
    
    try:
        params = {
            'input': query,
            'key': GOOGLE_API_KEY,
            'types': 'establishment'  # Only return businesses/places
        }
        
        response = requests.get(AUTOCOMPLETE_URL, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'OK':
            print(f"Places API error: {data.get('status')}")
            return []
        
        # Parse predictions
        suggestions = []
        for prediction in data.get('predictions', []):
            suggestions.append({
                'place_id': prediction['place_id'],
                'name': prediction['structured_formatting'].get('main_text', ''),
                'address': prediction['structured_formatting'].get('secondary_text', '')
            })
        
        return suggestions
        
    except requests.RequestException as e:
        print(f"Error calling Places API: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def get_place_details(place_id: str) -> Optional[Dict]:
    """
    Gets detailed information about a place using Google Places Details API.
    
    Args:
        place_id: Google place ID from autocomplete
        
    Returns:
        Dictionary with place details:
        - place_id: Google place ID
        - name: Place name
        - address: Formatted address
        - latitude: Latitude coordinate
        - longitude: Longitude coordinate
        
        Returns None if request fails
        
    Example:
        details = get_place_details('ChIJ...')
       # {
        #     'place_id': 'ChIJ...',
        #     'name': 'Starbucks',
        #     'address': '123 Main St, City, State 12345',
        #     'latitude': 40.7128,
        #     'longitude': -74.0060
        # }
    """
    if not GOOGLE_API_KEY:
        print("Warning: GOOGLE_PLACES_API_KEY not set")
        return None
    
    try:
        params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,geometry',
            'key': GOOGLE_API_KEY
        }
        
        response = requests.get(PLACE_DETAILS_URL, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'OK':
            print(f"Place Details API error: {data.get('status')}")
            return None
        
        result = data.get('result', {})
        location = result.get('geometry', {}).get('location', {})
        
        return {
            'place_id': place_id,
            'name': result.get('name', ''),
            'address': result.get('formatted_address', ''),
            'latitude': location.get('lat'),
            'longitude': location.get('lng')
        }
        
    except requests.RequestException as e:
        print(f"Error calling Place Details API: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
