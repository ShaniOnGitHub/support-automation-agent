import pytest
from unittest.mock import patch
from app.services.ai_service import (
    classify_ticket_with_gemini,
    generate_suggested_reply,
    propose_actions_for_ticket,
    TriageResult,
    ProposedAction
)
from app.core.config import settings

def test_groq_triage_success():
    with patch("app.services.ai_service._call_groq_api") as mock_groq:
        old_provider = settings.AI_PROVIDER
        old_key = settings.GROQ_API_KEY
        try:
            settings.AI_PROVIDER = "groq"
            settings.GROQ_API_KEY = "gsk_test_key"
            
            mock_groq.return_value = '{"priority": "high", "sentiment": "neutral", "summary": "triage test"}'
            
            res = classify_ticket_with_gemini("subject", "body")
            assert res is not None
            assert res.priority == "high"
            assert res.sentiment == "neutral"
            assert res.summary == "triage test"
            mock_groq.assert_called_once()
        finally:
            settings.AI_PROVIDER = old_provider
            settings.GROQ_API_KEY = old_key

def test_groq_suggested_reply_success():
    with patch("app.services.ai_service._call_groq_api") as mock_groq:
        old_provider = settings.AI_PROVIDER
        old_key = settings.GROQ_API_KEY
        try:
            settings.AI_PROVIDER = "groq"
            settings.GROQ_API_KEY = "gsk_test_key"
            
            mock_groq.return_value = "This is a reply draft"
            
            res = generate_suggested_reply("subject", "body", "context")
            assert res == "This is a reply draft"
            mock_groq.assert_called_once()
        finally:
            settings.AI_PROVIDER = old_provider
            settings.GROQ_API_KEY = old_key

def test_groq_propose_actions_success():
    with patch("app.services.ai_service._call_groq_api") as mock_groq:
        old_provider = settings.AI_PROVIDER
        old_key = settings.GROQ_API_KEY
        try:
            settings.AI_PROVIDER = "groq"
            settings.GROQ_API_KEY = "gsk_test_key"
            
            mock_groq.return_value = '{"actions": [{"tool_name": "check_order_status", "parameters": {"order_id": "123"}}]}'
            
            res = propose_actions_for_ticket("subject", "body")
            assert len(res) == 1
            assert res[0].tool_name == "check_order_status"
            assert res[0].parameters == {"order_id": "123"}
            mock_groq.assert_called_once()
        finally:
            settings.AI_PROVIDER = old_provider
            settings.GROQ_API_KEY = old_key
