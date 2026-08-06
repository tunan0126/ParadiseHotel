import os
import litellm

# 1. Test Groq
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "")
try:
    print("Testing Groq...")
    response = litellm.completion(
        model="groq/llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "Hello"}],
        api_key=os.environ["GROQ_API_KEY"]
    )
    print("Groq OK!")
except Exception as e:
    print("Groq Error:", e)

# 2. Test Gemini
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
try:
    print("Testing Gemini...")
    response = litellm.completion(
        model="gemini/gemini-2.0-flash",
        messages=[{"role": "user", "content": "Hello"}],
        api_key=os.environ["GEMINI_API_KEY"]
    )
    print("Gemini OK!")
except Exception as e:
    print("Gemini Error:", e)
