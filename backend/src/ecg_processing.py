
import cv2
import sys
import os

# Add parent directory to path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ecg_processor import ECGProcessor
from src.ecg_classifier import classify_ecg

_processor = ECGProcessor()

def process_ecg_image(image_path):
    result, message = _processor.process_image(image_path)
    if result is None:
        return {"error": message}

    condition = classify_ecg(image_path)
    result["detected_abnormality"] = condition
    
    if condition == "Normal":
        result["guidance"] = "Your ECG appears normal. Maintain a healthy lifestyle."
    else:
        result["guidance"] = "Cardiac pattern detected. Consult a specialist."
        
    return result
