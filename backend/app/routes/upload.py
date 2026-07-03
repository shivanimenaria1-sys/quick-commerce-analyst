import io
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import pandas as pd
from app.services.data_ingestion import ingest_and_validate_dataframe, ColumnValidationError

router = APIRouter()

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Accepts a CSV file upload, parses it using Pandas,
    validates the required columns, and stores it in-memory.
    """
    # Verify file extension
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only CSV files are allowed."
        )
    
    # Read file contents
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is empty."
            )
        
        # Load CSV into DataFrame
        df = pd.read_csv(io.BytesIO(contents))
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded CSV file contains no data."
        )
    except pd.errors.ParserError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed CSV file. Please check the file formatting."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing CSV file: {str(e)}"
        )
        
    # Ingest and validate DataFrame
    try:
        session_id, rows, columns = ingest_and_validate_dataframe(df)
        return {
            "session_id": session_id,
            "rows": rows,
            "columns": columns
        }
    except ColumnValidationError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Missing required columns",
                "missing_columns": e.missing_columns
            }
        )
