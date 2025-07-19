import os
import asyncio
from typing import List, Optional
import logging

from fastapi import FastAPI, UploadFile, File, WebSocket, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from services.pdf_processor import PDFProcessor
from services.voice_service import VoiceService
from services.agent_service_simple import SimpleAgentService
from services.vector_store import VectorStore
from config import settings, ensure_upload_dir

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VoiceRAG API", version="1.0.0")


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
pdf_processor = PDFProcessor()
voice_service = VoiceService()
agent_service = SimpleAgentService()
vector_store = VectorStore()

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    source_type: str  # "document" or "web"
    sources: List[dict]
    session_id: str

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Ensure upload directory exists
    ensure_upload_dir()
    
    # Initialize vector store
    await vector_store.initialize()
    print("VoiceRAG API started successfully!")

@app.get("/")
async def root():
    return {"message": "VoiceRAG API is running"}

@app.post("/api/documents/upload", response_model=dict)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process PDF file"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save uploaded file and get both paths
        file_path, original_filename = await pdf_processor.save_uploaded_file(file)
        
        # Process PDF and store in vector database
        result = await pdf_processor.process_pdf(file_path, original_filename)
        
        return {
            "success": True,
            "message": f"PDF '{original_filename}' uploaded and processed successfully",
            "document_id": result["document_id"],
            "pages_processed": result["pages_processed"],
            "chunks_created": result["chunks_created"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/api/chat/stream")
async def process_query(request: QueryRequest):
    """Process user query using the agent and stream the response"""
    try:
        from fastapi.responses import StreamingResponse
        
        async def event_generator():
            async for chunk in agent_service.stream_response(
                query=request.query, session_id=request.session_id
            ):
                if chunk:
                    yield f"data: {chunk}\n\n"
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")
        
    except Exception as e:
        logger.error(f"Error processing query stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/api/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        documents = await vector_store.list_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the vector store"""
    try:
        await vector_store.delete_document(document_id)
        return {"success": True, "message": f"Document {document_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.get("/api/documents/{document_id}/file")
async def get_document_file(document_id: str):
    """Get the file content for a document"""
    try:
        logger.info(f"PDF request for document ID: {document_id}")
        
        file_path = await vector_store.get_document_filepath(document_id)
        if not file_path or not os.path.exists(file_path):
            logger.error(f"File not found for document {document_id}: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")
        
        logger.info(f"Serving PDF from: {file_path}")
        
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
        
        headers = {
            'Content-Disposition': f'inline; filename="{os.path.basename(file_path)}"',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': '*',
            'Cache-Control': 'no-cache'
        }
        
        logger.info(f"Returning PDF: {len(pdf_bytes)} bytes")
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

    except Exception as e:
        logger.error(f"Error serving PDF for document {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting document file: {str(e)}")

@app.get("/api/documents/{document_id}/page/{page_number}/image")
async def get_page_image(document_id: str, page_number: int):
    """Get a page image as JPG from a document"""
    try:
        logger.info(f"Page image request for document ID: {document_id}, page: {page_number}")
        
        file_path = await vector_store.get_document_filepath(document_id)
        if not file_path or not os.path.exists(file_path):
            logger.error(f"File not found for document {document_id}: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")
        
        # Generate page image
        page_image_bytes = await pdf_processor.generate_page_image(file_path, page_number)
        
        if not page_image_bytes:
            raise HTTPException(status_code=404, detail="Page image not found")
        
        headers = {
            'Content-Type': 'image/jpeg',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': '*',
            'Cache-Control': 'public, max-age=3600'  # Cache for 1 hour
        }
        
        logger.info(f"Returning page image: {len(page_image_bytes)} bytes")
        return Response(content=page_image_bytes, media_type="image/jpeg", headers=headers)

    except Exception as e:
        logger.error(f"Error serving page image for document {document_id}, page {page_number}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting page image: {str(e)}")

@app.get("/api/chunks/{chunk_id}/image")
async def get_chunk_image(chunk_id: str):
    """Get extracted image data from a specific chunk"""
    try:
        logger.info(f"Chunk image request for chunk ID: {chunk_id}")
        
        # Query the vector store to get the chunk by ID
        dummy_embedding = [0.1] * settings.embedding_dimensions
        results = await vector_store.index.fetch(ids=[chunk_id])
        
        if not results.vectors or chunk_id not in results.vectors:
            raise HTTPException(status_code=404, detail="Chunk not found")
        
        chunk_data = results.vectors[chunk_id]
        metadata = chunk_data.metadata
        
        # Check if this chunk has image data
        if not metadata.get("image_data"):
            raise HTTPException(status_code=404, detail="No image data in this chunk")
        
        # Decode base64 image data
        import base64
        image_data = base64.b64decode(metadata["image_data"])
        
        headers = {
            'Content-Type': 'image/png',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': '*',
            'Cache-Control': 'public, max-age=3600'  # Cache for 1 hour
        }
        
        logger.info(f"Returning chunk image: {len(image_data)} bytes")
        return Response(content=image_data, media_type="image/png", headers=headers)

    except Exception as e:
        logger.error(f"Error serving chunk image for chunk {chunk_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting chunk image: {str(e)}")


@app.websocket("/api/voice/stream")
async def websocket_voice_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time voice transcription"""
    try:
        await websocket.accept()
        logger.info("WebSocket connection accepted, starting voice service...")
        await voice_service.handle_voice_stream(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            if websocket.client_state.name == "CONNECTED":
                await websocket.close(code=1000, reason=str(e))
        except Exception as close_error:
            logger.error(f"Error closing WebSocket: {close_error}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "vector_store": await vector_store.health_check(),
            "pdf_processor": pdf_processor.health_check(),
            "voice_service": voice_service.health_check(),
            "agent_service": agent_service.health_check()
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 