import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from urllib.parse import urlparse

from config import settings

logger = logging.getLogger(__name__)

class WebSearchService:
    def __init__(self):
        self.api_key = settings.serper_api_key
        self.base_url = "https://google.serper.dev/search"
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def search(self, query: str, num_results: int = None) -> List[Dict[str, Any]]:
        """Perform web search using Serper.dev API"""
        try:
            num_results = num_results or settings.serper_num_results
            
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": min(num_results, 20),  # Serper limits to 20 results
                "gl": "us",  # Country (US)
                "hl": "en"   # Language (English)
            }
            
            session = await self._get_session()
            
            async with session.post(self.base_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_search_results(data)
                else:
                    logger.error(f"Serper API error: {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error details: {error_text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []

    def _parse_search_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Serper API response into standardized format"""
        try:
            results = []
            
            # Parse organic results
            organic_results = data.get("organic", [])
            
            for result in organic_results:
                parsed_result = {
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "domain": self._extract_domain(result.get("link", "")),
                    "position": result.get("position", 0),
                    "date": result.get("date", ""),
                    "type": "organic"
                }
                
                # Clean and enhance the snippet
                parsed_result["snippet"] = self._clean_snippet(parsed_result["snippet"])
                
                results.append(parsed_result)
            
            # Parse knowledge graph if available
            knowledge_graph = data.get("knowledgeGraph", {})
            if knowledge_graph:
                kg_result = {
                    "title": knowledge_graph.get("title", ""),
                    "link": knowledge_graph.get("website", ""),
                    "snippet": knowledge_graph.get("description", ""),
                    "domain": self._extract_domain(knowledge_graph.get("website", "")),
                    "position": 0,  # Give knowledge graph high priority
                    "date": "",
                    "type": "knowledge_graph",
                    "attributes": knowledge_graph.get("attributes", {})
                }
                
                # Insert knowledge graph at the beginning
                results.insert(0, kg_result)
            
            # Parse answer box if available
            answer_box = data.get("answerBox", {})
            if answer_box:
                answer_result = {
                    "title": answer_box.get("title", "Direct Answer"),
                    "link": answer_box.get("link", ""),
                    "snippet": answer_box.get("answer", "") or answer_box.get("snippet", ""),
                    "domain": self._extract_domain(answer_box.get("link", "")),
                    "position": 0,  # Give answer box highest priority
                    "date": "",
                    "type": "answer_box"
                }
                
                # Insert answer box at the very beginning
                results.insert(0, answer_result)
            
            # Parse related searches for context
            related_searches = data.get("relatedSearches", [])
            if related_searches:
                # Add related searches as metadata to the first result
                if results:
                    results[0]["related_searches"] = [
                        search.get("query", "") for search in related_searches[:5]
                    ]
            
            logger.info(f"Parsed {len(results)} web search results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to parse search results: {e}")
            return []

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            if not url:
                return ""
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
                
            return domain
            
        except:
            return ""

    def _clean_snippet(self, snippet: str) -> str:
        """Clean and enhance snippet text"""
        try:
            if not snippet:
                return ""
            
            # Remove extra whitespace
            snippet = re.sub(r'\s+', ' ', snippet).strip()
            
            # Remove date prefixes like "3 days ago"
            snippet = re.sub(r'^\d+\s+(days?|hours?|minutes?|weeks?|months?|years?)\s+ago\s*[·-]?\s*', '', snippet)
            
            # Limit length
            if len(snippet) > 300:
                snippet = snippet[:297] + "..."
            
            return snippet
            
        except:
            return snippet

    async def search_news(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search for recent news articles"""
        try:
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": min(num_results, 10),
                "gl": "us",
                "hl": "en",
                "tbm": "nws"  # News search
            }
            
            session = await self._get_session()
            
            async with session.post(self.base_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_news_results(data)
                else:
                    logger.error(f"News search error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"News search failed: {e}")
            return []

    def _parse_news_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse news search results"""
        try:
            results = []
            news_results = data.get("news", [])
            
            for result in news_results:
                parsed_result = {
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "domain": self._extract_domain(result.get("link", "")),
                    "date": result.get("date", ""),
                    "source": result.get("source", ""),
                    "type": "news",
                    "position": result.get("position", 0)
                }
                
                # Clean snippet
                parsed_result["snippet"] = self._clean_snippet(parsed_result["snippet"])
                
                results.append(parsed_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to parse news results: {e}")
            return []

    async def search_images(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search for images (basic implementation)"""
        try:
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": min(num_results, 10),
                "gl": "us",
                "hl": "en",
                "tbm": "isch"  # Image search
            }
            
            session = await self._get_session()
            
            async with session.post(self.base_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_image_results(data)
                else:
                    logger.error(f"Image search error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Image search failed: {e}")
            return []

    def _parse_image_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse image search results"""
        try:
            results = []
            images = data.get("images", [])
            
            for result in images:
                parsed_result = {
                    "title": result.get("title", ""),
                    "image_url": result.get("imageUrl", ""),
                    "thumbnail_url": result.get("thumbnailUrl", ""),
                    "source_url": result.get("link", ""),
                    "domain": self._extract_domain(result.get("link", "")),
                    "width": result.get("imageWidth", 0),
                    "height": result.get("imageHeight", 0),
                    "type": "image",
                    "position": result.get("position", 0)
                }
                
                results.append(parsed_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to parse image results: {e}")
            return []

    async def get_search_suggestions(self, query: str) -> List[str]:
        """Get search suggestions for autocomplete"""
        try:
            # This would typically use Google's suggestion API
            # For now, return some basic suggestions based on the query
            suggestions = []
            
            # Add basic question variations
            question_starters = ["what is", "how to", "why does", "when did", "where is"]
            for starter in question_starters:
                if not query.lower().startswith(starter):
                    suggestions.append(f"{starter} {query}")
            
            return suggestions[:5]
            
        except Exception as e:
            logger.error(f"Failed to get suggestions: {e}")
            return []

    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

    def health_check(self) -> bool:
        """Check if web search service is healthy"""
        try:
            return bool(self.api_key)
        except:
            return False

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close() 