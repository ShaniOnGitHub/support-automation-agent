"""Quick diagnostic: tests which Gemini models are available with your API key."""
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

print(f"Testing with key: {API_KEY[:15]}...")

models_to_test = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.0-pro",
]
for model_name in models_to_test:
    try:
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content("Say hello in one word.")
        print(f"  ✅ {model_name}: {resp.text.strip()}")
    except Exception as e:
        print(f"  ❌ {model_name}: {e}")

print("\nAvailable models from API:")
try:
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(f"  • {m.name}")
except Exception as e:
    print(f"  Error listing models: {e}")
