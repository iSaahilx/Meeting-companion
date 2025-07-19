import asyncio
import uuid
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from config import settings
import logging
import os

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.pinecone = Pinecone(api_key=settings.pinecone_api_key)
        self.index = None
        self.initialized = False

    async def initialize(self):
        """Initialize Pinecone connection and index. Create index if it doesn't exist."""
        try:
            index_name = settings.pinecone_index_name
            
            if index_name not in self.pinecone.list_indexes().names():
                logger.info(f"Index '{index_name}' not found. Creating a new one...")
                self.pinecone.create_index(
                    name=index_name,
                    dimension=settings.embedding_dimensions,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-west-2"
                    )
                )
                logger.info(f"Index '{index_name}' created successfully.")

            self.index = self.pinecone.Index(index_name)
            self.initialized = True
            logger.info(f"Vector store initialized successfully. Connected to index: '{index_name}'")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts using OpenAI"""
        try:
            response = self.client.embeddings.create(
                model=settings.embedding_model,
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            logger.error(f"Failed to create embeddings: {e}")
            raise

    async def store_document_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        document_id: str,
        filename: str
    ) -> Dict[str, Any]:
        """Store document chunks in the vector database"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Prepare texts for embedding
            texts = [chunk["content"] for chunk in chunks]
            
            # Create embeddings
            embeddings = self.create_embeddings(texts)
            
            # Prepare vectors for upsert
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{document_id}_{i}"
                metadata = {
                    "document_id": document_id,
                    "filename": filename,
                    "original_filename": chunk.get("original_filename", filename),  # Store original filename
                    "page_number": chunk.get("page_number", 0),
                    "content": chunk["content"],
                    "chunk_index": i,
                    "section_title": chunk.get("section_title", ""),
                    "chunk_type": chunk.get("chunk_type", "text"),
                    "has_images": chunk.get("has_images", False),
                    "image_count": chunk.get("image_count", 0),
                }
                
                # Store image data for image chunks (if it's small enough for metadata)
                if chunk.get("chunk_type") == "image" and chunk.get("image_data"):
                    # Store image data for small images only (Pinecone has metadata size limits)
                    image_data = chunk.get("image_data", "")
                    if len(image_data) < 30000:  # About 30KB limit for metadata
                        metadata["image_data"] = image_data
                    else:
                        metadata["has_large_image"] = True
                
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Upsert vectors to Pinecone
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            logger.info(f"Stored {len(vectors)} chunks for document {document_id}")
            
            return {
                "document_id": document_id,
                "chunks_stored": len(vectors),
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"Failed to store document chunks: {e}")
            raise

    async def search_documents(
        self, 
        query: str, 
        top_k: int = None,
        filter_dict: Dict = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant document chunks"""
        try:
            if not self.initialized:
                await self.initialize()
            
            top_k = top_k or settings.top_k_results
            
            # Create embedding for the query
            query_embedding = self.create_embeddings([query])[0]
            
            # Search in Pinecone
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            results = []
            for match in search_results.matches:
                if match.score >= settings.similarity_threshold:
                    result = {
                        "id": match.id,
                        "score": float(match.score),
                        "content": match.metadata.get("content", ""),
                        "page_number": match.metadata.get("page_number", 0),
                        "filename": match.metadata.get("original_filename", match.metadata.get("filename", "")),
                        "document_id": match.metadata.get("document_id", ""),
                        "section_title": match.metadata.get("section_title", ""),
                        "chunk_type": match.metadata.get("chunk_type", "text"),
                        "has_images": match.metadata.get("has_images", False),
                        "image_count": match.metadata.get("image_count", 0),
                    }
                    
                    # Include image data if available
                    if match.metadata.get("image_data"):
                        result["image_data"] = match.metadata.get("image_data")
                    elif match.metadata.get("has_large_image"):
                        result["has_large_image"] = True
                    
                    results.append(result)
            
            logger.info(f"Found {len(results)} relevant chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            raise

    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the vector store using fetch operation"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Use index stats to get namespace information
            stats = self.index.describe_index_stats()
            
            # Since we can't easily get all document IDs without knowing them,
            # we'll use a different approach: query for a sample and extract unique docs
            # This is not ideal but works for small datasets
            
            # Create a dummy query to get some results
            dummy_embedding = [0.1] * settings.embedding_dimensions
            sample_results = self.index.query(
                vector=dummy_embedding,
                top_k=10000,  # Get many results to find all documents
                include_metadata=True
            )
            
            # Extract unique documents from results
            documents = {}
            for match in sample_results.matches:
                doc_id = match.metadata.get("document_id")
                # Prioritize original_filename over filename
                original_filename = match.metadata.get("original_filename")
                filename = match.metadata.get("filename")
                
                # Use original filename if available, otherwise fall back to filename
                display_filename = original_filename if original_filename else filename
                
                if doc_id and doc_id not in documents:
                    documents[doc_id] = {
                        "document_id": doc_id,
                        "filename": display_filename,
                        "chunk_count": 0
                    }
                
                if doc_id:
                    documents[doc_id]["chunk_count"] += 1
            
            return list(documents.values())
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []

    async def delete_document(self, document_id: str):
        """Delete all chunks for a specific document and remove the physical file"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # First, get the file path before deleting from vector store
            file_path = await self.get_document_filepath(document_id)
            
            # Use filter to find vectors with this document_id
            # First, we need to get the vector IDs
            dummy_embedding = [0.1] * settings.embedding_dimensions
            results = self.index.query(
                vector=dummy_embedding,
                top_k=10000,
                include_metadata=True,
                filter={"document_id": document_id}
            )
            
            # Delete all matching vectors from Pinecone
            vector_ids = [match.id for match in results.matches]
            
            if vector_ids:
                # Delete in batches
                batch_size = 1000
                for i in range(0, len(vector_ids), batch_size):
                    batch = vector_ids[i:i + batch_size]
                    self.index.delete(ids=batch)
                
                logger.info(f"Deleted {len(vector_ids)} chunks for document {document_id}")
            else:
                logger.warning(f"No vector chunks found for document {document_id}")
            
            # Delete the physical file if it exists
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted physical file: {file_path}")
                except OSError as e:
                    logger.error(f"Failed to delete physical file {file_path}: {e}")
                    raise Exception(f"Failed to delete physical file: {str(e)}")
            else:
                logger.warning(f"Physical file not found for document {document_id}: {file_path}")
            
            return {
                "success": True,
                "message": f"Document {document_id} and associated file deleted successfully",
                "chunks_deleted": len(vector_ids),
                "file_deleted": file_path is not None and os.path.exists(file_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise Exception(f"Failed to delete document: {str(e)}")

    async def get_document_filename(self, document_id: str) -> Optional[str]:
        """Get the filename for a specific document_id."""
        try:
            # Use a dummy query with filter to find the document
            dummy_embedding = [0.1] * settings.embedding_dimensions
            response = self.index.query(
                vector=dummy_embedding,
                top_k=1,
                filter={"document_id": document_id},
                include_metadata=True
            )
            if response.matches:
                return response.matches[0].metadata.get("filename")
            return None
        except Exception as e:
            logger.error(f"Failed to get document filename: {e}")
            return None

    async def get_document_filepath(self, document_id: str) -> Optional[str]:
        """Construct the full file path for a given document_id."""
        filename = await self.get_document_filename(document_id)
        if not filename:
            logger.warning(f"No filename found for document_id: {document_id}")
            return None
        
        file_path = os.path.join(settings.upload_dir, filename)
        
        # Check if the file actually exists
        if os.path.exists(file_path):
            logger.info(f"Found file for document {document_id}: {file_path}")
            return file_path
        else:
            logger.warning(f"File not found at path: {file_path}")
            # List all files in uploads directory for debugging
            if os.path.exists(settings.upload_dir):
                existing_files = os.listdir(settings.upload_dir)
                logger.info(f"Available files in uploads: {existing_files}")
            else:
                logger.warning(f"Uploads directory does not exist: {settings.upload_dir}")
            return None

    async def health_check(self) -> bool:
        """Check if the vector store is healthy"""
        try:
            if not self.initialized:
                return False
            
            # Try to get index stats
            stats = self.index.describe_index_stats()
            return True
            
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return False 