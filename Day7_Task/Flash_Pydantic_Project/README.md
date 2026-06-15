# Flask Pydantic Microservice Project

## 📌 Overview

This project is a REST microservice built using Flask and Pydantic.
It includes API validation, structured project architecture, pytest testing, and Docker containerization.

---

## 🚀 Features

* Flask App Factory Pattern
* Blueprint Routing
* Pydantic Request Validation
* REST API Endpoints
* Structured Error Handling
* Pytest Unit Testing
* Docker Support
* Health Monitoring Endpoint
* Beautiful Browser UI

---

## 📂 Project Structure

```bash
Flash_Pydantic_Project/
│
├── app/
│   ├── __init__.py
│   ├── errors.py
│   ├── logger.py
│   ├── models.py
│   └── routes.py
│
├── tests/
│   └── test_api.py
│
├── Dockerfile
├── requirements.txt
├── run.py
└── README.md
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone <your-github-repo-url>
cd Flash_Pydantic_Project
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run Application

```bash
python run.py
```

Application runs on:

```bash
http://127.0.0.1:5000
```

---

## ❤️ Health Endpoint

```bash
GET /health
```

Returns application health status.

---

## 🔮 Prediction Endpoint

```bash
POST /predictions
```

### Sample Request

```json
{
  "text": "hello",
  "confidence": 0.95
}
```

### Sample Response

```json
{
  "prediction": "positive",
  "score": 0.95
}
```

---

## 🧪 Run Tests

```bash
pytest
```

---

## 🐳 Docker Commands

### Build Docker Image

```bash
docker build -t flask-pydantic-app .
```

### Run Docker Container

```bash
docker run -p 5000:5000 flask-pydantic-app
```

---

## 🛠️ Technologies Used

* Flask
* Pydantic
* Pytest
* Docker
* Python

---

## ✅ Project Status

Completed Successfully
