from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from app.models import PredictionRequest, PredictionResponse

api = Blueprint("api", __name__)


# =========================
# BEAUTIFUL HEALTH PAGE
# =========================
@api.route("/health")
def health():
    return """
    <html>
    <head>
        <title>Flask Pydantic API</title>

        <style>
            body {
                margin: 0;
                padding: 0;
                background-color: #0f172a;
                font-family: Arial, sans-serif;

                display: flex;
                justify-content: center;
                align-items: center;

                height: 100vh;
            }

            .card {
                background: #1e293b;
                padding: 40px;
                border-radius: 20px;

                box-shadow: 0px 0px 25px rgba(0,0,0,0.5);

                width: 450px;
                text-align: center;
            }

            h1 {
                color: #38bdf8;
                margin-bottom: 30px;
            }

            .success {
                color: #22c55e;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
            }

            .info {
                color: white;
                font-size: 18px;
                margin: 12px 0;
            }

            .footer {
                margin-top: 25px;
                color: #94a3b8;
                font-size: 14px;
            }
        </style>
    </head>

    <body>

        <div class="card">

            <h1>🚀 Flask Pydantic API</h1>

            <div class="success">
                ✅ API Status : Healthy
            </div>

            <div class="info">
                🐳 Docker Container : Running
            </div>

            <div class="info">
                ⚡ Flask Server : Active
            </div>

            <div class="info">
                🔥 Microservice : Working Successfully
            </div>

            <div class="footer">
                Built with Flask + Pydantic + Docker
            </div>

        </div>

    </body>
    </html>
    """


# =========================
# PREDICTION API
# =========================
@api.route("/predictions", methods=["POST"])
def predictions():

    try:
        data = request.get_json()

        validated_data = PredictionRequest(**data)

        result = PredictionResponse(
            prediction="positive",
            score=validated_data.confidence
        )

        return jsonify(result.model_dump())

    except ValidationError as e:
        return jsonify({
            "error": e.errors()
        }), 422


# =========================
# GET PREDICTION BY ID
# =========================
@api.route("/predictions/<int:prediction_id>", methods=["GET"])
def get_prediction(prediction_id):

    return jsonify({
        "prediction_id": prediction_id,
        "status": "success",
        "message": "Prediction fetched successfully"
    })