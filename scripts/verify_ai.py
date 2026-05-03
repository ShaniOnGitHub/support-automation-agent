import os
import sys
import json
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai_service import (
    classify_ticket_with_gemini, 
    generate_suggested_reply, 
    propose_actions_for_ticket
)
from app.core.config import settings

def run_verify():
    load_dotenv()
    print(f"🚀 Verifying AI Provider: {settings.AI_PROVIDER}")
    
    subject = "Laptop not starting"
    body = "Hi, my laptop won't turn on since this morning. I ordered it last week, order #555. Please help."
    
    # 1. Triage
    print("\n1️⃣  Testing Triage...")
    try:
        triage = classify_ticket_with_gemini(subject, body)
        if triage:
            print(f"✅ Success: {triage}")
        else:
            print("❌ Failed: No triage result")
    except Exception as e:
        print(f"❌ Error in Triage: {e}")

    # 2. Suggested Reply
    print("\n2️⃣  Testing Suggested Reply...")
    try:
        reply = generate_suggested_reply(subject, body, context="Warranty: 1 year. Refund policy: 30 days.")
        if reply:
            print(f"✅ Success: \"{reply[:100]}...\"")
        else:
            print("❌ Failed: No reply generated")
    except Exception as e:
        print(f"❌ Error in Suggested Reply: {e}")

    # 3. Tool Proposals
    print("\n3️⃣  Testing Tool Proposals...")
    try:
        actions = propose_actions_for_ticket(subject, body)
        if actions:
            print(f"✅ Success: {[a.tool_name for a in actions]}")
        else:
            print("❌ Failed: No tools proposed")
    except Exception as e:
        print(f"❌ Error in Tool Proposals: {e}")

if __name__ == "__main__":
    run_verify()
