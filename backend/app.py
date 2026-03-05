
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

# Add src to path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.ecg_processing import process_ecg_image
from src.aqi import get_real_aqi
from src.hospitals import find_nearest_heart_care
from src.reporting import generate_pdf_report

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

def generate_health_recommendation(ecg_condition, aqi_category):
    """
    Generates health message based on ECG and AQI.
    """
    message = []
    
    # ECG Context
    if ecg_condition == "Normal":
        message.append("Your ECG appears normal. Maintain a healthy lifestyle.")
    else:
        message.append(f"Cardiac pattern detected: {ecg_condition}. Medical consultation is recommended.")
        
    # AQI Context
    if aqi_category not in ["Good", "Moderate"]:
        message.append(f"Air quality is {aqi_category.lower()}. Reduce strenuous outdoor activity.")
        
    return " ".join(message)

import csv

def load_aqi(city):
    aqi_val = 50
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'data', 'aqi.csv')
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['City'].strip().lower() == city.lower():
                    aqi_val = int(row['AQI'])
                    break
    except Exception as e:
        print(f"Error loading AQI: {e}")
    return aqi_val

def get_aqi_message(aqi):
    if aqi < 50:
        return "Good air quality. Safe for outdoor activities."
    elif aqi <= 100:
        return "Moderate air quality. Sensitive people should limit outdoor exertion."
    else:
        return "Poor air quality. Consider limiting outdoor activity."

HOSPITAL_MAPPING = {
    "kochi": "Medical Trust Hospital",
    "thiruvananthapuram": "KIMS Hospital",
    "kozhikode": "Aster MIMS",
    "kannur": "Kannur Medical College",
    "kollam": "Medicity",
    "thrissur": "Amala Institute",
    "alappuzha": "Medical College Alappuzha",
    "palakkad": "PK Das Hospital",
    "malappuram": "MES Medical College",
    "kottayam": "Caritas Hospital",
    "idukki": "Idukki District Hospital",
    "wayanad": "Wayanad Medical College",
    "pathanamthitta": "Muthoot Hospital",
    "kasaragod": "Kasaragod Care Hospital",
    "delhi": "AIIMS Delhi",
    "mumbai": "Lilavati Hospital",
    "bangalore": "Narayana Hrudayalaya",
    "chennai": "Apollo Hospitals",
    "hyderabad": "Care Hospitals",
    "kolkata": "AMRI Hospitals"
}

def find_nearest_hospital(city):
    nearest = HOSPITAL_MAPPING.get(city.lower(), "Medical Trust Hospital")
    phone = "0484-2358001"
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'data', 'hospitals.csv')
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['name'] == nearest:
                    phone = row['phone']
                    break
    except Exception as e:
        print(f"Error loading hospital data: {e}")
    return nearest, phone

def save_uploaded_file(file):
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    return filepath

@app.route("/analyze", methods=["POST"])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files["file"]
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    city = request.form.get("city", "Kochi")
    
    path = save_uploaded_file(file)
    result = process_ecg_image(path)
    
    if "error" in result:
        return jsonify(result), 400
        
    aqi = load_aqi(city)
    aqi_msg = get_aqi_message(aqi)
    h_name, h_phone = find_nearest_hospital(city)
    
    full_result = {
        "heart_rate": result.get("heart_rate", 0),
        "abnormality": result.get("detected_abnormality", "Unknown"),
        "stress_level": result.get("stress_level", "Unknown"),
        "signal_confidence": result.get("signal_confidence", 0),
        "city": city,
        "aqi": aqi,
        "aqi_message": aqi_msg,
        "nearest_hospital": h_name,
        "hospital_phone": h_phone,
        "signal": result.get("signal", []),
        "peaks": result.get("peaks", []),
        "guidance": result.get("guidance", "")
    }
    
    return jsonify(full_result)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Get location if provided
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    
    if lat: lat = float(lat)
    if lon: lon = float(lon)
    
    filepath = save_uploaded_file(file)
    
    try:
        # 1. Process ECG
        result = process_ecg_image(filepath)
        
        # Translate to Flask-expected keys
        ecg_results = {
            "bpm": result.get("heart_rate"),
            "condition": result.get("detected_abnormality"),
            "stress": result.get("stress_level"),
            "confidence": result.get("signal_confidence")
        }
        
        if 'error' in result:
             return jsonify(result), 400

        # 2. Get Real AQI
        aqi_data = get_real_aqi(lat, lon)
        
        # 3. Get Hospitals (if needed)
        # We fetch them anyway to include in the full report if the user wants to see them
        # Logic: Show if condition abnormal OR purely for information
        hospitals = find_nearest_heart_care(lat, lon)
        
        # 4. Generate Recommendation
        rec_text = generate_health_recommendation(ecg_results['condition'], aqi_data['category'])
        
        # 5. Aggregate Data
        final_response = {
            **ecg_results,
            "AQI": aqi_data['aqi'],
            "AQI_status": aqi_data['category'],
            "AQI_recommendation": aqi_data['recommendation'],
            "location": aqi_data['location'],
            "hospitals": hospitals if ecg_results['condition'] != "Normal" else [],
            "recommendation": rec_text
        }
        
        # 6. Generate Report Immediately (to provide URL)
        report_filename = f"report_{file.filename.split('.')[0]}.pdf"
        report_path = os.path.join(RESULTS_FOLDER, report_filename)
        generate_pdf_report(final_response, report_path)
        
        final_response['report_url'] = f"/results/{report_filename}"
        
        return jsonify(final_response)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if lat: lat = float(lat)
    if lon: lon = float(lon)
    
    hospitals = find_nearest_heart_care(lat, lon)
    return jsonify(hospitals)

@app.route('/api/aqi', methods=['GET'])
def get_aqi():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    city = request.args.get('city')
    
    if lat: lat = float(lat)
    if lon: lon = float(lon)
    
    aqi_data = get_real_aqi(lat, lon, city)
    return jsonify(aqi_data)

@app.route('/api/report', methods=['POST'])
def create_report():
    # Legacy endpoint incase frontend calls it separately
    data = request.json
    try:
        filename = f"report_{data.get('filename', 'scan')}.pdf"
        if not filename.lower().endswith('.pdf'): filename += ".pdf"
        
        filepath = os.path.join(RESULTS_FOLDER, filename)
        generate_pdf_report(data, filepath)
        return jsonify({'url': f'/results/{filename}', 'message': 'Report generated successfully'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/results/<path:filename>')
def download_file(filename):
    return send_from_directory(RESULTS_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
