# File: /home/roy/dev/personal/MFA-Token-Authenticator/backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routers import auth
from config import get_settings

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Modern replacement for @app.on_event("startup") and @app.on_event("shutdown")
    
    How it works:
    1. Code before 'yield' runs at startup
    2. 'yield' hands control to the application (app runs here)
    3. Code after 'yield' runs at shutdown
    """
    # Startup
    print("🚀 Starting MFA Token Authenticator API...")
    print(f"📊 Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
    init_db()
    print("✅ Database initialized")
    
    yield  # Application runs here
    
    # Shutdown (runs when server stops)
    print("👋 Shutting down MFA Token Authenticator API...")


# Create FastAPI application with lifespan
app = FastAPI(
    title=settings.app_name,
    description="MFA Token Authenticator API - Learn TOTP and secure authentication",
    version="1.0.0",
    docs_url="/api/docs",  # Swagger UI at http://localhost:8000/api/docs
    redoc_url="/api/redoc",  # ReDoc at http://localhost:8000/api/redoc
    lifespan=lifespan  # Register lifespan context manager
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server (alternative)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,  # Allow cookies and authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.get("/")
def root():
    """
    Root endpoint - API health check.
    
    Returns:
        dict: Welcome message and API status
    """
    return {
        "message": "MFA Token Authenticator API",
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/api/health")
def health_check():
    """
    Health check endpoint.
    
    Used by monitoring tools to verify API is running.
    
    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "mfa-auth-api"
    }


# Register routers
app.include_router(auth.router)