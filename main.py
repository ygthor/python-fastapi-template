# 1. main.py
from fastapi import FastAPI,Depends
from contextlib import asynccontextmanager
import os
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from dependencies.dev_auth import verify_dev_token
from api.routes import auth, dev, ai
from utils import add_logging_middleware

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Your Fast Api",
        version="1.0.0",
        description="With HTTPBearer auth in Swagger",
        routes=app.routes,
    )

    openapi_schema["servers"] = [
        {"url": API_ROOT_PATH or "/"}  # Show correct root in Swagger
    ]

    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # Optional: apply to all endpoints globally
    openapi_schema["security"] = [{"HTTPBearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


API_ROOT_PATH = os.getenv("API_ROOT_PATH")
app = FastAPI(
    root_path=API_ROOT_PATH
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_logging_middleware(app)
app.include_router(auth.router, prefix="/auth")

app.include_router(ai.router, prefix="/ai")

# Put at bottom
app.include_router(dev.router, prefix="/dev")
app.openapi = custom_openapi