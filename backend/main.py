import cv2 # Reloaded
import numpy as np
import neurokit2 as nk
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import load_aqi, get_aqi_message, find_nearest_hospital

app = FastAPI(title="ECG Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

QUALITY_THRESHOLD = 0.45
SAMPLING_RATE = 500


from src.ecg_processing import process_ecg_image
import os

TEMPORARY_STORAGE = "backend/data/uploads"
if not os.path.exists(TEMPORARY_STORAGE):
    os.makedirs(TEMPORARY_STORAGE)


@app.post("/analyze")
async def analyze_ecg(file: UploadFile = File(...), city: str = Form("Kochi")):
    try:
        file_path = os.path.join(TEMPORARY_STORAGE, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        result = process_ecg_image(file_path)
        
        aqi = load_aqi(city)
        aqi_msg = get_aqi_message(aqi)
        h_name, h_phone = find_nearest_hospital(city)
        
        # Ensure success field is added as expected by the frontend logic implemented previously
        result["success"] = True
        
        # Ensure new requested naming is appended
        result["abnormality"] = result.get("detected_abnormality", "Unknown")
        result["city"] = city
        result["aqi"] = aqi
        result["aqi_message"] = aqi_msg
        result["nearest_hospital"] = h_name
        result["hospital_phone"] = h_phone
        
        # Add legacy keys for frontend compatibility
        result["bpm"] = result.get("heart_rate")
        result["condition"] = result.get("detected_abnormality")
        result["stress"] = result.get("stress_level")
        result["confidence"] = result.get("signal_confidence")
        result["guidance"] = "Your ECG appears normal. Maintain a healthy lifestyle." if result.get("detected_abnormality") == "Normal" else "Cardiac pattern detected. Consult a specialist."

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "message": "Processing failed",
                "error": str(e)
            }
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)