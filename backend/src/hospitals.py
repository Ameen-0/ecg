
import requests
import math

# Static Fallback Dataset 
KERALA_HOSPITALS_FALLBACK = [
    {"name": "General Hospital, Ernakulam", "address": "Hospital Rd, Ernakulam", "distance": "2.5 km", "phone": "0484-2361251"},
    {"name": "Medical Trust Hospital", "address": "MG Road, Kochi", "distance": "3.1 km", "phone": "0484-2358001"},
    {"name": "Amrita Institute of Medical Sciences", "address": "Ponekkara, Kochi", "distance": "8.5 km", "phone": "0484-2851234"},
    {"name": "Lisie Hospital", "address": "Kaloor, Kochi", "distance": "3.8 km", "phone": "0484-2402044"},
    {"name": "Aster Medcity", "address": "Cheranallur, Kochi", "distance": "10.2 km", "phone": "0484-6699999"}
]

def get_hospitals_osm(lat, lon, limit=5):
    """
    Find nearby hospitals using OpenStreetMap Overpass API.
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Query for hospitals around the location (10km radius)
    # [out:json];node["amenity"="hospital"](around:10000, lat, lon);out;
    overpass_query = f"""
    [out:json];
    (
      node["amenity"="hospital"](around:10000, {lat}, {lon});
      way["amenity"="hospital"](around:10000, {lat}, {lon});
      relation["amenity"="hospital"](around:10000, {lat}, {lon});
    );
    out center;
    """
    
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=8)
        data = response.json()
        
        hospitals = []
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name', 'Unknown Hospital')
            
            # Filter for likely relevant places if needed, but generic "hospital" is good.
            # Avoid clinics if possible if name suggests tiny clinic, but OSM tags cover it.
            
            # Get coordinates
            if element['type'] == 'node':
                h_lat = element['lat']
                h_lon = element['lon']
            else:
                h_lat = element.get('center', {}).get('lat', lat)
                h_lon = element.get('center', {}).get('lon', lon)
                
            # Calculate distance (Haversine simpler approximation for short dist)
            # 1 deg lat ~ 111 km
            # 1 deg lon ~ 111 * cos(lat)
            dk = 111.0
            dist = math.sqrt(((lat - h_lat) * dk)**2 + ((lon - h_lon) * dk * math.cos(math.radians(lat)))**2)
            
            phone = tags.get('phone', tags.get('contact:phone', 'Not available'))
            street = tags.get('addr:street', '')
            city = tags.get('addr:city', '')
            address = f"{street}, {city}".strip(', ')
            if not address: address = "Address not listed locally"

            hospitals.append({
                "name": name,
                "address": address,
                "distance": f"{dist:.1f} km",
                "phone": phone,
                "dist_val": dist
            })
            
        # Sort by distance
        hospitals.sort(key=lambda x: x['dist_val'])
        
        # Helper to deduplicate by name (sometimes nodes and ways overlap)
        seen = set()
        unique_hospitals = []
        for h in hospitals:
            if h['name'] not in seen:
                seen.add(h['name'])
                del h['dist_val'] # remove internal key
                unique_hospitals.append(h)
                if len(unique_hospitals) >= limit: break
                
        return unique_hospitals
        
    except Exception as e:
        print(f"Hospital API Error: {e}")
        return []

def find_nearest_heart_care(lat=None, lon=None):
    """
    Wrapper to get hospitals. Falls back to static list if API fails or no location.
    """
    if lat and lon:
        results = get_hospitals_osm(lat, lon)
        if results:
            return results
            
    return KERALA_HOSPITALS_FALLBACK
