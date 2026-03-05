from tensorflow.keras.models import load_model
import cv2
import numpy as np
import os

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "models",
    "ecg_classifier.h5"
)

model = load_model(MODEL_PATH)

CLASSES = [
    "Normal",
    "Myocardial Infarction",
    "Abnormal Heartbeat",
    "History of MI"
]

def classify_ecg(image_path):
    img = cv2.imread(image_path)
    img = cv2.resize(img,(224,224))
    img = img/255.0
    img = np.expand_dims(img,axis=0)
    prediction = model.predict(img)
    class_index = np.argmax(prediction)
    return CLASSES[class_index]
