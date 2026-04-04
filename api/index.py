import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import traceback
import tempfile
import shutil

# Add current directory to path for serverless imports
sys.path.append(str(Path(__file__).parent))

from rag import process_all, generate_answer, initialize_components, reset_vector_store

app = FastAPI(title="RAG API", version="1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestRequest(BaseModel):
    urls: Optional[List[str]] = None
    pdf_paths: Optional[List[str]] = None

class QueryRequest(BaseModel):
    query: str

@app.on_event("startup")
def startup_event():
    try:
        initialize_components()
        print("✅ Components initialized")
    except Exception as e:
        print("❌ Startup init error:", str(e))


@app.get("/")
def root():
    return {
        "message": "RAG API is running",
        "endpoints": {
            "health": "/health",
            "ingest": "/ingest",
            "query": "/query",
            "upload": "/upload"
        }
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a PDF file and return the saved path for ingestion."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    try:
        # Save to a temp file
        upload_dir = Path(__file__).parent / "pdf_files"
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        return {"path": str(file_path), "filename": file.filename}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def run_ingestion(urls, pdf_paths):
    try:
        for step in process_all(urls, pdf_paths):
            print("STEP:", step)
    except Exception as e:
        print("❌ Ingestion error:", str(e))
        traceback.print_exc()


@app.post("/ingest")
def ingest(req: IngestRequest, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(run_ingestion, req.urls, req.pdf_paths)

        return {
            "message": "Ingestion started in background",
            "note": "Check terminal logs for progress"
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
def query(req: QueryRequest):
    try:
        answer, sources = generate_answer(req.query)

        return {
            "answer": answer,
            "sources": list(set(sources))
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clear")
def clear():
    """Manual reset of the vector database."""
    try:
        if reset_vector_store():
            return {"message": "Vector database cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear vector database")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))