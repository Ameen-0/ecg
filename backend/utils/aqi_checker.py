
import pandas as pd
import os

def get_aqi_advisory(city, bpm):
    """
    AQI advisory based on city data and BPM.
    """
    csv_path = os.path.join(os.path.dirname(__file__), '../data/aqi.csv')
    
    # Load AQI data
    try:
        df = pd.read_csv(csv_path)
        city_data = df[df['City'].str.lower() == city.lower()]
        if not city_data.empty:
            aqi = city_data.iloc[0]['AQI']
        else:
            aqi = 50 # Default moderate AQI
    except:
        aqi = 50

    # AQI Category Logic
    if aqi <= 50:
        aqi_level = "Good"
        aqi_message = "Air quality is satisfactory."
    elif aqi <= 100:
        aqi_level = "Moderate"
        aqi_message = "Air quality is acceptable."
    elif aqi <= 200:
        aqi_level = "Poor"
        aqi_message = "Members of sensitive groups may experience health effects."
    else:
        aqi_level = "Hazardous"
        aqi_message = "Health warning of emergency conditions."

    # Combined Cardiovascular Advisory
    health_advisory = "Maintain a healthy routine."
    if aqi > 100 and bpm > 100:
        health_advisory = "CRITICAL: Air quality is poor and heart rate is elevated. Avoid outdoor activity immediately."
    elif bpm > 100:
        health_advisory = "Heart rate is elevated. Avoid strenuous exercise."
    elif aqi > 100:
        health_advisory = "Air quality is unhealthy. Use a mask or stay indoors."

    return {
        "aqi_level": aqi_level,
        "aqi_message": aqi_message,
        "health_advisory": health_advisory,
        "aqi_value": int(aqi)
    }
