import cv2
import numpy as np
import neurokit2 as nk
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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


def remove_grid(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 40, 40])
    upper_red1 = np.array([10, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)

    lower_red2 = np.array([170, 40, 40])
    upper_red2 = np.array([180, 255, 255])
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    mask = mask1 + mask2
    image[mask > 0] = [255, 255, 255]

    return image


def split_leads(image, rows=4):
    h, w, _ = image.shape
    row_height = h // rows
    return [image[i*row_height:(i+1)*row_height, :] for i in range(rows)]


import scipy.signal

def extract_waveform(lead_img):
    gray = cv2.cvtColor(lead_img, cv2.COLOR_BGR2GRAY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        15,
        2
    )

    h, w = thresh.shape
    signal = []

    for x in range(w):
        ys = np.where(thresh[:, x] > 0)[0]
        if len(ys) > 0:
            signal.append(h - np.mean(ys))
        else:
            signal.append(signal[-1] if signal else 0)

    signal = np.array(signal)

    if len(signal) == 0 or np.isnan(np.std(signal)) or np.std(signal) == 0:
        return None

    signal = (signal - np.mean(signal)) / np.std(signal)
    
    # Resample to 5000 length to correctly align image width (approx 10s) with 500Hz
    if len(signal) != 5000:
        signal = scipy.signal.resample(signal, 5000)

    signal = nk.signal_smooth(signal, method="savgol", size=11)
    return signal


def process_ecg_image(image):
    if image is None:
        return {"success": False, "message": "Failed to decode image"}
        
    image = remove_grid(image)
    leads = split_leads(image)

    results = []
    qualities = []

    for i, lead in enumerate(leads):
        try:
            signal = extract_waveform(lead)
            if signal is None or len(signal) == 0:
                continue

            # Filtering for quality check and peak detection
            signal_filtered = nk.signal_filter(
                signal,
                lowcut=0.5,
                highcut=40,
                sampling_rate=SAMPLING_RATE
            )

            # Quality calculation (average of per-sample quality)
            quality_array = nk.ecg_quality(signal_filtered, sampling_rate=SAMPLING_RATE)
            quality = float(np.nanmean(quality_array)) if len(quality_array) > 0 else 0.0
            qualities.append(quality)

            if quality < QUALITY_THRESHOLD:
                continue

            # Robust Heart Rate calculation using peaks instead of full process
            _, rpeaks = nk.ecg_peaks(signal_filtered, sampling_rate=SAMPLING_RATE)
            peaks = rpeaks.get("ECG_R_Peaks", [])
            
            if len(peaks) < 2:
                # Not enough peaks to compute a rate for this lead
                continue
                
            hr_array = nk.signal_rate(peaks, sampling_rate=SAMPLING_RATE, desired_length=len(signal_filtered))
            hr = float(np.nanmean(hr_array))
            
            if np.isnan(hr) or hr <= 0:
                continue

            results.append({
                "heart_rate": hr,
                "quality": quality
            })

        except Exception as e:
            print(f"Error processing lead {i}: {e}")
            continue

    if len(results) == 0:
        q_str = ", ".join([f"{q:.3f}" for q in qualities]) if qualities else "None"
        return {
            "success": False,
            "message": f"No valid ECG leads detected. Qualities: {q_str}",
            "valid_leads": 0
        }

    valid_hrs = [r["heart_rate"] for r in results]
    valid_qs = [r["quality"] for r in results]

    return {
        "success": True,
        "average_heart_rate": float(np.mean(valid_hrs)),
        "average_quality": float(np.mean(valid_qs)),
        "valid_leads": len(results)
    }


@app.post("/analyze")
async def analyze_ecg(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        result = process_ecg_image(image)

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
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)