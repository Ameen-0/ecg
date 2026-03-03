# backend/config.py
"""
Configuration constants for ECG Cardiac Awareness System
"""

# Sampling rate (Hz) - MUST be consistent everywhere
SAMPLING_RATE = 250

# BPM validation limits
MIN_BPM = 30
MAX_BPM = 220

# R-peak validation
MIN_RPEAKS = 3

# Signal quality threshold (0-1)
QUALITY_THRESHOLD = 0.6

# Minimum signal duration in seconds
MIN_SIGNAL_SECONDS = 2

# Image processing constants
IMAGE_TARGET_WIDTH = 2000
GAUSSIAN_BLUR_KERNEL = (5, 5)
MORPHOLOGY_KERNEL = (3, 3)

# File paths
DATA_PATH = "backend/data/"
UPLOAD_PATH = "backend/uploads/"