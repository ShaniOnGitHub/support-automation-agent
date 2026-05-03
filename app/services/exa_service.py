import httpx
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.services.ai_service import _log_error

class ExaSearchResult(BaseModel):
    title: Optional[str] = None
    url: str
    highlights: Optional[List[str]] = None

def search_exa(query: str, num_results: int = 3) -> Dict[str, Any]:
    """
    Calls the Exa Search API for web search results matching the query.
    Returns a dictionary with status and results.
    """
    api_key = settings.EXA_API_KEY
    if not api_key or api_key == "your_exa_key_here":
        return {"status": "failed", "error": "EXA_API_KEY not configured"}

    url = "https://api.exa.ai/search"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "type": "auto",
        "num_results": num_results,
        "contents": {
            "highlights": {
                "max_characters": 2000
            }
        }
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            results = []
            for item in data.get("results", []):
                extracted_highlights = item.get("highlights", [])
                
                results.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "highlights": extracted_highlights
                })
                
            return {"status": "success", "results": results}
    except Exception as e:
        _log_error(f"Exa Search Error: {e}")
        return {"status": "failed", "error": str(e)}
