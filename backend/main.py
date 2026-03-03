
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import shutil
import pandas as pd
from datetime import datetime
import sys

# Add to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import utilities
from utils.ecg_processor import ECGProcessor
from utils.aqi_checker import AQIChecker
from utils.hospital_finder import HospitalFinder
import config

# Initialize FastAPI
app = FastAPI(title="ECG Cardiac Awareness System")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
ecg_processor = ECGProcessor()
aqi_checker = AQIChecker()
hospital_finder = HospitalFinder()

# Ensure upload directory exists
os.makedirs(config.UPLOAD_PATH, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "ECG Cardiac Awareness System API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/analyze/image")
async def analyze_image(
    file: UploadFile = File(...),
    city: str = Form("Default")
):
    """
    Analyze ECG from uploaded image
    """
    try:
        # Save uploaded file
        file_path = os.path.join(config.UPLOAD_PATH, f"image_{datetime.now().timestamp()}.jpg")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process image
        result, message = ecg_processor.process_image(file_path)
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
        
        if result is None:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": message}
            )
        
        # Get AQI advisory
        aqi_info = aqi_checker.get_aqi_advisory(city=city)
        
        # Get hospital suggestions
        hospital_info = hospital_finder.get_hospitals_for_bpm(result['bpm'])
        
        # Get combined warning
        combined_warning = aqi_checker.get_combined_warning(
            result['bpm'], 
            aqi_info['aqi']
        )
        
        # Prepare response
        response = {
            "success": True,
            "analysis": {
                "bpm": result['bpm'],
                "condition": result['condition'],
                "stress": result['stress'],
                "confidence": result['confidence']
            },
            "aqi": {
                "level": aqi_info['level'],
                "value": aqi_info['aqi'],
                "advisory": aqi_info['advisory']
            },
            "warning": combined_warning,
            "hospitals": hospital_info['hospitals']
        }
        
        return response
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Server error: {str(e)}"}
        )

@app.post("/analyze/digital")
async def analyze_digital(
    file: UploadFile = File(...),
    city: str = Form("Default")
):
    """
    Analyze ECG from digital CSV file
    """
    try:
        # Save uploaded file
        file_path = os.path.join(config.UPLOAD_PATH, f"signal_{datetime.now().timestamp()}.csv")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Read CSV
        try:
            df = pd.read_csv(file_path)
            signal = df.iloc[:, 0].values
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": f"Invalid CSV format: {str(e)}"}
            )
        
        # Process signal
        result, message = ecg_processor.process_digital(signal)
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
        
        if result is None:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": message}
            )
        
        # Get AQI advisory
        aqi_info = aqi_checker.get_aqi_advisory(city=city)
        
        # Get hospital suggestions
        hospital_info = hospital_finder.get_hospitals_for_bpm(result['bpm'])
        
        # Get combined warning
        combined_warning = aqi_checker.get_combined_warning(
            result['bpm'], 
            aqi_info['aqi']
        )
        
        # Prepare response
        response = {
            "success": True,
            "analysis": {
                "bpm": result['bpm'],
                "condition": result['condition'],
                "stress": result['stress'],
                "confidence": result['confidence']
            },
            "aqi": {
                "level": aqi_info['level'],
                "value": aqi_info['aqi'],
                "advisory": aqi_info['advisory']
            },
            "warning": combined_warning,
            "hospitals": hospital_info['hospitals']
        }
        
        return response
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Server error: {str(e)}"}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)