from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import options
from app.config import settings

# Instantiates FastAPI app
app = FastAPI(
    title="Options Pricing API",
    description="Multi-model options pricing and Greeks calculation API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(options.router, prefix="/api/options", tags=["options"])

# Defines root GET endpoint
@app.get("/")
async def root():
    return {"message": "Options Pricing API is running"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models_available": ["black_scholes", "binomial", "monte_carlo"]
    }