import asyncio
import uuid
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import settings
from services.vector_store import VectorStore
from services.web_search import WebSearchService

logger = logging.getLogger(__name__)

class SimpleAgentService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.2
        )
        self.vector_store = VectorStore()
        self.web_search = WebSearchService()
        self.sessions: Dict[str, List[BaseMessage]] = {}

    async def search_both_sources(self, query: str) -> tuple[List[Dict], List[Dict]]:
        """Always search both documents and web, then return top 5 from each"""
        try:
            logger.info(f"Searching both documents and web for query: {query}")
            
            # Search documents and web in parallel
            doc_task = self.vector_store.search_documents(query)
            web_task = self.web_search.search(query)
            
            doc_results, web_results = await asyncio.gather(
                doc_task, web_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(doc_results, Exception):
                logger.error(f"Document search failed: {str(doc_results)}")
                doc_results = []
            
            if isinstance(web_results, Exception):
                logger.error(f"Web search failed: {str(web_results)}")
                web_results = []
            
            # Take top 5 from each source
            top_doc_results = doc_results[:5] if doc_results else []
            top_web_results = web_results[:5] if web_results else []
            
            logger.info(f"Found {len(top_doc_results)} document + {len(top_web_results)} web results")
            
            return top_doc_results, top_web_results
            
        except Exception as e:
            logger.error(f"Combined search failed: {e}")
            return [], []

    def format_document_sources(self, results: List[Dict]) -> List[Dict]:
        """Format document search results into a structured source list"""
        sources = []
        for res in results:
            # Create JPG filename from original PDF filename
            original_filename = res.get("filename", "Unknown Document")
            if original_filename.endswith('.pdf'):
                jpg_filename = original_filename[:-4] + f"_page_{res.get('page_number', 1)}.jpg"
            else:
                jpg_filename = f"{original_filename}_page_{res.get('page_number', 1)}.jpg"
            
            source = {
                "type": "document",
                "title": jpg_filename,
                "content": res.get("content", ""),
                "page_number": res.get("page_number"),
                "document_id": res.get("document_id"),
                "filename": jpg_filename,  # Show as JPG filename
                "chunk_type": "image",  # Force to image type to show page images
                "chunk_id": res.get("id", ""),
                "has_images": res.get("has_images", False),
                "image_count": res.get("image_count", 0),
                "page_image_url": f"/api/documents/{res.get('document_id')}/page/{res.get('page_number')}/image",
                "link": f"/api/documents/{res.get('document_id')}/page/{res.get('page_number')}/image"  # Direct link to image
            }
            
            # Always show page images instead of text content
            source["has_large_image"] = True
            source["page_image_data"] = True  # Signal to frontend to load page image
            
            sources.append(source)
        return sources

    def format_web_sources(self, results: List[Dict]) -> List[Dict]:
        """Format web search results into a standardized source format"""
        sources = []
        for res in results:
            sources.append({
                "type": "web",
                "title": res.get("title"),
                "content": res.get("snippet"),
                "url": res.get("link")
            })
        return sources

    async def generate_context(self, query: str, doc_results: List[Dict], web_results: List[Dict]) -> str:
        """Generate context from top 5 results from each source"""
        context_parts = []
        
        if doc_results:
            context_parts.append("--- DOCUMENT CONTEXT (Top 5 Results) ---")
            for i, result in enumerate(doc_results):
                context_parts.append(f"[Doc {i+1}] {result['filename']} (Page {result['page_number']}):\n{result['content'][:500]}...")
        
        if web_results:
            context_parts.append("--- WEB SEARCH CONTEXT (Top 5 Results) ---")
            for i, result in enumerate(web_results):
                context_parts.append(f"[Web {i+1}] {result['title']}:\n{result['snippet'][:300]}... (Source: {result['link']})")
        
        return "\n\n".join(context_parts)

    async def stream_response(self, query: str, session_id: Optional[str] = None):
        """Stream the response for a given query and session"""
        if not session_id:
            session_id = str(uuid.uuid4())

        logger.info(f"Processing query: {query}")

        try:
            # Step 1: Always search both documents and web
            doc_results, web_results = await self.search_both_sources(query)
            
            # Step 2: Generate context from top 5 results from each source
            context = await self.generate_context(query, doc_results, web_results)
            
            if not context:
                yield json.dumps({"type": "error", "data": "No relevant information found to answer your question."})
                return

            # Step 3: Create prompt for LLM
            system_message = SystemMessage(content="You are a helpful AI assistant. Answer the user's query based on the provided context from both document search and web search. Be comprehensive and cite sources using the format [Doc X] or [Web X]. If information from documents conflicts with web search, prioritize the most recent or authoritative source.")
            human_message = HumanMessage(content=f"CONTEXT:\n{context}\n\nQUERY: {query}")
            
            # Step 4: Stream LLM response
            logger.info("Starting LLM streaming...")
            async for chunk in self.llm.astream([system_message, human_message]):
                if chunk.content:
                    yield json.dumps({"type": "response", "data": chunk.content})
            
            # Step 5: Send sources
            sources = []
            sources.extend(self.format_document_sources(doc_results))
            sources.extend(self.format_web_sources(web_results))
            
            logger.info(f"Sending {len(sources)} sources")
            yield json.dumps({"type": "sources", "data": sources})

        except Exception as e:
            logger.error(f"Error in stream_response: {e}", exc_info=True)
            yield json.dumps({"type": "error", "data": f"Failed to process query: {str(e)}"})

    def health_check(self) -> bool:
        """Check if the agent service is healthy"""
        try:
            return bool(settings.openai_api_key)
        except:
            return False 