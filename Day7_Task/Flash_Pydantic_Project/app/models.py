from pydantic import BaseModel


class PredictionRequest(BaseModel):
    text: str
    confidence: float


class PredictionResponse(BaseModel):
    prediction: str
    score: float

