
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
    if ecg_condition == "Normal ECG":
        message.append("Your ECG appears normal. Maintain a healthy lifestyle.")
    else:
        message.append(f"Abnormal pattern detected ({ecg_condition}). Medical consultation is recommended.")
        
    # AQI Context
    if aqi_category in ["Good", "Moderate"]:
        pass # No need to alarm
    elif aqi_category in ["Unhealthy for Sensitive Groups", "Unhealthy"]:
        message.append("Air quality is currently poor. Consider reducing outdoor exertion.")
    elif aqi_category in ["Very Unhealthy", "Hazardous"]:
        message.append("Air quality is critical. Avoid outdoor exposure to protect heart health.")
        
    return " ".join(message)

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
    
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    try:
        # 1. Process ECG
        ecg_results = process_ecg_image(filepath)
        
        if 'error' in ecg_results:
             return jsonify(ecg_results), 400

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
            "hospitals": hospitals if ecg_results['condition'] != "Normal ECG" else [],
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
