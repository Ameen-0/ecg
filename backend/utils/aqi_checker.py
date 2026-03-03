
import pandas as pd
import os

class AQIChecker:
    def __init__(self, data_path="backend/data/aqi.csv"):
        self.data_path = data_path
        self.aqi_data = self._load_aqi_data()
    
    def _load_aqi_data(self):
        """Load AQI data from CSV"""
        try:
            if os.path.exists(self.data_path):
                df = pd.read_csv(self.data_path)
                df.columns = [c.lower() for c in df.columns]
                return df
            else:
                # Return default data if file not found
                return pd.DataFrame({
                    'city': ['Default'],
                    'aqi': [50],
                    'level': ['Good'],
                    'advisory': ['Air quality is satisfactory']
                })
        except Exception as e:
            print(f"Error loading AQI data: {e}")
            return None
    
    def get_aqi_advisory(self, city=None, aqi_value=None):
        """Get AQI level and health advisory"""
        if aqi_value is not None:
            aqi = aqi_value
        elif city and self.aqi_data is not None:
            city_data = self.aqi_data[self.aqi_data['city'].str.lower() == city.lower()]
            if not city_data.empty:
                aqi = city_data.iloc[0]['aqi']
            else:
                aqi = 50
        else:
            aqi = 50
        
        # Determine AQI level and advisory
        if aqi <= 50:
            level = "Good"
            advisory = "Safe for outdoor activities"
        elif aqi <= 100:
            level = "Moderate"
            advisory = "Sensitive individuals should limit outdoor exertion"
        elif aqi <= 150:
            level = "Unhealthy for Sensitive Groups"
            advisory = "Children and elderly reduce outdoor activities"
        elif aqi <= 200:
            level = "Unhealthy"
            advisory = "Limit outdoor activities"
        else:
            level = "Hazardous"
            advisory = "Avoid all outdoor activities"
        
        return {
            "aqi": aqi,
            "level": level,
            "advisory": advisory
        }
    
    def get_combined_warning(self, bpm, aqi):
        """Get combined warning if both BPM and AQI are concerning"""
        warnings = []
        
        if bpm < 60:
            warnings.append("Low heart rate")
        elif bpm > 100:
            warnings.append("Elevated heart rate")
        
        if aqi > 100:
            warnings.append("Poor air quality")
        
        if len(warnings) >= 2:
            return "⚠️ CAUTION: " + " + ".join(warnings)
        elif warnings:
            return "ℹ️ Note: " + warnings[0]
        else:
            return "✅ All parameters normal"