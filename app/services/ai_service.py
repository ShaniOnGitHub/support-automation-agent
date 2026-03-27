from google import genai
from google.genai import types
import datetime
import time
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

def _get_client():
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_key_here":
        return None
    return genai.Client(api_key=settings.GEMINI_API_KEY)

def _call_with_retry(fn, retries=3, delay=5):
    last_err = None
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            last_err = e
            err_str = str(e)
            if "quota" in err_str.lower() or "429" in err_str or "rate" in err_str.lower():
                _log_error(f"Rate limit hit (attempt {attempt+1}): {e}")
                time.sleep(delay)
            else:
                _log_error(f"AI Call Error (attempt {attempt+1}): {e}")
                # Don't sleep for non-rate errors
    return None

def classify_ticket_with_gemini(subject: str, body: str) -> TriageResult | None:
    client = _get_client()
    if not client: return None
    try:
        # Simplify model name - SDK handles the /models path
        response = _call_with_retry(lambda: client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Analyze this ticket and return JSON: {subject} - {body}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TriageResult,
                temperature=0.1
            )
        ))
        return response.parsed if response and response.parsed else None
    except Exception as e:
        _log_error(f"AI Triage: {e}")
        return None

def generate_suggested_reply(subject: str, description: str, context: str = "") -> str | None:
    client = _get_client()
    if not client: return None
    try:
        prompt = f"Support Context: {context}\nReply to: {subject} - {description}"
        response = _call_with_retry(lambda: client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3)
        ))
        return response.text.strip() if response and response.text else None
    except Exception as e:
        _log_error(f"AI Suggestion: {e}")
        return None

def generate_embeddings(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float] | None:
    client = _get_client()
    if not client: return None
    try:
        res = client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(task_type=task_type)
        )
        return res.embeddings[0].values if res.embeddings else None
    except Exception as e:
        # Try fallback model
        try:
            res = client.models.embed_content(model="gemini-embedding-001", contents=text)
            return res.embeddings[0].values
        except:
            return None

def propose_actions_for_ticket(subject: str, body: str) -> List[ProposedAction]:
    client = _get_client()
    if not client: return []
    try:
        prompt = f"List tools (check_order_status {{'order_id': '...'}}) in JSON list for: {subject} {body}"
        response = _call_with_retry(lambda: client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        ))
        if response and response.text:
            import json
            text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)
            actions_data = data.get("actions", data if isinstance(data, list) else [])
            return [ProposedAction(**a) for a in actions_data]
        return []
    except Exception as e:
        _log_error(f"AI Propose: {e}")
        return []
