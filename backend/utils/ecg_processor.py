
import cv2
import numpy as np
import neurokit2 as nk
from scipy.signal import find_peaks

def get_sampling_rate_from_grid(gray):
    """
    Automatic grid detection to calibrate pixels per second.
    Standard ECG: 25mm/s, grid 1mm = 1 square.
    """
    edges = cv2.Canny(gray, 50, 150)
    # Sum across columns to find vertical lines
    projection = np.sum(edges, axis=0)
    peaks, _ = find_peaks(projection, distance=15)
    
    if len(peaks) > 1:
        avg_spacing = np.mean(np.diff(peaks))
        # Standard paper speed 25mm/s. Assuming each grid peak is 1mm.
        sampling_rate = avg_spacing * 25
        return sampling_rate
    return 300 # Default if detection fails

def deskew_image(gray):
    """
    Deskew image using Hough line detection.
    """
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
    
    angles = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            if abs(angle) < 45: # Filter out near-vertical lines
                angles.append(angle)
    
    if angles:
        median_angle = np.median(angles)
        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        deskewed = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return deskewed
    return gray

def process_ecg(image_bytes):
    # 1. Decode image bytes to grayscale
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {"success": False, "error": "Invalid image"}

    # 2. Deskew image
    deskewed = deskew_image(img)

    # 3. Gaussian blur
    blurred = cv2.GaussianBlur(deskewed, (5, 5), 0)

    # 4. OTSU binary inverse threshold
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 5. Morphological opening to remove grid noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned_binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    # 6. Column-wise median tracing to extract waveform
    h, w = cleaned_binary.shape
    signal = []
    for x in range(w):
        y_indices = np.where(cleaned_binary[:, x] > 0)[0]
        if len(y_indices) > 0:
            signal.append(h - np.median(y_indices))
        else:
            if signal:
                signal.append(signal[-1]) # Simple interpolation
            else:
                signal.append(0)

    signal = np.array(signal)

    # 7. Normalize signal (mean 0, std 1)
    if np.std(signal) > 0:
        signal = (signal - np.mean(signal)) / np.std(signal)

    # 8. Calibration
    sampling_rate = get_sampling_rate_from_grid(deskewed)

    # 9. Clean using NeuroKit2
    try:
        cleaned_signal = nk.ecg_clean(signal, sampling_rate=int(sampling_rate))
        
        # 10. Detect peaks
        peaks, info = nk.ecg_peaks(cleaned_signal, sampling_rate=int(sampling_rate))
        rpeaks = info["ECG_R_Peaks"]
        
        # 11. Validation
        if len(rpeaks) < 3:
            return {"success": False, "error": "ECG quality insufficient (weak signal)"}

        # 12. Compute RR and BPM
        rr = np.diff(rpeaks)
        rr_median = np.median(rr)
        bpm = 60 / (rr_median / sampling_rate)
        
        # 14. Reject unrealistic BPM
        if bpm < 30 or bpm > 220:
             return {"success": False, "error": "ECG quality insufficient (unrealistic BPM)"}

        # 15. Compute quality
        quality_score = nk.ecg_quality(cleaned_signal, sampling_rate=int(sampling_rate))
        # NeuroKit returns an array or value depending on method, simplified here:
        confidence = float(np.mean(quality_score) * 100) if isinstance(quality_score, np.ndarray) else float(quality_score * 100)

        # 16. Condition logic
        status = "Normal Sinus Rhythm"
        stress_level = "Normal"
        if bpm < 60:
            status = "Bradycardia"
            stress_level = "Monitor Required"
        elif 60 <= bpm <= 100:
            status = "Normal Sinus Rhythm"
        elif 100 < bpm <= 120:
            status = "Elevated Cardiac Stress"
            stress_level = "Elevated"
        elif bpm > 120:
            status = "Tachycardia"
            stress_level = "High"

        # HRV check for Arrhythmia
        hrv_std = np.std(rr) / sampling_rate * 1000 # in ms
        if hrv_std > 15: # Simplified threshold
            status = "Possible Arrhythmia"
            stress_level = "High"

        return {
            "success": True,
            "bpm": int(bpm),
            "status": status,
            "stress_level": stress_level,
            "confidence": f"{int(confidence)}%",
            "hrv": hrv_std
        }
    except Exception as e:
        return {"success": False, "error": f"Internal processing error: {str(e)}"}
