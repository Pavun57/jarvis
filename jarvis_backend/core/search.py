"""Web search using Serper.dev API."""
import sys
import http.client
import json
from pathlib import Path
from typing import List, Dict, Optional

# Add jarvis_backend to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings


class WebSearch:
    """Wrapper for Serper.dev (Google Search) API with DuckDuckGo fallback."""
    
    def __init__(self):
        self.api_key = settings.SERPER_API_KEY
        if not self.api_key:
            # Fallback to DuckDuckGo if Serper.dev key not provided
            try:
                from duckduckgo_search import DDGS
                self.ddgs = DDGS()
                self.use_serper = False
            except ImportError:
                self.use_serper = False
                self.ddgs = None
        else:
            self.use_serper = True
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Perform web search and return results."""
        if self.use_serper and self.api_key:
            return self._search_serper(query, max_results)
        else:
            return self._search_duckduckgo(query, max_results)
    
    def _search_serper(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search using Serper.dev API."""
        try:
            conn = http.client.HTTPSConnection("google.serper.dev")
            
            payload = json.dumps({
                "q": query,
                "num": max_results
            })
            
            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            conn.request("POST", "/search", payload, headers)
            res = conn.getresponse()
            data = res.read()
            response_data = json.loads(data.decode("utf-8"))
            
            results = []
            
            # Extract organic results
            if "organic" in response_data:
                for item in response_data["organic"][:max_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
            
            # If no organic results, try answer box or knowledge graph
            if not results:
                if "answerBox" in response_data:
                    answer = response_data["answerBox"]
                    results.append({
                        "title": answer.get("title", query),
                        "url": answer.get("link", ""),
                        "snippet": answer.get("answer", answer.get("snippet", ""))
                    })
                elif "knowledgeGraph" in response_data:
                    kg = response_data["knowledgeGraph"]
                    results.append({
                        "title": kg.get("title", query),
                        "url": kg.get("website", ""),
                        "snippet": kg.get("description", "")
                    })
            
            return results if results else [{"error": "No search results found"}]
        except Exception as e:
            return [{"error": f"Serper.dev search failed: {str(e)}"}]
    
    def _search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Fallback to DuckDuckGo search."""
        if not self.ddgs:
            return [{"error": "No search API configured. Please set SERPER_API_KEY in .env file"}]
        
        try:
            results = []
            search_results = self.ddgs.text(query, max_results=max_results)
            
            for result in search_results:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })
            
            return results if results else [{"error": "No search results found"}]
        except Exception as e:
            return [{"error": f"DuckDuckGo search failed: {str(e)}"}]
    
    def format_results(self, results: List[Dict[str, str]]) -> str:
        """Format search results as a readable string."""
        if not results:
            return "No search results found."
        
        formatted = []
        for i, result in enumerate(results, 1):
            if "error" in result:
                formatted.append(f"Error: {result['error']}")
            else:
                formatted.append(f"{i}. {result['title']}")
                formatted.append(f"   URL: {result['url']}")
                formatted.append(f"   {result['snippet']}")
                formatted.append("")
        
        return "\n".join(formatted)

