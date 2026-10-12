import os
from fastapi import FastAPI
from dotenv import load_dotenv
from sqlalchemy import create_engine
from core.database.models import Base

# Load environment variables
load_dotenv()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing AfyaVoice Core Platform...")
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("Database tables verified.")
    yield
    print("AfyaVoice shutting down.")

# Initialize FastAPI App
app = FastAPI(
    title="AfyaVoice Core API",
    description="Sovereign Multilingual Healthcare Voice Triage & Telemedicine Platform",
    version="2.0.0",
    lifespan=lifespan
)

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./afyavoice.db"
)

# Initialize Database Engine
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

@app.get("/health")
def health_check():
    """
    Simple health check endpoint for Kubernetes/Docker orchestrators.
    """
    return {"status": "healthy", "service": "afyavoice-core"}

# Import and include routers
from api.webhooks.whatsapp import router as whatsapp_router
from api.portal.routes import router as portal_router
from api.portal.landing import landing_router

# Register the Landing Page router
app.include_router(
    landing_router,
    tags=["Landing"]
)

# Register the WhatsApp Webhook router
app.include_router(
    whatsapp_router, 
    prefix="/webhooks/whatsapp", 
    tags=["Webhooks"]
)

# Register the Web Telemedicine Portal & Simulator
app.include_router(
    portal_router,
    tags=["Portal"]
)

if __name__ == "__main__":
    import uvicorn
    # Run the application locally
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
