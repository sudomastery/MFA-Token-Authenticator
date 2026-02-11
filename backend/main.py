# File: /home/roy/dev/personal/MFA-Token-Authenticator/backend/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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
        "http://localhost:8080",  # Vite dev server (actual port)
        "http://localhost:8081",  # Vite dev server (backup port)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081"
    ],
    allow_credentials=True,  # Allow cookies and authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Add request validation error handler for debugging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors for debugging and add CORS headers"""
    try:
        body = await request.body()
        print(f"\n❌ VALIDATION ERROR on {request.method} {request.url.path}")
        print(f"Request body: {body.decode('utf-8') if body else 'empty'}")
        
        # Safely serialize errors by converting bytes to string
        errors = []
        for error in exc.errors():
            error_dict = dict(error)
            # Convert bytes input to string if present
            if 'input' in error_dict and isinstance(error_dict['input'], bytes):
                error_dict['input'] = error_dict['input'].decode('utf-8', errors='replace')
            errors.append(error_dict)
        
        print(f"Validation errors: {errors}\n")
    except Exception as e:
        print(f"Error processing validation exception: {e}")
        errors = [{"type": "validation_error", "msg": "Request validation failed"}]
    
    # Create simplified error response
    error_messages = []
    for error in errors:
        field = error.get('loc', ['unknown'])[-1] if error.get('loc') else 'unknown'
        msg = error.get('msg', 'Validation error')
        error_messages.append(f"{field}: {msg}")
    
    # Create response with CORS headers
    response = JSONResponse(
        status_code=422,
        content={
            "detail": ", ".join(error_messages) if error_messages else "Validation failed",
            "errors": errors
        },
    )
    
    # Add CORS headers to error response
    origin = request.headers.get("origin")
    if origin in [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081"
    ]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response


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