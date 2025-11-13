"""Skill to perform web searches."""
import sys
import urllib.parse
from pathlib import Path

# Add jarvis_cli to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from core.skill_registry import Skill
from core.search import WebSearch
from core.executor import Executor
from typing import Dict, Any, Tuple


class WebSearchSkill(Skill):
    """Performs web searches using DuckDuckGo or opens specific websites."""
    
    name = "web_search"
    description = "Searches the web for information or opens websites"
    
    def __init__(self):
        self.search = WebSearch()
        self.executor = Executor()
    
    def _is_website_specific_search(self, query: str) -> Tuple[bool, str]:
        """Check if query is for a specific website and return URL if so."""
        query_lower = query.lower()
        
        # YouTube searches - try to play video directly
        if "youtube" in query_lower or "play" in query_lower and ("song" in query_lower or "music" in query_lower or "video" in query_lower):
            # Extract search query (split into words to avoid removing substrings)
            words = query_lower.split()
            stop_words = {"youtube", "play", "search", "on", "in", "the", "a", "an"}
            search_query = " ".join([word for word in words if word not in stop_words]).strip()
            
            if search_query:
                # Use YouTube search with parameters that help with video results
                # Adding sp=EgIQAQ%253D%253D to prioritize videos
                encoded_query = urllib.parse.quote(search_query)
                # This URL format shows video results and makes it easier to click/play
                return True, f"https://www.youtube.com/results?search_query={encoded_query}&sp=EgIQAQ%253D%253D"
            return True, "https://www.youtube.com"
        
        # Google searches
        if "google" in query_lower and "search" in query_lower:
            search_query = query_lower.replace("google", "").replace("search", "").strip()
            if search_query:
                encoded_query = urllib.parse.quote(search_query)
                return True, f"https://www.google.com/search?q={encoded_query}"
        
        # Direct website names
        websites = {
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "facebook": "https://www.facebook.com",
            "twitter": "https://www.twitter.com",
            "instagram": "https://www.instagram.com",
            "github": "https://www.github.com",
            "stackoverflow": "https://www.stackoverflow.com",
            "reddit": "https://www.reddit.com",
        }
        
        for site_name, url in websites.items():
            if site_name in query_lower and ("open" in query_lower or "go to" in query_lower or "visit" in query_lower):
                return True, url
        
        return False, ""
    
    def _get_youtube_video_url(self, query: str) -> str:
        """Search for YouTube video and get the first video URL to play directly."""
        try:
            # Search YouTube specifically
            youtube_query = f"site:youtube.com/watch {query}"
            results = self.search.search(youtube_query, max_results=3)
            
            # Find the first YouTube video URL
            for result in results:
                url = result.get("url", "")
                if "youtube.com/watch" in url or "youtu.be" in url:
                    # Extract video ID if it's a youtu.be link
                    if "youtu.be" in url:
                        video_id = url.split("/")[-1].split("?")[0]
                        return f"https://www.youtube.com/watch?v={video_id}"
                    # If it's already a watch URL, use it directly
                    if "watch?v=" in url:
                        return url.split("&")[0]  # Remove extra parameters, keep just video ID
            
            # If no direct video found, fall back to search results page
            encoded_query = urllib.parse.quote(query)
            return f"https://www.youtube.com/results?search_query={encoded_query}&sp=EgIQAQ%253D%253D"
        except Exception:
            # Fallback to search page
            encoded_query = urllib.parse.quote(query)
            return f"https://www.youtube.com/results?search_query={encoded_query}&sp=EgIQAQ%253D%253D"
    
    def run(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the web search skill."""
        query = parameters.get("query", "")
        if not query:
            return {"success": False, "error": "query parameter required"}
        
        query_lower = query.lower()
        
        # Check if this is a "play" command - always treat as YouTube
        if "play" in query_lower:
            # Extract the actual search query (remove "play" and common words)
            # Split into words to avoid removing substrings within words
            words = query_lower.split()
            # Remove common command words (whole words only)
            stop_words = {"play", "youtube", "search", "on", "in", "the", "a", "an", "for", "me", "this", "song", "music", "video"}
            search_query = " ".join([word for word in words if word not in stop_words]).strip()
            
            if search_query:
                # Try to get the actual video URL to play
                video_url = self._get_youtube_video_url(search_query)
                result = self.executor.open_url(video_url)
                return {
                    "success": result.get("success", False),
                    "message": f"Playing {search_query} on YouTube",
                    "url": video_url
                }
            else:
                # Just open YouTube if no query
                result = self.executor.open_url("https://www.youtube.com")
                return {
                    "success": result.get("success", False),
                    "message": "Opened YouTube",
                    "url": "https://www.youtube.com"
                }
        
        # Check if this is a YouTube-specific search
        if "youtube" in query_lower:
            # Extract the actual search query (split into words to avoid removing substrings)
            words = query_lower.split()
            stop_words = {"youtube", "search", "on", "in", "the", "a", "an", "for"}
            search_query = " ".join([word for word in words if word not in stop_words]).strip()
            
            if search_query:
                # Try to get the actual video URL to play
                video_url = self._get_youtube_video_url(search_query)
                result = self.executor.open_url(video_url)
                return {
                    "success": result.get("success", False),
                    "message": f"Playing {search_query} on YouTube",
                    "url": video_url
                }
            else:
                # Just open YouTube
                result = self.executor.open_url("https://www.youtube.com")
                return {
                    "success": result.get("success", False),
                    "message": "Opened YouTube",
                    "url": "https://www.youtube.com"
                }
        
        # Check if this is a website-specific search that should open in browser
        is_website, url = self._is_website_specific_search(query)
        
        if is_website:
            # Open the URL in browser
            result = self.executor.open_url(url)
            return {
                "success": result.get("success", False),
                "message": result.get("message", f"Opened {url}"),
                "url": url
            }
        
        # Otherwise, do a regular web search
        max_results = parameters.get("max_results", 5)
        results = self.search.search(query, max_results=max_results)
        
        # Check if results contain YouTube URLs - if so, open the first one
        youtube_url = None
        for result in results:
            if "error" not in result:
                url = result.get("url", "")
                if "youtube.com/watch" in url or "youtu.be" in url:
                    # Extract clean video URL
                    if "youtu.be" in url:
                        video_id = url.split("/")[-1].split("?")[0]
                        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                    elif "watch?v=" in url:
                        # Get just the video ID part
                        youtube_url = url.split("&")[0]  # Remove extra parameters
                    else:
                        youtube_url = url
                    break
        
        # If we found a YouTube URL and query seems to be about playing/searching, open it
        if youtube_url and ("play" in query_lower or "song" in query_lower or "music" in query_lower or "video" in query_lower):
            result = self.executor.open_url(youtube_url)
            return {
                "success": result.get("success", False),
                "message": f"Playing video on YouTube",
                "url": youtube_url,
                "results": results
            }
        
        # Otherwise, return formatted results
        formatted = self.search.format_results(results)
        
        return {
            "success": True,
            "results": results,
            "formatted": formatted
        }

