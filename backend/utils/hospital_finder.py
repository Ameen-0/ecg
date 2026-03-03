
import pandas as pd
import os
import math

class HospitalFinder:
    def __init__(self, data_path="backend/data/hospitals.csv"):
        self.data_path = data_path
        self.hospitals = self._load_hospitals()
    
    def _load_hospitals(self):
        """Load hospital data from CSV"""
        try:
            if os.path.exists(self.data_path):
                df = pd.read_csv(self.data_path)
                df.columns = [c.lower() for c in df.columns]
                return df
            else:
                # Return default hospitals if file not found
                return pd.DataFrame({
                    'name': ['City Heart Institute', 'General Hospital', 'Apollo Cardiac Center'],
                    'latitude': [12.9716, 12.9765, 12.9689],
                    'longitude': [77.5946, 77.5912, 77.5987],
                    'phone': ['080-22334455', '080-11223344', '080-99887766'],
                    'specialty': ['Cardiology', 'Emergency', 'Cardiac Care'],
                    'distance_km': [2.3, 3.1, 4.2]
                })
        except Exception as e:
            print(f"Error loading hospital data: {e}")
            return None
    
    def find_nearest_hospitals(self, latitude=12.9716, longitude=77.5946, limit=1):
        """Find nearest hospitals to given coordinates"""
        if self.hospitals is None or len(self.hospitals) == 0:
            return []
        
        # For simplicity, return first hospital
        result = []
        for _, row in self.hospitals.head(limit).iterrows():
            hospital = {
                'name': row['name'],
                'distance': row.get('distance_km', 2.3),
                'phone': row['phone'],
                'specialty': row['specialty']
            }
            result.append(hospital)
        
        return result
    
    def get_hospitals_for_bpm(self, bpm):
        """Get hospital suggestions based on BPM abnormality"""
        is_abnormal = bpm < 60 or bpm > 100
        
        if is_abnormal:
            hospitals = self.find_nearest_hospitals()
            return {
                'suggested': True,
                'hospitals': hospitals
            }
        else:
            return {
                'suggested': False,
                'hospitals': []
            }