import asyncio
import uuid
import json
import requests
from typing import List, Dict, Any, Optional, TypedDict
from datetime import datetime
import logging

from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver

from config import settings
from services.vector_store import VectorStore
from services.web_search import WebSearchService

logger = logging.getLogger(__name__)

class AgentState(TypedDict, total=False):
    messages: List[BaseMessage]
    query: str
    session_id: str
    document_results: Optional[List[Dict]]
    web_results: Optional[List[Dict]]
    final_prompt: Optional[List[BaseMessage]]
    sources: List[Dict]
    confidence: float
    error: Optional[str]

class AgentService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.2,
            max_tokens=4000
        )
        self.vector_store = VectorStore()
        self.web_search = WebSearchService()
        self.checkpointer = MemorySaver()
        self.graph = self._create_agent_graph()
        self.sessions: Dict[str, List[BaseMessage]] = {}

    def _create_agent_graph(self) -> StateGraph:
        """Create the LangGraph workflow for the agent"""
        
        # Define the workflow
        workflow = StateGraph(AgentState)
        
        # Add nodes - simplified to always search both
        workflow.add_node("search_both", self.search_both)
        workflow.add_node("generate_response", self.generate_response)
        
        # Set entry point
        workflow.set_entry_point("search_both")
        
        # Add edges
        workflow.add_edge("search_both", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile(checkpointer=self.checkpointer)

    async def search_both(self, state: AgentState) -> dict:
        """Always search both documents and web, then combine top 5 from each"""
        try:
            query = state["query"]
            logger.info(f"Searching both documents and web for query: {query}")
            
            # Search documents and web in parallel
            doc_task = self.vector_store.search_documents(query)
            web_task = self.web_search.search(query)
            
            doc_results, web_results = await asyncio.gather(
                doc_task, web_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(doc_results, Exception):
                logger.error(f"Document search failed: {doc_results}")
                doc_results = []
            
            if isinstance(web_results, Exception):
                logger.error(f"Web search failed: {web_results}")
                web_results = []
            
            # Take top 5 from each source
            top_doc_results = doc_results[:5] if doc_results else []
            top_web_results = web_results[:5] if web_results else []
            
            # Combine sources
            doc_sources = self._format_document_sources(top_doc_results)
            web_sources = self._format_web_sources(top_web_results)
            sources = doc_sources + web_sources
            
            logger.info(f"Found {len(top_doc_results)} document + {len(top_web_results)} web results")
            
            return {
                **state,
                "document_results": top_doc_results,
                "web_results": top_web_results,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Combined search failed: {e}")
            return {
                **state,
                "document_results": [],
                "web_results": [],
                "sources": [],
                "error": f"Combined search failed: {str(e)}"
            }

    async def generate_response(self, state: AgentState) -> dict:
        """Prepare the final prompt for the LLM based on search results."""
        try:
            logger.info("Starting response generation...")
            query = state["query"]
            doc_results = state.get("document_results", [])
            web_results = state.get("web_results", [])
            
            # Prepare context with top 5 from each source
            context_parts = []
            
            if doc_results:
                context_parts.append("--- DOCUMENT CONTEXT (Top 5 Results) ---")
                for i, result in enumerate(doc_results):
                    context_parts.append(f"[Doc {i+1}] {result['filename']} (Page {result['page_number']}):\\n{result['content'][:500]}...")
            
            if web_results:
                context_parts.append("--- WEB SEARCH CONTEXT (Top 5 Results) ---")
                for i, result in enumerate(web_results):
                    context_parts.append(f"[Web {i+1}] {result['title']}:\\n{result['snippet'][:300]}... (Source: {result['link']})")
            
            context = "\\n\\n".join(context_parts)
            
            # Create the list of messages for the LLM
            llm_messages = [
                SystemMessage(content="You are a helpful AI assistant. Answer the user's query based on the provided context from both document search and web search. Be comprehensive and cite sources using the format [Doc X] or [Web X]. If information from documents conflicts with web search, prioritize the most recent or authoritative source."),
                HumanMessage(content=f"CONTEXT:\\n{context}\\n\\nQUERY: {query}")
            ]

            return {**state, "final_prompt": llm_messages}

        except Exception as e:
            logger.error(f"Response preparation failed: {e}")
            return {**state, "error": f"Failed to prepare response prompt: {str(e)}"}

    def _format_document_sources(self, results: List[Dict]) -> List[Dict]:
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
                "snippet": res.get("content", ""),
                "page_number": res.get("page_number"),
                "document_id": res.get("document_id"),
                "filename": jpg_filename,  # Show as JPG filename
                "chunk_type": "image",  # Force to image type to show page images
                "chunk_id": res.get("id", ""),
                "has_images": res.get("has_images", False),
                "image_count": res.get("image_count", 0),
                "link": f"/api/documents/{res.get('document_id')}/page/{res.get('page_number')}/image",  # Direct link to image
                "page_image_url": f"/api/documents/{res.get('document_id')}/page/{res.get('page_number')}/image"
            }
            
            # Always show page images instead of text content
            source["has_large_image"] = True
            source["page_image_data"] = True  # Signal to frontend to load page image
            
            sources.append(source)
        return sources

    def _format_web_sources(self, results: List[Dict]) -> List[Dict]:
        """Format web search results into a standardized source format"""
        sources = []
        for res in results:
            sources.append({
                "type": "web",
                "title": res.get("title"),
                "snippet": res.get("snippet"),
                "link": res.get("link")
            })
        return sources

    def _calculate_confidence(self, doc_results: List[Dict], web_results: List[Dict]) -> float:
        """Calculate a confidence score based on search results"""
        # Simple confidence logic: more results = higher confidence
        doc_score = min(len(doc_results), 5) / 5.0
        web_score = min(len(web_results), 5) / 5.0
        
        if doc_results and web_results:
            return 0.7 * doc_score + 0.3 * web_score
        elif doc_results:
            return doc_score
        elif web_results:
            return web_score
        else:
            return 0.0

    async def get_response(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        if not session_id:
            session_id = str(uuid.uuid4())
        
        self.sessions.setdefault(session_id, [SystemMessage(content="You are a helpful AI assistant.")])
        self.sessions[session_id].append(HumanMessage(content=query))
        
        initial_state = AgentState(
            query=query,
            session_id=session_id,
            messages=self.sessions[session_id]
        )
        
        final_state = await self.graph.ainvoke(initial_state)
        
        self.sessions[session_id].append(AIMessage(content=final_state["final_response"]))
        
        return {
            "response": final_state["final_response"],
            "sources": final_state["sources"],
            "session_id": session_id
        }
        
    async def stream_response(self, query: str, session_id: Optional[str] = None):
        """Stream the response for a given query and session"""
        if not session_id:
            session_id = str(uuid.uuid4())

        # Ensure session exists
        session_history = self.sessions.setdefault(session_id, [])
        session_history.append(HumanMessage(content=query))
        
        # Prepare initial state
        initial_state = {
            "query": query,
            "session_id": session_id,
            "messages": session_history,
            "sources": [],
            "confidence": 0.0,
            "error": None,
            "final_prompt": None,
            "document_results": [],
            "web_results": []
        }
        
        # Run the graph to get the final state with the prompt
        try:
            logger.info(f"Starting graph execution with initial state: {initial_state}")
            final_state = await self.graph.ainvoke(initial_state)
            logger.info(f"Graph execution completed. Final state keys: {list(final_state.keys()) if final_state else 'None'}")
        except Exception as e:
            logger.error(f"Graph execution failed: {e}", exc_info=True)
            yield json.dumps({"type": "error", "data": f"Failed to process query: {str(e)}"})
            return

        if not final_state:
            yield json.dumps({"type": "error", "data": "Graph execution returned no result"})
            return

        if final_state.get("error"):
            yield json.dumps({"type": "error", "data": final_state["error"]})
            return

        final_prompt = final_state.get("final_prompt")
        if not final_prompt:
            yield json.dumps({"type": "error", "data": "Could not generate a response prompt."})
            return
            
        # Now, stream the LLM response
        try:
            logger.info("Starting LLM streaming...")
            async for chunk in self.llm.astream(final_prompt):
                if chunk.content:
                    yield json.dumps({"type": "response", "data": chunk.content})
            logger.info("LLM streaming completed")
        except Exception as e:
            logger.error(f"LLM streaming failed: {e}", exc_info=True)
            yield json.dumps({"type": "error", "data": f"Failed to generate response: {str(e)}"})
            return

        # At the end, send the sources
        sources = final_state.get("sources", [])
        logger.info(f"Sending {len(sources)} sources")
        yield json.dumps({"type": "sources", "data": sources})

    def health_check(self) -> bool:
        """Check if the agent service is healthy"""
        try:
            # Check if OpenAI API key is configured
            return bool(settings.openai_api_key)
        except:
            return False

    async def clear_session(self, session_id: str) -> bool:
        """Clear session history"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False
        except:
            return False

    async def get_session_history(self, session_id: str) -> List[Dict]:
        """Get session message history"""
        try:
            if session_id in self.sessions:
                history = []
                for message in self.sessions[session_id]:
                    history.append({
                        "type": message.__class__.__name__,
                        "content": message.content,
                        "timestamp": datetime.now().isoformat()
                    })
                return history
            return []
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return [] 