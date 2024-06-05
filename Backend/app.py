from flask import Flask, jsonify, request
from flask_caching import Cache
import logging
from urllib.parse import urlparse, parse_qs
from components.weatherAPI import get_weather_data
from waitress import serve
import sys
from components.getCityCoordinates import get_coordinates
from geopy.geocoders import Nominatim

app = Flask(__name__)

# Set up logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('waitress')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

# Ensure Flask uses the same logger
app.logger.handlers = logger.handlers
app.logger.setLevel(logger.level)

# Configure caching
cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)

# Initialize geocoder
geolocator = Nominatim(user_agent="weather_app")

@app.route('/weather/location/', methods=['GET'])
def get_weather():
    # Log the entire GET request
    app.logger.info(f"Received GET request: {request.url}")

    # Retrieve query parameters
    query_params = parse_qs(urlparse(request.url).query)
    textInput = query_params.get('input', [None])[0]
    latitude = query_params.get('lat', [None])[0]
    longitude = query_params.get('long', [None])[0]

    # Ensure "Null" or empty strings are treated as None for input
    if textInput == "Null":
        textInput = None

    # Log the received query parameters
    app.logger.info(f"Received input: {textInput}, lat: {latitude}, long: {longitude}")

    # Initialize weather data list
    weather_data_list = []

    # If latitude and longitude are provided, fetch weather data based on those coordinates
    if latitude and longitude:
        current_location_weather = get_weather_data(float(latitude), float(longitude))
        if current_location_weather:
            # Get human-readable address from coordinates
            location = geolocator.reverse((latitude, longitude))
            current_location_weather['location'] = location.address
            current_location_weather['location_type'] = 'current_location'
            weather_data_list.append(current_location_weather)

    # If textInput exists, fetch weather data based on the provided input
    if textInput:
        try:
            # Get coordinates from the provided city name
            city_latitude, city_longitude = get_coordinates(textInput)
            search_location_weather = get_weather_data(city_latitude, city_longitude)
            if search_location_weather:
                search_location_weather['location'] = textInput
                search_location_weather['location_type'] = 'search_location'
                weather_data_list.append(search_location_weather)
        except Exception as e:
            # Log and handle any errors
            app.logger.error(f"Error fetching weather data: {e}")

    # Retrieve previously cached weather data
    cached_weather_data = cache.get('weather_data') or []

    # Filter out duplicate current_location entries
    current_location_present = False
    for weather_data in weather_data_list:
        if weather_data['location_type'] == 'current_location':
            for cached_data in cached_weather_data:
                if cached_data['location_type'] == 'current_location' and cached_data['location'] == weather_data['location']:
                    current_location_present = True
                    break
            if not current_location_present:
                cached_weather_data.append(weather_data)
        else:
            cached_weather_data.append(weather_data)

    # Cache the combined weather data list
    cache.set('weather_data', cached_weather_data, timeout=3600)  # Cache for 1 hour

    # Return the weather data list
    return jsonify(cached_weather_data)

if __name__ == '__main__':
    # Serve the app with Waitress
    serve(app, host='0.0.0.0', port=25565)