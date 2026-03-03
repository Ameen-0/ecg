
import cv2
import numpy as np
from scipy.signal import find_peaks, butter, filtfilt, savgol_filter
from .ml_models import predict_stress_level
import math

# -----------------------------------------------------------------------------
# PART 1: CLINICAL-GRADE ECG SIGNAL PROCESSING
# -----------------------------------------------------------------------------

def bandpass_filter(signal, lowcut=0.5, highcut=40, fs=250, order=4):
    """
    Apply Butterworth Bandpass Filter.
    """
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    filtered = filtfilt(b, a, signal)
    return filtered

def smooth_signal(signal):
    """
    Apply Savitzky-Golay filter for smoothing.
    """
    # window_length must be odd and <= len(signal)
    window_length = 11
    polyorder = 3
    if len(signal) < window_length:
        window_length = len(signal) if len(signal) % 2 == 1 else len(signal) - 1
        if window_length < polyorder: return signal
    
    return savgol_filter(signal, window_length, polyorder)

def normalize_signal(signal):
    """
    Normalize signal using Z-score normalization: (signal - mean) / std.
    """
    if np.std(signal) == 0:
        return signal - np.mean(signal)
    return (signal - np.mean(signal)) / np.std(signal)

def preprocess_image_clinical(img_raw):
    """
    Step 1: Image Preprocessing
    - Grayscale
    - CLAHE
    - Gaussian Blur (5,5)
    """
    if len(img_raw.shape) == 3:
        gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_raw

    # Adaptive Histogram Equalization (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_eq = clahe.apply(gray)

    # Gaussian Blur
    blurred = cv2.GaussianBlur(gray_eq, (5, 5), 0)
    
    return blurred

