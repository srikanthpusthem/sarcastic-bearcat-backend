from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables (works locally and on Render)
load_dotenv()

app = FastAPI()

# OpenRouter API setup
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
YOUR_SITE_URL = os.getenv("SITE_URL", "https://sarcastic-bearcat.vercel.app")  # Default to Vercel frontend
YOUR_SITE_NAME = "Sarcastic Bearcat"

# GIPHY API setup
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
GIPHY_URL = "https://api.giphy.com/v1/gifs/random"

# CORS setup (allow Vercel frontend or local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",  # Local React dev
        "https://sarcastic-bearcat.vercel.app"  # Deployed frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/chat/{message}")
async def get_sarcastic_response(message: str, history: str = ""):
    chat_context = []
    if history:
        try:
            history_list = json.loads(history)
            recent_history = history_list[-3:] if len(history_list) > 3 else history_list
            chat_context = [{"role": "user" if msg["type"] == "user" else "assistant", 
                            "content": msg["text"]} for msg in recent_history]
        except json.JSONDecodeError:
            chat_context = []

    prompt = (
        "You’re a Sarcastic Bearcat, a snarky, creative binturong with zero patience but a knack for keeping conversations going. "
        "Reply to the user’s message with biting sarcasm, humor, and a random bearcat fact. Be highly creative, "
        "always ask a follow-up question or make a playful comment to continue the conversation. Use the chat history (if any) to "
        "maintain context and respond naturally. Keep it short, snappy, funny, slightly passive-aggressive, crisp, and entertaining in simple English, all in 1 sentence. "
        f"User message: '{message}'"
    )

    messages = chat_context + [{"role": "user", "content": prompt}]

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": YOUR_SITE_URL,
                "X-Title": YOUR_SITE_NAME,
            },
            json={
                "model": "qwen/qwen2.5-vl-72b-instruct:free",
                "messages": messages,
                "max_tokens": 200,
            }
        )
        response.raise_for_status()
        sarcasm = response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        sarcasm = f"Wow, the API crashed harder than my patience — enjoy the popcorn smell. Error: {str(e)}"

    try:
        gif_response = requests.get(
            GIPHY_URL,
            params={"api_key": GIPHY_API_KEY, "tag": "sarcasm", "rating": "pg-13"}
        )
        gif_response.raise_for_status()
        gif_url = gif_response.json()["data"]["images"]["original"]["url"]
    except requests.RequestException:
        gif_url = "https://media.giphy.com/media/26FPy3QZQqGtDcrja/giphy.gif"

    return {"sarcasm": sarcasm, "gif": gif_url}

if __name__ == "__main__":
    # For Render, use environment PORT or default to 8000 locally
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)