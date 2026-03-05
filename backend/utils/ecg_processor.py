
import cv2
import numpy as np
import neurokit2 as nk
import pandas as pd
from skimage.transform import rotate
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

from scipy.signal import find_peaks, medfilt
import cv2
import numpy as np
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class ECGProcessor:
    def __init__(self):
        self.sampling_rate = config.SAMPLING_RATE
        self.min_rpeaks = config.MIN_RPEAKS
        self.quality_threshold = config.QUALITY_THRESHOLD
        
    def process_image(self, image_path):
        """
        Main entry point for image-based ECG analysis.
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None, "Could not read image file"
            
            return self.process_frame(image)
        except Exception as e:
            return None, f"Image processing error: {str(e)}"

    def process_frame(self, image):
        """
        Implementation of the AI-assisted ECG interpretation pipeline.
        """
        try:
            # Step 1: Process only rhythm strip
            h, w = image.shape[:2]
            rhythm_strip = image[int(h * 0.65):h, 0:w]
            
            # Step 2: Convert to grayscale
            gray = cv2.cvtColor(rhythm_strip, cv2.COLOR_BGR2GRAY)
            
            # Step 3: Remove grid and noise
            blur = cv2.GaussianBlur(gray, (7,7), 0)
            _, thresh = cv2.threshold(
                blur,
                0,
                255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
            
            # Step 4: Extract waveform
            signal = np.mean(thresh, axis=0)
            if np.max(signal) > 0:
                signal = signal / np.max(signal)
            
            # Step 5: Detect R-peaks
            peaks, _ = find_peaks(
                signal,
                distance=60,
                height=0.3
            )
            
            # Step 6: Compute BPM
            duration_seconds = 10
            bpm = int((len(peaks) / duration_seconds) * 60)
            
            # Step 7: Add peak filtering
            if bpm < 40 or bpm > 180:
                bpm = int(np.clip(bpm, 40, 180))
            
            # RR Interval Analysis
            rr_intervals = []
            if len(peaks) >= 3:
                rr_intervals = np.diff(peaks)
            
            # HRV and Stress Level Estimation
            stress_level = self._estimate_stress_hrv(rr_intervals)
            
            # Signal Quality Analysis
            confidence = self._calculate_confidence(signal, peaks)
            
            # Visualization Data Prep
            ds_ratio = 4
            result = {
                "heart_rate": bpm,
                "stress_level": stress_level,
                "signal_confidence": round(confidence),
                "signal": signal.tolist()[::ds_ratio],
                "peaks": [int(p/ds_ratio) for p in peaks]
            }
            
            return result, "Success"
            
        except Exception as e:
            return None, f"Interpretation error: {str(e)}"

    def _estimate_stress_hrv(self, rr_intervals):
        if len(rr_intervals) < 2: return "Normal"
        hrv = np.std(rr_intervals) / (np.mean(rr_intervals) + 1e-6)
        
        if hrv > 0.12: return "Low"
        elif hrv > 0.06: return "Moderate"
        else: return "High"

    def _calculate_confidence(self, signal, peaks):
        if len(peaks) < 3: return 60
        noise = np.var(np.diff(signal))
        continuity = max(0, 100 - (noise * 12))
        completeness = min(100, (len(peaks) / 10) * 100)
        
        score = (0.6 * completeness) + (0.4 * continuity)
        return max(60, min(98, score))
