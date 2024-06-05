# weatherAPI.py
import openmeteo_requests
import requests_cache
import pandas as pd
from geopy.geocoders import ArcGIS
from retry_requests import retry
from components.timezoneProvider import get_timezone_info

def get_weather_data(latitude, longitude):
    try:
        # Get timezone info
        print("Fetching timezone information...")
        timezone_info = get_timezone_info(latitude, longitude)
        print(f"Received timezone info: {timezone_info}")
        timezone_offset_str = timezone_info.split(", ")[-1].split(": ")[-1]  # Extract the UTC offset
        print(f"Extracted timezone offset string: {timezone_offset_str}")  # Add this line for logging
        offset_hours, offset_minutes = map(int, timezone_offset_str[1:].split(":"))  # Get hours and minutes
        print(f"Extracted hours and minutes: {offset_hours}, {offset_minutes}")  # Add this line for logging
        timezone_offset = pd.Timedelta(hours=offset_hours, minutes=offset_minutes)  # Create Timedelta object
        print(f"UTC offset: {timezone_offset}")

        # Setup the Open-Meteo API client with cache and retry on error
        print("Setting up Open-Meteo API client...")
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        openmeteo = openmeteo_requests.Client(session=retry_session)

        # Make sure all required weather variables are listed here
        # The order of variables in hourly or daily is important to assign them correctly below
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ["temperature_2m", "weather_code"],
            "hourly": "temperature_2m",
            "models": "best_match"
        }
        print("Fetching weather data from Open-Meteo API...")
        responses = openmeteo.weather_api(url, params=params)
        print("Received weather data.")
        

        # Process first location. Add a for-loop for multiple locations or weather models
        response = responses[0]
        location = get_location_from_coordinates(latitude, longitude)

        # Current values. The order of variables needs to be the same as requested.
        current = response.Current()
        current_temperature_2m = current.Variables(0).Value()
        current_weather_code = current.Variables(1).Value()

        # Process hourly data. The order of variables needs to be the same as requested.
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

        hourly_data = {"date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        )}
        hourly_data["temperature_2m"] = hourly_temperature_2m

        hourly_dataframe = pd.DataFrame(data=hourly_data)

        # Calculate highest and lowest temperature in the last 24 hours
        twenty_four_hours_ago = pd.Timestamp.now() - pd.Timedelta(hours=24) - timezone_offset  # Adjust for timezone
        last_24_hours_data = hourly_dataframe[hourly_dataframe['date'].dt.tz_convert(None) >= twenty_four_hours_ago]
        highest_temp_last_24h = last_24_hours_data["temperature_2m"].max()
        lowest_temp_last_24h = last_24_hours_data["temperature_2m"].min()

        weather_data = {
            'location': location,
            'temperature': f"{round(float(current_temperature_2m))}°",
            'condition': get_weather_condition(current_weather_code),
            'high': f"H: {round(float(highest_temp_last_24h))}°",
            'low': f"L:{round(float(lowest_temp_last_24h))}°"
        }

        # Return the weather data as a dictionary
        print("Weather data fetched successfully.")
        return weather_data
    
    except Exception as e:
        # Log error message and return it as a dictionary
        print(f"Error fetching weather data: {e}")
        return {"error": str(e)}

# Define a function to get weather condition based on weather code
def get_weather_condition(weather_code):
    # Define a mapping of weather codes to conditions
    weather_conditions = {
        0: "Clear",
        1: "Clearing",
        2: "Stable",
        3: "Developing",
        4: "Smoky",
        5: "Hazy",
        6: "Dusty",
        7: "Windy",
        8: "Whirlwind",
        9: "Duststorm",
        10: "Misty",
        11: "Foggy",
        12: "Foggy",
        13: "Lightning",
        14: "Drizzle",
        15: "Distant",
        16: "Nearby",
        17: "Thunder",
        18: "Squally",
        19: "Tornado",
        20: "Drizzle",
        21: "Rain",
        22: "Snow",
        23: "Sleet",
        24: "Freezing",
        25: "Rainy",
        26: "Snowy",
        27: "Hail",
        28: "Foggy",
        29: "Stormy",
        30: "Dusty",
        31: "Dusty",
        32: "Dusty",
        33: "Dusty",
        34: "Dusty",
        35: "Dusty",
        36: "Blowing",
        37: "Drifting",
        38: "Blowing",
        39: "Drifting",
        40: "Foggy",
        41: "Foggy",
        42: "Thinning",
        43: "Thinning",
        44: "Stable",
        45: "Stable",
        46: "Thickening",
        47: "Thickening",
        48: "Rime",
        49: "Rime",
        50: "Drizzle",
        51: "Drizzle",
        52: "Drizzle",
        53: "Drizzle",
        54: "Drizzle",
        55: "Drizzle",
        56: "Freezing",
        57: "Freezing",
        58: "Drizzling",
        59: "Drizzling",
        60: "Rain",
        61: "Rain",
        62: "Rain",
        63: "Rain",
        64: "Rain",
        65: "Rain",
        66: "Freezing",
        67: "Freezing",
        68: "Mixed",
        69: "Mixed",
        70: "Snowing",
        71: "Snowing",
        72: "Snowing",
        73: "Snowing",
        74: "Snowing",
        75: "Snowing",
        76: "Dusting",
        77: "Snowing",
        78: "Snowing",
        79: "Sleet",
        80: "Shower",
        81: "Shower",
        82: "Shower",
        83: "Shower",
        84: "Shower",
        85: "Shower",
        86: "Shower",
        87: "Shower",
        88: "Shower",
        89: "Shower",
        90: "Shower",
        91: "Light",
        92: "Heavy",
        93: "Light",
        94: "Heavy",
        95: "Thunder",
        96: "Thunder",
        97: "Thunder",
        98: "Thunder",
        99: "Thunder",
        100: "Unknown",
        101: "Clearing",
        102: "Stable",
        103: "Developing",
        104: "Hazy",
        105: "Smoky",
        106: "Unknown",
        107: "Unknown",
        108: "Unknown",
        109: "Unknown",
        110: "Misty",
        111: "Diamond",
        112: "Distant",
        113: "Unknown",
        114: "Unknown",
        115: "Unknown",
        116: "Unknown",
        117: "Unknown",
        118: "Squalls",
        119: "Unknown",
        120: "Foggy",
        121: "Precipitating",
        122: "Drizzling",
        123: "Raining",
        124: "Snowing",
        125: "Freezing",
        126: "Thundering",
        127: "Blowing",
        128: "Blowing",
        129: "Blowing",
        130: "Foggy",
        131: "Foggy",
        132: "Thinning",
        133: "Stable",
        134: "Thickening",
        135: "Rime",
        136: "Unknown",
        137: "Unknown",
        138: "Unknown",
        139: "Unknown",
        140: "Precipitating",
        141: "Drizzling",
        142: "Raining",
        143: "Sleeting",
        144: "Freezing",
        145: "Snowing",
        146: "Snowing",
        147: "Sleeting",
        148: "Freezing",
        149: "Unknown",
        150: "Drizzling",
        151: "Drizzling",
        152: "Drizzling",
        153: "Drizzling",
        154: "Freezing",
        155: "Freezing",
        156: "Freezing",
        157: "Mixed",
        158: "Mixed",
        159: "Unknown",
        160: "Raining",
        161: "Raining",
        162: "Raining",
        163: "Raining",
        164: "Freezing",
        165: "Freezing",
        166: "Freezing",
        167: "Mixed",
        168: "Mixed",
        169: "Unknown",
        170: "Snowing",
        171: "Snowing",
        172: "Snowing",
        173: "Snowing",
        174: "Sleeting",
        175: "Sleeting",
        176: "Sleeting",
        177: "Snowing",
        178: "Snowing",
        179: "Unknown",
        180: "Showering",
        181: "Showering",
        182: "Showering",
        183: "Showering",
        184: "Showering",
        185: "Showering",
        186: "Showering",
        187: "Showering",
        188: "Unknown",
        189: "Hailing",
        190: "Thunderstorm",
        191: "Thunderstorm",
        192: "Thunderstorm",
        193: "Thunderstorm",
        194: "Thunderstorm",
        195: "Thunderstorm",
        196: "Thunderstorm",
        197: "Unknown",
        198: "Unknown",
        199: "Tornado"
    }

    # Return the weather condition if it exists in the mapping, otherwise return "Unknown"
    return weather_conditions.get(weather_code, "Unknown")

def get_location_from_coordinates(latitude, longitude):
    geolocator = ArcGIS(user_agent="geoapiExercises")
    location = geolocator.reverse((latitude, longitude), exactly_one=True)
    if location:
        return location.address
    else:
        return None