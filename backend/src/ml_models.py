
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/stress_model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), '../models/stress_scaler.pkl')

def train_stress_model():
    """
    Trains a Logistic Regression model on synthetic data for stress classification.
    Features: [Heart Rate, RR Mean, RR Std, Variance, Entropy]
    Classes: 0 (Normal), 1 (Stress/Abnormal)
    """
    X = []
    y = []
    
    # Generate synthetic data
    # Normal: HR 60-90, RR ~0.8, RR_std low, Var normal, Entropy normal
    for _ in range(200):
        hr = np.random.normal(70, 10)
        rr_mean = 60.0 / hr
        rr_std = np.random.normal(0.05, 0.02)
        var = np.random.normal(1.0, 0.2)
        entropy = np.random.normal(5.0, 0.5)
        X.append([hr, rr_mean, rr_std, var, entropy])
        y.append(0) # Normal

    # Stress/Abnormal: HR > 100 or < 50, RR erratic, Entropy high/low
    for _ in range(200):
        # Stress Type 1 (Tachy)
        hr = np.random.normal(110, 15)
        rr_mean = 60.0 / hr
        rr_std = np.random.normal(0.15, 0.05) # Higher variability or very low
        var = np.random.normal(1.5, 0.5)
        entropy = np.random.normal(6.5, 0.8) # Higher disorder
        X.append([hr, rr_mean, rr_std, var, entropy])
        y.append(1) # Stress/Abnormal

    X = np.array(X)
    y = np.array(y)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = LogisticRegression(random_state=42, C=1.0)
    model.fit(X_scaled, y)
    
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print("Model and Scaler trained and saved.")
    return model, scaler

def load_components():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        return train_stress_model()
    return joblib.load(MODEL_PATH), joblib.load(SCALER_PATH)

def predict_stress_level(features):
    """
    Predicts stress level based on dictionary of features.
    Input matches ecg_processing output.
    """
    try:
        model, scaler = load_components()
        
        # Extract features in order
        # [Heart Rate, RR Mean, RR Std, Variance, Entropy]
        hr = features.get('heart_rate', 70)
        rr_mean = features.get('rr_mean', 0.8)
        rr_std = features.get('rr_std', 0.05)
        var = features.get('variance', 1.0)
        entropy = features.get('entropy', 5.0)
        
        vector = np.array([[hr, rr_mean, rr_std, var, entropy]])
        vector_scaled = scaler.transform(vector)
        
        prediction = model.predict(vector_scaled)[0]
        probs = model.predict_proba(vector_scaled)[0]
        
        confidence = float(np.max(probs) * 100)
        
        if prediction == 0:
            condition = "Normal"
            risk_level = "Low"
        else:
            condition = "Stress"
            risk_level = "High" if confidence > 80 else "Moderate"
            
        return {
            "condition": condition,
            "risk_level": risk_level,
            "confidence": round(confidence, 1)
        }
        
    except Exception as e:
        print(f"ML Prediction Error: {e}")
        return {
            "condition": "Normal", # Default fallback
            "risk_level": "Low",
            "confidence": 0
        }

if __name__ == "__main__":
    train_stress_model()
