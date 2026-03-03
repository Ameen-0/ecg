import os
import wfdb
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.stats import entropy
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

DATASET_PATH = "../datasets/mitbih"

def extract_features(signal, fs=360):
    signal = np.array(signal)

    peaks, _ = find_peaks(signal, distance=fs*0.6)

    if len(peaks) < 2:
        return None

    rr_intervals = np.diff(peaks) / fs

    heart_rate = 60 / np.mean(rr_intervals)
    rr_mean = np.mean(rr_intervals)
    rr_std = np.std(rr_intervals)
    signal_var = np.var(signal)
    signal_entropy = entropy(np.histogram(signal, bins=50)[0])

    return [
        heart_rate,
        rr_mean,
        rr_std,
        signal_var,
        signal_entropy
    ]

X = []
y = []

print("Reading MITBIH dataset...")

records = os.listdir(DATASET_PATH)

records = [r.replace(".dat", "") for r in records if ".dat" in r]

for record in records:

    try:
        record_path = os.path.join(DATASET_PATH, record)

        data = wfdb.rdrecord(record_path)
        signal = data.p_signal[:, 0]

        features = extract_features(signal)

        if features:
            X.append(features)

            hr = features[0]

            if hr < 60:
                label = 0  # Bradycardia
            elif hr > 100:
                label = 2  # Tachycardia
            else:
                label = 1  # Normal

            y.append(label)

    except:
        pass

X = np.array(X)
y = np.array(y)

print("Total samples:", len(X))

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    random_state=42
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("Model Accuracy:", accuracy * 100, "%")

os.makedirs("models", exist_ok=True)

joblib.dump(model, "models/ecg_model.pkl")

print("Model saved at backend/models/ecg_model.pkl")
