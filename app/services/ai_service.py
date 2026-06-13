from google import genai
from google.genai import types
import datetime
import time
import json
import httpx
import re
import os
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

def _call_groq_api(prompt: str, json_mode: bool = False) -> str:
    """
    Call Groq Cloud's chat completions API.
    Model: llama-3.3-70b-versatile
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a helpful customer support AI. If formatting JSON, do NOT use markdown code blocks."},
            {"role": "user", "content": prompt}
        ]
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    def request():
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].replace("```json", "").replace("```", "")

    return _call_with_retry(request)

def _is_api_key_dummy() -> bool:
    if os.environ.get("TESTING") == "1":
        return False
    if settings.AI_PROVIDER == "groq":
        key = settings.GROQ_API_KEY
    else:
        key = settings.GEMINI_API_KEY
    if not key:
        return False
    key_lower = key.lower()
    return "your" in key_lower or "dummy" in key_lower or "mock" in key_lower

def _mock_triage_fallback(subject: str, body: str) -> TriageResult:
    subject_lower = subject.lower()
    body_lower = body.lower()
    
    if "refund" in subject_lower or "refund" in body_lower or "double charge" in subject_lower or "double charge" in body_lower:
        return TriageResult(
            priority="high",
            sentiment="frustrated",
            summary="Customer is requesting a refund for order"
        )
    elif "won't turn on" in subject_lower or "won't turn on" in body_lower or "broken" in subject_lower or "broken" in body_lower:
        return TriageResult(
            priority="high",
            sentiment="frustrated",
            summary="Hardware/device won't start or is broken"
        )
    else:
        return TriageResult(
            priority="medium",
            sentiment="neutral",
            summary="Customer inquiry"
        )

def _mock_suggested_reply_fallback(subject: str, description: str, context: str = "") -> str:
    subject_lower = subject.lower()
    description_lower = description.lower()
    
    grounding_info = ""
    if context:
        grounding_info = f"\n\nBased on our policy context: {context}"
        
    if "refund" in subject_lower or "refund" in description_lower:
        return (
            "Hi there,\n\n"
            "I'm sorry to hear that you need a refund. Under our return and refund policy, "
            "refunds are allowed within 14 days of purchase. "
            "Please let us know your order details so we can process this for you right away."
            f"{grounding_info}"
        )
    elif "won't turn on" in subject_lower or "won't turn on" in description_lower:
        return (
            "Hi there,\n\n"
            "I'm sorry to hear your device won't turn on. "
            "Please try holding the power button for 10 seconds to perform a hard reset. "
            "If that doesn't help, let us know and we'll check your warranty status."
            f"{grounding_info}"
        )
    else:
        return (
            "Hi there,\n\n"
            "Thank you for contacting customer support. We have received your request "
            "and are looking into it. We will get back to you shortly."
            f"{grounding_info}"
        )

def _mock_propose_actions_fallback(subject: str, body: str) -> List[ProposedAction]:
    actions = []
    text_to_search = (subject + " " + body).lower()
    
    order_id = "555"
    match = re.search(r"order\s*#?\s*(\d+)", text_to_search)
    if match:
        order_id = match.group(1)
        actions.append(ProposedAction(tool_name="check_order_status", parameters={"order_id": order_id}))
        actions.append(ProposedAction(tool_name="check_refund_status", parameters={"order_id": order_id}))
    elif "refund" in text_to_search:
        actions.append(ProposedAction(tool_name="check_refund_status", parameters={"order_id": "unknown"}))
        
    if "fix" in text_to_search or "how to" in text_to_search or "won't" in text_to_search or "laptop" in text_to_search:
        actions.append(ProposedAction(tool_name="search_web", parameters={"query": "laptop won't start troubleshooting guide"}))
        
    return actions

def classify_ticket_with_gemini(subject: str, body: str) -> TriageResult | None:
    """
    Provider-agnostic classification.
    """
    if _is_api_key_dummy():
        return _mock_triage_fallback(subject, body)

    if settings.AI_PROVIDER in ("xai", "exa", "groq"):
        try:
            prompt = (
                f"Analyze this support ticket and provide triage data in JSON format.\n"
                f"Subject: {subject}\n"
                f"Body: {body}\n\n"
                "Return a JSON object with: priority (low/medium/high/urgent), sentiment, summary."
            )
            if settings.AI_PROVIDER == "exa":
                content = _call_exa_chat_api(prompt)
            elif settings.AI_PROVIDER == "groq":
                content = _call_groq_api(prompt, json_mode=True)
            else:
                content = _call_xai_responses_api(prompt)
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
        if not client:
            if _is_api_key_dummy():
                return _mock_triage_fallback(subject, body)
            return None
        try:
            response = _call_with_retry(lambda: client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"Analyze this ticket: {subject} - {body}",
                config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=TriageResult)
            ))
            return response.parsed if response and response.parsed else None
        except Exception as e:
            _log_error(f"Gemini Triage Error: {e}")
            if "key" in str(e).lower() or "400" in str(e) or _is_api_key_dummy():
                return _mock_triage_fallback(subject, body)
            return None

def generate_suggested_reply(subject: str, description: str, context: str = "") -> str | None:
    """
    Generate a suggested reply.
    """
    if _is_api_key_dummy():
        return _mock_suggested_reply_fallback(subject, description, context)

    if settings.AI_PROVIDER in ("xai", "exa", "groq"):
        try:
            prompt = f"Support Context: {context}\n\nDraft a polite reply to: {subject} - {description}"
            if settings.AI_PROVIDER == "exa":
                return _call_exa_chat_api(prompt)
            elif settings.AI_PROVIDER == "groq":
                return _call_groq_api(prompt, json_mode=False)
            else:
                return _call_xai_responses_api(prompt)
        except Exception as e:
            _log_error(f"{settings.AI_PROVIDER.upper()} Suggestion Error: {e}")
            return f"Hello, I am looking into your issue regarding '{subject}' now."
    else:
        client = _get_gemini_client()
        if not client:
            if _is_api_key_dummy():
                return _mock_suggested_reply_fallback(subject, description, context)
            return None
        try:
            prompt = f"Context: {context}\nReply to: {subject} - {description}"
            response = _call_with_retry(lambda: client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            ))
            return response.text.strip() if response and response.text else None
        except Exception as e:
            _log_error(f"Gemini Suggestion Error: {e}")
            if "key" in str(e).lower() or "400" in str(e) or _is_api_key_dummy():
                return _mock_suggested_reply_fallback(subject, description, context)
            return None

def generate_embeddings(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float] | None:
    if _is_api_key_dummy() or settings.AI_PROVIDER == "groq":
        return [0.1] * 3072
    client = _get_gemini_client()
    if not client:
        return [0.1] * 3072
    try:
        res = client.models.embed_content(model="text-embedding-004", contents=text)
        return res.embeddings[0].values if res.embeddings else None
    except Exception as e:
        _log_error(f"Gemini Embeddings Error: {e}")
        if "key" in str(e).lower() or "400" in str(e) or _is_api_key_dummy():
            return [0.1] * 3072
        return None

def propose_actions_for_ticket(subject: str, body: str) -> List[ProposedAction]:
    """
    Propose tools using xAI or Gemini.
    """
    if _is_api_key_dummy():
        return _mock_propose_actions_fallback(subject, body)

    if settings.AI_PROVIDER in ("xai", "exa", "groq"):
        try:
            prompt = (
                f"Propose diagnostic tools for: {subject} {body}\n"
                "Available tools: check_order_status(order_id), check_refund_status(order_id), search_web(query).\n\n"
                "Return a JSON object with 'actions' list."
            )
            if settings.AI_PROVIDER == "exa":
                content = _call_exa_chat_api(prompt)
            elif settings.AI_PROVIDER == "groq":
                content = _call_groq_api(prompt, json_mode=True)
            else:
                content = _call_xai_responses_api(prompt)
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
        if not client:
            if _is_api_key_dummy():
                return _mock_propose_actions_fallback(subject, body)
            return []
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
            if "key" in str(e).lower() or "400" in str(e) or _is_api_key_dummy():
                return _mock_propose_actions_fallback(subject, body)
            return []
