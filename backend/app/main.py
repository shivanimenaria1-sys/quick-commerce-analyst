from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.upload import router as upload_router
from app.routes.cleaning import router as cleaning_router
from app.routes.engineering import router as engineering_router
from app.routes.kpis import router as kpis_router
from app.routes.insights import router as insights_router
from app.routes.analysis import router as analysis_router
from app.routes.report import router as report_router

app = FastAPI(
    title="Quick Commerce Analyst API",
    description="API for the Quick Commerce Analyst tool",
    version="0.1.0"
)

# Set up origins allowed to connect to API
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

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
app.include_router(cleaning_router, prefix="/api", tags=["cleaning"])
app.include_router(engineering_router, prefix="/api", tags=["engineering"])
app.include_router(kpis_router, prefix="/api", tags=["kpis"])
app.include_router(insights_router, prefix="/api", tags=["insights"])
app.include_router(analysis_router, prefix="/api", tags=["analysis"])
app.include_router(report_router, prefix="/api", tags=["report"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
