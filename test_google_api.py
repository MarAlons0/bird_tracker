import requests
import os

def test_google_places_api():
    api_key = 'AIzaSyC6MVglln7fltmGCpdyvPGqdByyxagy3hQ'
    
    # Test the Places API with a simple nearby search
    base_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    params = {
        'location': '37.7749,-122.4194',  # San Francisco coordinates
        'radius': '1000',
        'key': api_key
    }
    
    response = requests.get(base_url, params=params)
    print(f'Status Code: {response.status_code}')
    print(f'Response: {response.json()}')

if __name__ == '__main__':
    test_google_places_api() 