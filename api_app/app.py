# app.py (FastAPI version)
import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn
import os
from sklearn.preprocessing import StandardScaler # Import StandardScaler
from starlette.middleware.cors import CORSMiddleware # Import CORSMiddleware

# Define paths to the saved model and scaler
MODEL_PATH = 'random_forest_fraud_model.joblib'
SCALER_PATH = 'time_amount_scaler.joblib'

# Load the model and scaler
model = None
scaler = None
try:
    model = joblib.load(MODEL_PATH)
    print(f"Model loaded successfully from {MODEL_PATH}")
    scaler = joblib.load(SCALER_PATH)
    print(f"Scaler loaded successfully from {SCALER_PATH}")
except Exception as e:
    print(f"Error loading model or scaler: {e}")
    # If loading fails, the API will return 500 errors for predictions

# Initialize FastAPI app
app = FastAPI(
    title="Credit Card Fraud Detection API",
    description="API for predicting credit card fraud using a trained Random Forest model.",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Define the input data model using Pydantic
# We expect 30 features (V1-V28, Time, Amount)
class TransactionFeatures(BaseModel):
    features: List[float]

    # Add a validator to ensure exactly 30 features are provided
    # This is a Pydantic validator, not a standard Python function.
    # It ensures the list has the correct number of elements.
    # @validator('features')
    # def check_features_length(cls, v):
    #     if len(v) != 30:
    #         raise ValueError('Exactly 30 features are required.')
    #     return v

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Credit Card Fraud Detection API. Visit /docs for API documentation."}

@app.post("/predict")
async def predict_fraud(transaction: TransactionFeatures):
    if model is None or scaler is None:
        raise HTTPException(status_code=500, detail="Model or scaler not loaded. Please check server logs.")

    try:
        # Ensure exactly 30 features are provided
        if len(transaction.features) != 30:
            raise ValueError("Expected 30 features (V1-V28, Time, Amount).")

        # Extract Time and Amount (last two features)
        raw_time = transaction.features[28]
        raw_amount = transaction.features[29]

        # Scale Time and Amount using the loaded scaler
        # Reshape for scaler: it expects a 2D array (n_samples, n_features)
        scaled_time = scaler.transform(np.array([[raw_time]]))[0][0]
        scaled_amount = scaler.transform(np.array([[raw_amount]]))[0][0]

        # Reconstruct features with scaled Time and Amount
        # V1-V28 are assumed to be already scaled or are placeholders
        processed_features = transaction.features[:28] + [scaled_time, scaled_amount]

        # Convert processed features to numpy array and reshape for prediction
        input_data = np.array(processed_features).reshape(1, -1)

        # Make prediction
        prediction = model.predict(input_data)[0]
        prediction_proba = model.predict_proba(input_data)[:, 1][0]

        # Return prediction
        return {
            "prediction": int(prediction),
            "prediction_proba": float(prediction_proba),
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
