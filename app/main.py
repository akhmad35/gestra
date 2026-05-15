from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.routes import auth, halaman, latihan, kuis, profil, kelas, guru, murid
from app.database import engine, Base
import os

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("gestra")

# Initialize database
try:
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")

app = FastAPI(title="GESTRA Fullstack API")

@app.on_event("startup")
async def startup_event():
    logger.info("GESTRA System is starting up...")
    logger.info("Checking static directories...")
    if os.path.exists("app/static"):
        logger.info("app/static directory found.")
    else:
        logger.warning("app/static directory NOT found!")
    
    if os.path.exists("app/templates"):
        logger.info("app/templates directory found.")
    else:
        logger.warning("app/templates directory NOT found!")


# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(halaman.router)
app.include_router(latihan.router)
app.include_router(kuis.router)
app.include_router(profil.router)
app.include_router(kelas.router)
app.include_router(guru.router)
app.include_router(murid.router)

# Dummy ML endpoint
@app.post("/api/predict")
async def predict_model():
    return JSONResponse(content={
        "result": "A",
        "confidence": 0.9
    })

# Error handler for validation
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation Error: {exc.errors()} | Body: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Generic Error Handler to avoid unexplained ISE
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)}
    )