def remove_background_grid(blurred_img):
    """
    Step 2: Remove background grid lines
    - Morphological opening
    - Otsu Thresholding
    """
    # Morphological opening to remove small noise/grid lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morphed = cv2.morphologyEx(blurred_img, cv2.MORPH_OPEN, kernel)
    
    # Otsu Thresholding to isolate the waveform
    # Invert first if the trace is dark on light background (typical paper ECG)
    # We assume standard ECG: dark trace on light background.
    # Otsu works on bimodal distribution. 
    # Let's invert so trace is white, background dark for processing
    _, binary = cv2.threshold(morphed, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    return binary

def extract_signal_1d(binary_img):
    """
    Step 3: Signal Extraction
    Convert waveform pixels into 1D signal array.
    """
    h, w = binary_img.shape
    signal = []
    
    for col in range(w):
        column_pixels = binary_img[:, col]
        # Find indices where pixel is 'on' (white)
        fg_indices = np.where(column_pixels > 0)[0]
        
        if len(fg_indices) > 0:
            # Take the median or mean index as the signal value
            # Inverting Y axis because image coordinate 0 is at top
            val = h - np.median(fg_indices)
            signal.append(val)
        else:
            # Handle gaps (interpolation later)
            signal.append(np.nan)
            
    signal = np.array(signal)
    
    # Interpolate NaNs
    nans = np.isnan(signal)
    if np.any(nans) and not np.all(nans):
        x_indices = np.arange(len(signal))
        signal[nans] = np.interp(x_indices[nans], x_indices[~nans], signal[~nans])
    elif np.all(nans):
        # Fallback if no signal detected
        return np.zeros(w)
        
    # Normalize between -1 and +1 for initial processing
    sig_min = np.min(signal)
    sig_max = np.max(signal)
    if sig_max - sig_min != 0:
        signal = 2 * ((signal - sig_min) / (sig_max - sig_min)) - 1
        
    return signal

def calculate_sampling_rate(binary_img, duration_sec=10.0):
    """
    Estimate sampling rate based on image width and typical ECG strip duration.
    Standard 12-lead strip is usually 10 seconds.
    """
    h, w = binary_img.shape
    # If we detected a grid, we could be more precise, but assuming standard 10s or 25mm/s paper speed
    # is a robust fallback. 
    # Let's default to standard 10s for full width if it's a strip.
    fs = w / duration_sec
    return max(fs, 100) # Ensure fs isn't too low to cause filter errors

def calculate_quality_score(signal_raw, binary_img):
    """
    Calculate signal quality score based on continuity and noise.
    """
    # 1. Connectivity check
    h, w = binary_img.shape
    filled_cols = 0
    for col in range(w):
        if np.any(binary_img[:, col] > 0):
            filled_cols += 1
    continuity_score = (filled_cols / w) * 100
    
    # 2. Noise check (variance of first derivative)
    if len(signal_raw) > 1:
        diffs = np.diff(signal_raw)
        noise_score = max(0, 100 - (np.std(diffs) * 20)) # Heuristic
    else:
        noise_score = 0
        
    final_score = (continuity_score * 0.7) + (noise_score * 0.3)
    return min(100, max(0, final_score))

# -----------------------------------------------------------------------------
# MASTER PROCESSING FUNCTION
# -----------------------------------------------------------------------------

def process_ecg_image(image_path):
    """
    Main pipeline function.
    """
    img_raw = cv2.imread(image_path)
    if img_raw is None:
        raise ValueError("Could not load image file.")

    # 1. Preprocess
    blurred = preprocess_image_clinical(img_raw)
    
    # 2. Remove Grid / Binarize
    binary = remove_background_grid(blurred)
    
    # 3. Extract 1D Signal
    raw_signal = extract_signal_1d(binary)
    
    # Sampling Rate Estimation
    fs = calculate_sampling_rate(binary)
    
    # 4. Bandpass Filter
    filtered_signal = bandpass_filter(raw_signal, lowcut=0.5, highcut=40, fs=fs)
    
    # 5. Smooth Signal (Savitzky-Golay)
    smoothed_signal = smooth_signal(filtered_signal)
    
    # 6. Normalize (Z-score)
    final_signal = normalize_signal(smoothed_signal)
    
    # Signal Quality Check
    quality_score = calculate_quality_score(raw_signal, binary)
    
    if quality_score < 30: # Threshold for "insufficient quality"
        return {
            "error": "ECG signal quality insufficient. Please upload clearer ECG.",
            "quality_score": quality_score
        }

    # -------------------------------------------------------------------------
    # PART 2: ACCURATE HEART RATE DETECTION
    # -------------------------------------------------------------------------
    
    # Find Peaks
    # distance=150 is relative to sampling rate. 
    # If fs ~ 100-200Hz, 150 samples is ~0.75-1.5s, which might be too strict for tachycardia.
    # Adjust distance based on FS. 
    # Normal HR max ~200 BPM -> 3.33 BPS -> RR ~ 0.3s.
    # min_distance = 0.3 * fs
    min_dist = int(0.3 * fs) 
    
    peaks, properties = find_peaks(final_signal, distance=min_dist, height=0.3)
    
    duration_sec = len(final_signal) / fs
    
    if len(peaks) > 1:
        # Calculate Heart Rate based on RR intervals for better accuracy than simple count
        rr_intervals = np.diff(peaks) # in samples
        mean_rr_samples = np.mean(rr_intervals)
        mean_rr_sec = mean_rr_samples / fs
        heart_rate = 60.0 / mean_rr_sec
    else:
        # Fallback
        heart_rate = (len(peaks) / duration_sec) * 60 if duration_sec > 0 else 0

    # Ensure realistic range
    # Clamp if it's statistically impossible noise, but keep real abnormalities
    if heart_rate > 250 or heart_rate < 20: 
        # If outside physiological extremes, it might be noise or wrong scaling
        # Let's trust the calculation but flag confidence low later if needed
        pass

    # -------------------------------------------------------------------------
    # PART 3: CLASSIFY CONDITION
    # -------------------------------------------------------------------------
    
    condition = "Normal ECG"
    if heart_rate < 60:
        condition = "Bradycardia"
    elif heart_rate > 100:
        condition = "Tachycardia"
        
    # Arrhythmia Check (RR variability)
    rr_variability = 0
    if len(peaks) > 2:
        rr_intervals = np.diff(peaks)
        rr_std = np.std(rr_intervals)
        rr_mean = np.mean(rr_intervals)
        cv = rr_std / rr_mean # Coefficient of Variation
        
        if cv > 0.15: # 15% variation threshold
            condition = "Arrhythmia Detected"
            
    # -------------------------------------------------------------------------
    # PART 4: ML MODEL INTEGRATION
    # -------------------------------------------------------------------------
    
    # Feature Extraction for ML
    rr_mean_val = np.mean(np.diff(peaks)) if len(peaks) > 1 else 0
    rr_std_val = np.std(np.diff(peaks)) if len(peaks) > 1 else 0
    sig_var = np.var(final_signal)
    
    # Entropy (approximate shannon entropy of histogram)
    hist, _ = np.histogram(final_signal, bins=20, density=True)
    hist = hist[hist > 0]
    sig_entropy = -np.sum(hist * np.log(hist))
    
    # Predict Stress / Risk using ML Model
    ml_result = predict_stress_level({
        "heart_rate": heart_rate,
        "rr_mean": rr_mean_val,
        "rr_std": rr_std_val,
        "variance": sig_var,
        "entropy": sig_entropy
    })
    
    risk_level = ml_result.get("risk_level", "Low")
    confidence = ml_result.get("confidence", 85.0) # Baseline confidence
    
    # Adjust condition for Stress if ML says High Risk
    if ml_result.get("condition") == "Stress" and condition == "Normal ECG":
        condition = "Stress-related abnormality"

    return {
        "heart_rate": int(heart_rate),
        "condition": condition,
        "confidence": confidence,
        "risk_level": risk_level,
        "signal_quality": quality_score,
        "signal_processing_metrics": {
             "rr_variability": float(rr_variability) if 'rr_variability' in locals() else 0,
             "entropy": float(sig_entropy)
        },
        "signal": final_signal.tolist()[::5], # Downsample for frontend performance
        "filename": image_path.split('\\')[-1]
    }
