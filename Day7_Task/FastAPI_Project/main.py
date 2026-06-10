from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.orders import router as orders_router

app = FastAPI(
    title="Order Management API",
    description="FastAPI Nested Pydantic Demo",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders_router)


@app.get("/", tags=["Health"])
def health():
    return {
        "status": "ok",
        "message": "Order Management API is running 🚀"
    }