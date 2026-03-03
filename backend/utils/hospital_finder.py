
import pandas as pd
import os

def find_nearest_hospitals(city, bpm_status):
    """
    Find nearest hospitals from city data if condition is abnormal.
    """
    if "Normal" in bpm_status:
        return []

    csv_path = os.path.join(os.path.dirname(__file__), '../data/hospitals.csv')
    
    try:
        df = pd.read_csv(csv_path)
        city_data = df[df['City'].str.lower() == city.lower()]
        
        if city_data.empty:
            return []
            
        # Top 3 nearest hospitals
        hospitals = city_data.head(3).to_dict('records')
        return hospitals
    except:
        return []
