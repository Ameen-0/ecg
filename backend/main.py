
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from utils.ecg_processor import process_ecg
from utils.aqi_checker import get_aqi_advisory
from utils.hospital_finder import find_nearest_hospitals
import os

app = FastAPI(title="ECG Digitalization and Intelligent Cardiac Awareness System")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze-ecg")
async def analyze_ecg(
    file: UploadFile = File(...),
    city: str = Form("Kochi")
):
    try:
        # Read image
        image_bytes = await file.read()
        
        # 1. ECG Signal Analysis
        ecg_results = process_ecg(image_bytes)
        
        if not ecg_results.get("success"):
            return {
                "success": False,
                "error": ecg_results.get("error")
            }
            
        bpm = ecg_results.get("bpm")
        status = ecg_results.get("status")

        # 2. AQI Advisory
        aqi_results = get_aqi_advisory(city, bpm)

        # 3. Hospital Search
        hospitals = find_nearest_hospitals(city, status)

        # Final response
        return {
            "success": True,
            "analysis": {
                "bpm": bpm,
                "status": status,
                "stress_level": ecg_results.get("stress_level"),
                "confidence": ecg_results.get("confidence"),
                "hrv": ecg_results.get("hrv"),
                "aqi_value": aqi_results.get("aqi_value"),
                "aqi_level": aqi_results.get("aqi_level"),
                "aqi_message": aqi_results.get("aqi_message"),
                "health_advisory": aqi_results.get("health_advisory"),
                "nearest_hospitals": hospitals
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"API Error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
