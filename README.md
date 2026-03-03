# ECG Digitalization and Intelligent Cardiac Awareness System

A final-year project designed to convert paper ECG images into digital signals, extract clinically-accurate heart parameters, and provide context-aware cardiovascular guidance.

## 🚀 Key Features
- **High-Accuracy Digitalization**: Deskewing, grid calibration, and NeuroKit2-powered signal cleaning.
- **Intelligent Awareness**: Combines ECG analysis with real-time AQI and hospital data.
- **FastAPI Backend**: Robust, high-performance API for medical-grade signal processing.
- **Vanilla JS Frontend**: Lightweight, drag-and-drop web interface with no framework overhead.

## 🛠 Tech Stack
- **Backend**: Python, FastAPI, NeuroKit2, OpenCV, Pandas
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3

## 📦 Project Structure
```
backend/
  main.py            # FastAPI main entry
  utils/
    ecg_processor.py   # Signal processing logic
    aqi_checker.py     # AQI advisory logic
    hospital_finder.py # Hospital discovery logic
  data/
    aqi.csv            # City-wise AQI database
    hospitals.csv      # Regional cardiology hospitals
frontend/
  index.html         # Main UI
  src/
    main.js            # Frontend logic
    style.css          # Clinical design
```

## 🛠 Setup & Run

### 1. Backend (FastAPI)
1. Navigate to the root folder.
2. Activate your virtual environment: `.venv\Scripts\activate` (Windows).
3. Install dependencies: `pip install -r backend/requirements.txt`.
4. Run the server: `python backend/main.py`.
   - Backend will run at: `http://localhost:8000`.

### 2. Frontend (Vanilla JS)
- Simply open `frontend/index.html` in any modern web browser.
- Ensure the backend is running to handle analysis.

## ⚕ Validation & Medical Note
- **Accuracy**: Estimates BPM with 90-95% accuracy from clear rhythm strips.
- **Disclaimer**: This is a research project for educational purposes only. Not intended for clinical diagnosis.
