
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

class ECGProcessor:
    def __init__(self):
        self.sampling_rate = config.SAMPLING_RATE
        self.min_rpeaks = config.MIN_RPEAKS
        self.quality_threshold = config.QUALITY_THRESHOLD
        
    def process_image(self, image_path):
        """
        Process paper ECG image and extract BPM
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return None, "Could not read image file"
            
            # Step 1: Deskew image
            deskewed = self._deskew_image(image)
            
            # Step 2: Remove grid lines
            cleaned = self._remove_grid(deskewed)
            
            # Step 3: Extract waveform
            signal = self._extract_waveform(cleaned)
            
            # Step 4: Normalize signal
            signal = (signal - np.mean(signal)) / np.std(signal)
            
            # Step 5: Process with NeuroKit2
            return self._process_signal(signal)
            
        except Exception as e:
            return None, f"Image processing error: {str(e)}"
    
    def process_digital(self, signal_data):
        """
        Process digital ECG signal (CSV or array)
        """
        try:
            # Convert to numpy array if needed
            if isinstance(signal_data, list):
                signal = np.array(signal_data)
            elif isinstance(signal_data, pd.Series):
                signal = signal_data.values
            else:
                signal = signal_data
            
            return self._process_signal(signal)
            
        except Exception as e:
            return None, f"Digital processing error: {str(e)}"
    
    def _deskew_image(self, image):
        """Deskew image using Hough transform"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
        
        if lines is not None:
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = np.degrees(theta) - 90
                angles.append(angle)
            
            if angles:
                median_angle = np.median(angles)
                if abs(median_angle) > 0.5:
                    rotated = rotate(image, median_angle, cval=1)
                    return (rotated * 255).astype(np.uint8)
        
        return image
    
    def _remove_grid(self, image):
        """Remove grid lines using morphological operations"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, config.GAUSSIAN_BLUR_KERNEL, 0)
        
        # OTSU threshold
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Morphological opening to remove grid
        kernel = np.ones(config.MORPHOLOGY_KERNEL, np.uint8)
        opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        
        return opened
    
    def _extract_waveform(self, binary_image):
        """Extract ECG waveform using column-wise median tracing"""
        height, width = binary_image.shape
        signal = []
        
        for col in range(width):
            column = binary_image[:, col]
            white_pixels = np.where(column > 0)[0]
            
            if len(white_pixels) > 0:
                y_pos = np.median(white_pixels)
                signal_value = height - y_pos
            else:
                signal_value = signal[-1] if signal else 0
            
            signal.append(signal_value)
        
        # Resize to reasonable length
        target_length = self.sampling_rate * 10  # 10 seconds
        if len(signal) > target_length:
            # Downsample
            indices = np.linspace(0, len(signal)-1, target_length, dtype=int)
            signal = [signal[i] for i in indices]
        
        return np.array(signal)
    
    def _process_signal(self, signal):
        """Core signal processing with NeuroKit2"""
        # Check signal length
        min_samples = self.sampling_rate * config.MIN_SIGNAL_SECONDS
        if len(signal) < min_samples:
            return None, f"Signal too short ({len(signal)/self.sampling_rate:.1f} seconds)"
        
        try:
            # Clean signal
            cleaned = nk.ecg_clean(signal, sampling_rate=self.sampling_rate)
            
            # Detect R-peaks
            peaks, info = nk.ecg_peaks(cleaned, sampling_rate=self.sampling_rate)
            
            # Get R-peaks array
            rpeaks = info['ECG_R_Peaks']
            
            # Validate number of peaks
            if len(rpeaks) < self.min_rpeaks:
                return None, f"Insufficient R-peaks detected ({len(rpeaks)} found, need {self.min_rpeaks})"
            
            # Check signal quality
            quality_result = nk.ecg_quality(cleaned, sampling_rate=self.sampling_rate)
            quality = np.mean(quality_result) if isinstance(quality_result, np.ndarray) else quality_result
            
            if quality < self.quality_threshold:
                return None, f"Poor signal quality ({quality:.2f} < {self.quality_threshold})"
            
            # Calculate RR intervals
            rr_intervals = np.diff(rpeaks)
            
            # Use MEDIAN RR (not mean) for robustness
            rr_median = np.median(rr_intervals)
            
            # Calculate BPM
            bpm = 60 / (rr_median / self.sampling_rate)
            
            # Validate BPM range
            if bpm < config.MIN_BPM or bpm > config.MAX_BPM:
                return None, f"BPM {bpm:.1f} outside valid range ({config.MIN_BPM}-{config.MAX_BPM})"
            
            # Calculate HRV for arrhythmia detection
            hrv_std = np.std(rr_intervals) * (60 / self.sampling_rate)
            
            # Classify condition
            condition = self._classify_condition(bpm, hrv_std)
            
            # Determine stress level
            if bpm < 60:
                stress = "Low"
            elif 60 <= bpm <= 100:
                stress = "Normal"
            else:
                stress = "High"
            
            # Prepare result
            result = {
                "bpm": round(bpm, 1),
                "condition": condition,
                "stress": stress,
                "confidence": round(quality * 100),
                "hrv_std": round(hrv_std, 2),
                "num_peaks": len(rpeaks),
                "signal_duration": round(len(signal) / self.sampling_rate, 1)
            }
            
            return result, "Success"
            
        except Exception as e:
            return None, f"Signal processing error: {str(e)}"
    
    def _classify_condition(self, bpm, hrv_std):
        """Classify cardiac condition based on BPM and HRV"""
        if bpm < 60:
            base_condition = "Bradycardia"
        elif 60 <= bpm <= 100:
            base_condition = "Normal"
        elif 100 < bpm <= 120:
            base_condition = "Elevated"
        else:
            base_condition = "Tachycardia"
        
        # Check for possible arrhythmia
        if hrv_std > 15:
            return f"{base_condition} (Arrhythmia)"
        
        return base_condition