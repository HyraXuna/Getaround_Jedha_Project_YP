import mlflow 
import uvicorn
import pandas as pd 
from pydantic import BaseModel
from typing import Literal, List, Union
from fastapi import FastAPI, File, UploadFile
import joblib
from fastapi.responses import RedirectResponse
import pickle

logged_model = 'runs:/c2037b0c2c9e4c629a02b7b8a7eb2642/model'
loaded_model = mlflow.pyfunc.load_model(logged_model)
print("✅ Model loaded successfully!")


description = """
Welcome to the rental price predictor API for Getaround 🏎️ !\n
Submit the parameters of your car and a XGBoost Machine Learning model, trained on GetAround data, will recommend you a price per day for your rental. 

**Use the endpoint `/predict` to estimate the daily rental price of your car !**
"""

tags_metadata = [
    {
        "name": "Price Predictions 💶💶💶",
        "description": "Use this endpoint for getting predictions"
    }
]

app = FastAPI(
    title="💸 Rental Price Prediction API",
    description=description,
    version="1.0",
    openapi_tags=tags_metadata
)

class PredictionFeatures(BaseModel):
    model_key: Literal['Citroën','Peugeot','PGO','Renault','Audi','BMW','Mercedes','Opel','Volkswagen','Ferrari','Mitsubishi','Nissan','SEAT','Subaru','Toyota','other'] 
    mileage: Union[int, float]
    engine_power: Union[int, float]
    fuel: Literal['diesel','petrol','other']
    paint_color: Literal['black','grey','white','red','silver','blue','beige','brown','other']
    car_type: Literal['convertible','coupe','estate','hatchback','sedan','subcompact','suv','van']
    private_parking_available: bool
    has_gps: bool
    has_air_conditioning: bool
    automatic_car: bool
    has_getaround_connect: bool
    has_speed_regulator: bool
    winter_tires: bool

# Load the preprocessor
with open('preprocessor.pkl', 'rb') as file:
    preprocessor = pickle.load(file)

# Redirect automatically to /docs (without showing this endpoint in /docs)
@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url='/docs')


@app.post("/predict", tags=["Price Predictions 💶💶💶"])
async def predict(predictionFeatures: PredictionFeatures):
    # Read data 
    input_data = pd.DataFrame({
            "model_key": [predictionFeatures.model_key],
            "mileage": [predictionFeatures.mileage],
            "engine_power": [predictionFeatures.engine_power],
            "fuel": [predictionFeatures.fuel],
            "paint_color": [predictionFeatures.paint_color],
            "car_type": [predictionFeatures.car_type],
            "private_parking_available": [predictionFeatures.private_parking_available],
            "has_gps": [predictionFeatures.has_gps],
            "has_air_conditioning": [predictionFeatures.has_air_conditioning],
            "automatic_car": [predictionFeatures.automatic_car],
            "has_getaround_connect": [predictionFeatures.has_getaround_connect],
            "has_speed_regulator": [predictionFeatures.has_speed_regulator],
            "winter_tires": [predictionFeatures.winter_tires]
        })
    
    preprocessed_data = preprocessor.transform(input_data)

    prediction = loaded_model.predict(preprocessed_data)

    # Format response
    response = {"prediction": prediction.tolist()[0]}
    return response
