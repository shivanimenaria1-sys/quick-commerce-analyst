import logging
import io
import pandas as pd
from abc import ABC, abstractmethod
from typing import Union, List

logger = logging.getLogger("dataset_profiler")

class BaseParser(ABC):
    """
    Abstract Base Class defining the parser interface.
    Allows future extensions to support Excel, Parquet, SQL, cloud databases, etc.
    """
    @abstractmethod
    def parse(self) -> pd.DataFrame:
        """
        Parses the data source and returns a pandas DataFrame.
        """
        pass


class CSVParser(BaseParser):
    """
    Concrete parser for structured CSV files.
    Robustly handles mixed encodings, headers, separator formats, and malformed rows.
    """
    def __init__(self, source: Union[str, bytes, io.BytesIO, io.StringIO], chunk_size: int = None):
        self.source = source
        self.chunk_size = chunk_size

    def clean_column_names(self, columns: List[str]) -> List[str]:
        """
        Cleans messy column names: strips whitespace, removes non-printable chars,
        and standardizes spacing. Detects and resolves duplicate headers dynamically
        to prevent key collision errors.
        """
        cleaned = []
        seen = {}
        for i, col in enumerate(columns):
            c_str = str(col).strip()
            # Remove control characters and non-printable characters
            c_str = "".join(ch for ch in c_str if ch.isprintable())
            # Replace double spaces with single space
            c_str = " ".join(c_str.split())
            
            # Support missing headers or unnamed columns
            if not c_str or c_str.lower().startswith("unnamed:"):
                c_str = f"unnamed_column_{i}"
                
            # Handle duplicates
            base_name = c_str
            suffix = 1
            while c_str in seen:
                c_str = f"{base_name}_{suffix}"
                suffix += 1
            seen[c_str] = True
            
            cleaned.append(c_str)
        return cleaned

    def parse(self) -> pd.DataFrame:
        """
        Reads CSV robustly trying fallback encodings: utf-8, latin-1, cp1252.
        Graces over bad/malformed rows and empty files.
        """
        encodings = ['utf-8', 'latin-1', 'cp1252']
        df = None
        last_err = None

        # Convert bytes to file-like object if needed
        if isinstance(self.source, bytes):
            buffer = io.BytesIO(self.source)
        elif isinstance(self.source, str) and not self.source.endswith('.csv') and ',' in self.source:
            buffer = io.StringIO(self.source)
        else:
            buffer = self.source

        for encoding in encodings:
            try:
                logger.info(f"Attempting to parse CSV with encoding: {encoding}")
                if hasattr(buffer, 'seek'):
                    buffer.seek(0)
                
                # Use on_bad_lines='skip' to skip malformed lines rather than crashing
                if self.chunk_size:
                    chunks = pd.read_csv(
                        buffer, 
                        encoding=encoding, 
                        nrows=self.chunk_size,
                        on_bad_lines='skip'
                    )
                    df = chunks
                else:
                    df = pd.read_csv(
                        buffer, 
                        encoding=encoding,
                        on_bad_lines='skip'
                    )
                
                logger.info(f"Successfully parsed CSV using encoding: {encoding}")
                break
            except Exception as e:
                logger.warning(f"Failed to parse CSV using encoding {encoding}: {e}")
                last_err = e
                continue

        if df is None:
            # Return an empty DataFrame rather than crashing if everything fails or file is completely empty
            logger.warning("Empty or completely malformed CSV dataset parsed. Returning empty DataFrame.")
            return pd.DataFrame()

        # Check for empty dataset rows
        if df.empty:
            logger.warning("Processed dataset has 0 rows.")

        # Clean column names
        df.columns = self.clean_column_names(list(df.columns))
        
        # Gracefully handle fully empty rows (all null)
        df.dropna(how='all', inplace=True)
        
        return df
