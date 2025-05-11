from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from .api import image_router
from .auth import get_current_active_user
from .storage import STATIC_DIR
import os

app = FastAPI(title="Image Processing API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Mount static directory for serving images
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Routers will be included here
app.include_router(image_router.router)

# Health check endpoint
@app.get("/health")
@app.head("/health")
async def health_check():
    return {"status": "healthy"}

# Serve frontend files
@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")

@app.get("/login.html")
async def read_login():
    return FileResponse("frontend/login.html")

# Protected route example
@app.get("/protected")
async def protected_route(current_user = Depends(get_current_active_user)):
    return {"message": "This is a protected route", "user": current_user.username} 