import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.services.dataset_profiler.parser import CSVParser
from app.services.dataset_profiler.profiler import profile_dataset
from app.services.semantic_mapper import map_semantics, save_correction

router = APIRouter(prefix="/semantic")
logger = logging.getLogger("dataset_profiler")

class CorrectionRequest(BaseModel):
    schema_fingerprint: str
    column_name: str
    original_role: str
    corrected_role: str

@router.post("/profile")
async def profile_and_map_semantics(file: UploadFile = File(...)):
    """
    Parses, cleans, and profiles an uploaded CSV file, then
    infers the semantic meaning of each column.
    Never sends the raw dataset to the LLM.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    try:
        logger.info(f"Received file upload for semantic profiling: {file.filename}")
        contents = await file.read()
        
        # 1. Parse dataset
        parser = CSVParser(contents)
        df = parser.parse()
        
        # Generate session ID and store in-memory
        import uuid
        from app.services.data_ingestion import sessions
        from app.services.dataset_profiler.parser import BaseParser
        
        session_id = str(uuid.uuid4())
        df.attrs['dataset_name'] = file.filename
        sessions[session_id] = df
        
        class PreparsedParser(BaseParser):
            def __init__(self, parsed_df):
                self.parsed_df = parsed_df
            def parse(self):
                return self.parsed_df
                
        # 2. Profile dataset using the preparsed data
        pre_parser = PreparsedParser(df)
        profile = profile_dataset(pre_parser)
        
        # 3. Map column semantics
        mapping = map_semantics(profile)
        
        return {
            "session_id": session_id,
            "profile": profile,
            "mapping": mapping
        }
    except Exception as e:
        logger.error(f"Error in profile_and_map_semantics route: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/correct")
def record_semantic_correction(request: CorrectionRequest):
    """
    Records a user correction override for a semantic column mapping
    and updates the active schema cache mapping.
    """
    try:
        save_correction(
            fingerprint=request.schema_fingerprint,
            column_name=request.column_name,
            original_role=request.original_role,
            corrected_role=request.corrected_role
        )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error recording semantic correction: {e}")
        raise HTTPException(status_code=500, detail=str(e))
