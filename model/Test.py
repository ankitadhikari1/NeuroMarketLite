import os
from pathlib import Path
import json

os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")

import h5py
from tf_keras.models import load_model, model_from_json
from tf_keras.preprocessing.image import img_to_array
import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
CASCADE_PATH = BASE_DIR / "haarcascade_frontalface_default.xml"
MODEL_PATH = BASE_DIR / "Emotion_little_vgg.h5"

face_classifier = cv2.CascadeClassifier(str(CASCADE_PATH))
if face_classifier.empty():
    fallback = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    face_classifier = cv2.CascadeClassifier(str(fallback))

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model file not found at {MODEL_PATH}. Train with train.py or place Emotion_little_vgg.h5 in this folder."
    )


def _normalize_legacy_input_shapes(model_config):
    layers = model_config.get("config", {}).get("layers", [])
    for layer in layers:
        cfg = layer.get("config", {})
        shape = cfg.get("batch_input_shape")
        if isinstance(shape, list) and len(shape) == 5 and shape[1] is None:
            cfg["batch_input_shape"] = [shape[0], shape[2], shape[3], shape[4]]
        build_shape = cfg.get("build_input_shape")
        if isinstance(build_shape, list) and len(build_shape) == 5 and build_shape[1] is None:
            cfg["build_input_shape"] = [build_shape[0], build_shape[2], build_shape[3], build_shape[4]]
    return model_config


def load_legacy_compatible_model(model_path):
    try:
        return load_model(str(model_path))
    except ValueError as exc:
        if "Kernel shape must have the same length as input" not in str(exc):
            raise

        with h5py.File(model_path, "r") as model_file:
            raw_config = model_file.attrs.get("model_config")
            if raw_config is None:
                raise
            if isinstance(raw_config, bytes):
                raw_config = raw_config.decode("utf-8")
            model_config = _normalize_legacy_input_shapes(json.loads(raw_config))

        model = model_from_json(json.dumps(model_config))
        model.load_weights(str(model_path))
        return model


classifier = load_legacy_compatible_model(MODEL_PATH)

class_labels = ['Angry','Happy','Neutral','Sad','Surprise']

# def face_detector(img):
#     # Convert image to grayscale
#     gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
#     faces = face_classifier.detectMultiScale(gray,1.3,5)
#     if faces is ():
#         return (0,0,0,0),np.zeros((48,48),np.uint8),img

#     for (x,y,w,h) in faces:
#         cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
#         roi_gray = gray[y:y+h,x:x+w]

#     try:
#         roi_gray = cv2.resize(roi_gray,(48,48),interpolation=cv2.INTER_AREA)
#     except:
#         return (x,w,y,h),np.zeros((48,48),np.uint8),img
#     return (x,w,y,h),roi_gray,img


cap = cv2.VideoCapture(0)



while True:
    # Grab a single frame of video
    ret, frame = cap.read()
    if not ret:
        break

    top_confidence = None
    top_label = "No Face"
    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    faces = face_classifier.detectMultiScale(gray,1.3,5)

    for (x,y,w,h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
        roi_gray = gray[y:y+h,x:x+w]
        roi_gray = cv2.resize(roi_gray,(48,48),interpolation=cv2.INTER_AREA)
    # rect,face,image = face_detector(frame)


        if np.sum([roi_gray])!=0:
            roi = roi_gray.astype('float')/255.0
            roi = img_to_array(roi)
            roi = np.expand_dims(roi,axis=0)

        # make a prediction on the ROI, then lookup the class

            preds = classifier.predict(roi)[0]
            label=class_labels[preds.argmax()]
            confidence = float(np.max(preds) * 100.0)
            if top_confidence is None or confidence > top_confidence:
                top_confidence = confidence
                top_label = label
            label_position = (x,y)
            cv2.putText(frame,label,label_position,cv2.FONT_HERSHEY_SIMPLEX,2,(0,255,0),3)
        else:
            cv2.putText(frame,'No Face Found',(20,60),cv2.FONT_HERSHEY_SIMPLEX,2,(0,255,0),3)

    if top_confidence is not None:
        right_text = f"{top_label}: {top_confidence:.1f}%"
    else:
        right_text = "No Face: 0.0%"

    (text_width, _), _ = cv2.getTextSize(right_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    text_x = max(10, frame.shape[1] - text_width - 10)
    cv2.putText(frame, right_text, (text_x, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow('Emotion Detector',frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()


























