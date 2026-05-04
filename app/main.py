from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.routes import auth, halaman, latihan, kuis, profil, kelas, guru, murid
from app.database import engine, Base
import os

# Initialize database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GESTRA Fullstack API")

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
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )
