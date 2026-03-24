from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import configure_logging, RequestIdMiddleware
from app.api.v1.routes import router as api_router

# Configure logging first
configure_logging()

app = FastAPI(title=settings.APP_NAME)

# Add Request ID Middleware
app.add_middleware(RequestIdMiddleware)

# Include API Router
app.include_router(api_router, prefix="/api/v1")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "details": str(exc)},
    )

@app.get("/")
async def root():
    return {"message": "Welcome to SupportAutomationAgent API"}
