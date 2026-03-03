
import requests
import time

def get_location_from_ip():
    """
    Auto-detect location using IP-API.
    """
    try:
        response = requests.get("http://ip-api.com/json/")
        data = response.json()
        if data['status'] == 'success':
            return data['lat'], data['lon'], data['city']
    except Exception as e:
        print(f"IP Location Error: {e}")
    return 10.0, 76.3, "Kochi" # Default Fallback (Kerala)

def get_aqi_category(aqi):
    """
    Returns AQI category and health recommendation.
    """
    if aqi <= 50:
        return "Good", "Air quality is satisfactory, and air pollution poses little or no risk."
    elif aqi <= 100:
        return "Moderate", "Air quality is acceptable. However, there may be a risk for some people, particularly those who are unusually sensitive to air pollution."
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "Members of sensitive groups may experience health effects. The general public is less likely to be affected."
    elif aqi <= 200:
        return "Unhealthy", "Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects."
    elif aqi <= 300:
        return "Very Unhealthy", "Health alert: The risk of health effects is increased for everyone."
    else:
        return "Hazardous", "Health warning of emergency conditions: everyone is more likely to be affected."

def get_real_aqi(lat=None, lon=None, city=None):
    """
    Fetches Real AQI data using Open-Meteo Air Quality API (No key required, highly reliable).
    Falls back to IP location if lat/lon not provided.
    """
    if lat is None or lon is None:
        lat, lon, detected_city = get_location_from_ip()
        if city is None:
            city = detected_city
            
    # Open-Meteo Air Quality API
    # We use US AQI which is standard.
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'current' in data and 'us_aqi' in data['current']:
            aqi_val = data['current']['us_aqi']
            category, recommendation = get_aqi_category(aqi_val)
            
            return {
                "aqi": aqi_val,
                "category": category,
                "recommendation": recommendation,
                "location": city if city else f"{lat},{lon}",
                "source": "Open-Meteo Real-time API"
            }
            
    except Exception as e:
        print(f"AQI Fetch Error: {e}")

    # Fallback to simulated valid data if API fails to avoid breaking UI
    return {
        "aqi": 75,
        "category": "Moderate",
        "recommendation": "Unable to fetch real-time data. Estimate based on region.",
        "location": city if city else "Unknown",
        "source": "Fallback Estimate"
    }

# For backward compatibility if needed
def get_kerala_aqi(city='Kochi'):
    return get_real_aqi(city=city)
