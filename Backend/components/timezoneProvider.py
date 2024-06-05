import pytz
from datetime import datetime
from timezonefinder import TimezoneFinder
import requests_cache

# Dictionary to store cached timezone information
timezone_cache = {}

# Install and enable requests cache
requests_cache.install_cache('.cache', expire_after=3600)

def get_utc_offset(timezone_str):
    try:
        print(f"Received timezone string: {timezone_str}")  # Add this line for logging
        if timezone_str is None:
            return "Unknown"
        elif "GMT" in timezone_str or "UTC" in timezone_str:
            return timezone_str
        else:
            tz = pytz.timezone(timezone_str)
            now = datetime.now(pytz.utc)
            tz_now = now.astimezone(tz)
            utc_offset = tz_now.utcoffset()
            # Convert UTC offset to hours and minutes
            hours = int(utc_offset.total_seconds() // 3600)
            minutes = int((utc_offset.total_seconds() % 3600) // 60)
            # Format the offset as ±HH:MM
            offset_str = f"{'+' if utc_offset.total_seconds() >= 0 else '-'}{abs(hours):02}:{abs(minutes):02}"
            return offset_str
    except ValueError as ve:
        print(f"ValueError: {ve}")
        return "Unknown"
    except Exception as e:
        print(f"Error fetching UTC offset: {e}")
        raise

def get_timezone_info(latitude, longitude):
    try:
        # Check if timezone info is already cached
        if (latitude, longitude) in timezone_cache:
            timezone_str = timezone_cache[(latitude, longitude)]
            print("Timezone information retrieved from cache.")
        else:
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
            timezone_cache[(latitude, longitude)] = timezone_str
            print(f"Received timezone string: {timezone_str}")  # Add this line for logging

        if timezone_str:
            utc_offset = get_utc_offset(timezone_str)
            return f"Timezone: {timezone_str}, UTC offset: {utc_offset}"
        else:
            return "Timezone not found for the specified coordinates"
    except Exception as e:
        print(f"Error fetching timezone info for latitude {latitude} and longitude {longitude}: {e}")
        return "Unknown"  # Return a default value in case of error

if __name__ == "__main__":
    try:
        latitude = 59.4370  # Latitude of Tallinn
        longitude = 24.7536  # Longitude of Tallinn
        timezone_info = get_timezone_info(latitude, longitude)
        print(timezone_info)
    except Exception as e:
        print(f"Error: {e}")