import os
from pathlib import Path
from dotenv import load_dotenv

# Define the absolute path to backend/.env
BASE_DIR = Path(__file__).resolve().parents[1]
env_path = BASE_DIR / ".env"

if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# Verify that GEMINI_API_KEY is configured
if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError("Critical startup error: GEMINI_API_KEY is missing or empty in environment after loading .env.")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.upload import router as upload_router
from app.routes.insights import router as insights_router
from app.routes.analysis import router as analysis_router
from app.routes.report import router as report_router
from app.routes.semantic import router as semantic_router
from app.routes.processing import router as processing_router
from app.routes.kpi import router as kpi_router
from app.routes.visualization import router as visualization_router
from app.routes.evaluation import router as evaluation_router

app = FastAPI(
    title="Quick Commerce Analyst API",
    description="API for the Quick Commerce Analyst tool",
    version="0.1.0"
)

# Set up origins allowed to connect to API
cors_origins_env = os.getenv("CORS_ORIGINS", "")
origins = []
if cors_origins_env:
    origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

# Include development origins
dev_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]
for origin in dev_origins:
    if origin not in origins:
        origins.append(origin)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Register routes
app.include_router(upload_router, prefix="/api", tags=["ingestion"])
app.include_router(insights_router, prefix="/api", tags=["insights"])
app.include_router(analysis_router, prefix="/api", tags=["analysis"])
app.include_router(report_router, prefix="/api", tags=["report"])
app.include_router(semantic_router, prefix="/api", tags=["semantic"])
app.include_router(processing_router, prefix="/api", tags=["processing"])
app.include_router(kpi_router, prefix="/api", tags=["kpi"])
app.include_router(visualization_router, prefix="/api", tags=["visualization"])
app.include_router(evaluation_router, prefix="/api", tags=["evaluation"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
