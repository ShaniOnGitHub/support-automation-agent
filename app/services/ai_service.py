from google import genai
from google.genai import types
import datetime
import time
import json
import httpx
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.config import settings

class TriageResult(BaseModel):
    priority: str = Field(..., description="The priority of the ticket: 'low', 'medium', 'high', or 'urgent'")
    sentiment: str = Field(..., description="Brief description of user sentiment (e.g., 'frustrated', 'neutral', 'satisfied')")
    summary: str = Field(..., description="A concise 1-sentence summary of the core issue")

class ProposedAction(BaseModel):
    tool_name: str = Field(..., description="The name of the tool, e.g., 'check_order_status'")
    parameters: dict = Field(..., description="JSON parameters, e.g., {'order_id': '555'}")

class ProposedActionsList(BaseModel):
    actions: List[ProposedAction]

def _log_error(msg: str):
    with open("error_log.txt", "a") as f:
        f.write(f"{datetime.datetime.now()}: {msg}\n")

def _get_gemini_client():
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_key_here":
        return None
    return genai.Client(api_key=settings.GEMINI_API_KEY)

def _call_with_retry(fn, retries=4, initial_delay=2):
    """
    Calls the provided function with exponential backoff on 429/quota errors.
    """
    last_err = None
    delay = initial_delay
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            last_err = e
            err_str = str(e)
            if "quota" in err_str.lower() or "429" in err_str or "rate" in err_str.lower():
                _log_error(f"Rate limit hit (attempt {attempt+1}): {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2 # Exponential backoff
            else:
                _log_error(f"AI Call Error (attempt {attempt+1}): {e}")
                raise e # Don't retry non-rate errors
    raise last_err

def _call_xai_responses_api(prompt: str) -> str:
    """
    Call the new xAI /responses API as seen in the user dashboard.
    Endpoint: https://api.x.ai/v1/responses
    Model: grok-4.20-reasoning
    """
    if not settings.XAI_API_KEY:
        raise ValueError("XAI_API_KEY is not set")
    
    url = "https://api.x.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {settings.XAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "grok-4.20-reasoning", # Exact model from your screenshot
        "input": prompt
    }

    def request():
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            # The new /responses API returns 'message' or 'response' in the root
            data = resp.json()
            # Try common keys for the new API response
            return data.get("message", data.get("response", data.get("output", "")))

    return _call_with_retry(request)

def _call_exa_chat_api(prompt: str) -> str:
    """
    Call Exa's OpenAI-compatible chat completions API.
    """
    if not settings.EXA_API_KEY:
        raise ValueError("EXA_API_KEY is not set")
        
    url = "https://api.exa.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.EXA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "exa",
        "messages": [
            {"role": "system", "content": "You are a helpful customer support AI. If formatting JSON, do NOT use markdown code blocks."},
            {"role": "user", "content": prompt}
        ]
    }
    
    def request():
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].replace("```json", "").replace("```", "")
            
    return _call_with_retry(request)

def classify_ticket_with_gemini(subject: str, body: str) -> TriageResult | None:
    """
    Provider-agnostic classification.
    """
    if settings.AI_PROVIDER in ("xai", "exa"):
        try:
            prompt = (
                f"Analyze this support ticket and provide triage data in JSON format.\n"
                f"Subject: {subject}\n"
                f"Body: {body}\n\n"
                "Return a JSON object with: priority (low/medium/high/urgent), sentiment, summary."
            )
            content = _call_exa_chat_api(prompt) if settings.AI_PROVIDER == "exa" else _call_xai_responses_api(prompt)
            # Find JSON in the response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end != -1:
                content = content[start:end]
            
            data = json.loads(content)
            return TriageResult(**data)
        except Exception as e:
            _log_error(f"{settings.AI_PROVIDER.upper()} Triage Error: {e}")
            # Minimal fallback triage
            return TriageResult(priority="medium", sentiment="neutral", summary=subject[:50])
    else:
        # Gemini logic...
        client = _get_gemini_client()
        if not client: return None
        try:
            response = _call_with_retry(lambda: client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"Analyze this ticket: {subject} - {body}",
                config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=TriageResult)
            ))
            return response.parsed if response and response.parsed else None
        except Exception as e:
            _log_error(f"Gemini Triage Error: {e}")
            return None

def generate_suggested_reply(subject: str, description: str, context: str = "") -> str | None:
    """
    Generate a suggested reply.
    """
    if settings.AI_PROVIDER in ("xai", "exa"):
        try:
            prompt = f"Support Context: {context}\n\nDraft a polite reply to: {subject} - {description}"
            return _call_exa_chat_api(prompt) if settings.AI_PROVIDER == "exa" else _call_xai_responses_api(prompt)
        except Exception as e:
            _log_error(f"{settings.AI_PROVIDER.upper()} Suggestion Error: {e}")
            return f"Hello, I am looking into your issue regarding '{subject}' now."
    else:
        client = _get_gemini_client()
        if not client: return None
        try:
            prompt = f"Context: {context}\nReply to: {subject} - {description}"
            response = _call_with_retry(lambda: client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            ))
            return response.text.strip() if response and response.text else None
        except Exception as e:
            _log_error(f"Gemini Suggestion Error: {e}")
            return None

def generate_embeddings(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float] | None:
    client = _get_gemini_client()
    if not client: return None
    try:
        res = client.models.embed_content(model="text-embedding-004", contents=text)
        return res.embeddings[0].values if res.embeddings else None
    except Exception as e:
        _log_error(f"Gemini Embeddings Error: {e}")
        return None

def propose_actions_for_ticket(subject: str, body: str) -> List[ProposedAction]:
    """
    Propose tools using xAI or Gemini.
    """
    if settings.AI_PROVIDER in ("xai", "exa"):
        try:
            prompt = (
                f"Propose diagnostic tools for: {subject} {body}\n"
                "Available tools: check_order_status(order_id), check_refund_status(order_id), search_web(query).\n\n"
                "Return a JSON object with 'actions' list."
            )
            content = _call_exa_chat_api(prompt) if settings.AI_PROVIDER == "exa" else _call_xai_responses_api(prompt)
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end != -1:
                content = content[start:end]
            
            data = json.loads(content)
            actions_list = data.get("actions", [])
            return [ProposedAction(**a) for a in actions_list]
        except Exception as e:
            _log_error(f"{settings.AI_PROVIDER.upper()} Action Proposal Error: {e}")
            return []
    else:
        # Gemini logic...
        client = _get_gemini_client()
        if not client: return []
        try:
            prompt = f"List tools in JSON list for: {subject} {body}\nAvailable tools: check_order_status(order_id), check_refund_status(order_id), search_web(query)."
            response = _call_with_retry(lambda: client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            ))
            if response and response.text:
                data = json.loads(response.text)
                actions_data = data.get("actions", [])
                return [ProposedAction(**a) for a in actions_data]
            return []
        except Exception as e:
            _log_error(f"Gemini Action Proposal Error: {e}")
            return []
