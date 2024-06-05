import requests
import requests_cache
from geopy.geocoders import Nominatim

requests_cache.install_cache('.cache', expire_after=3600)
geolocator = Nominatim(user_agent="autocorrect")

def get_corrected_city_name(city_name):
    location = geolocator.geocode(city_name)
    if location:
        return location.address.split(",")[0]
    else:
        return city_name

def get_coordinates(city_name):
    try:
        corrected_city_name = get_corrected_city_name(city_name)
        geocode_url = "https://nominatim.openstreetmap.org/search"
        geocode_params = {
            "city": corrected_city_name,
            "format": "json",
            "limit": 1
        }
        response = requests.get(geocode_url, params=geocode_params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        if not data:
            raise ValueError("City not found")
        latitude = float(data[0]['lat'])
        longitude = float(data[0]['lon'])
        return latitude, longitude
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coordinates: {e}")
        raise
    except ValueError as ve:
        print(f"Error: {ve}")
        raise

if __name__ == "__main__":
    try:
        city_name = "londan"  # Incorrectly spelled city name
        latitude, longitude = get_coordinates(city_name)
        print(f"Latitude: {latitude}, Longitude: {longitude}")
    except Exception as e:
        print(f"Error: {e}")