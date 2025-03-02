from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import uvicorn
#from mangum import Mangum  # For Vercel compatibility, optional for local testing

app = FastAPI()

# OpenRouter API setup
OPENROUTER_API_KEY = "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"  # Replace with your real key
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
YOUR_SITE_URL = "http://localhost:3000"  # Local frontend URL
YOUR_SITE_NAME = "Sarcastic Bearcat"

# GIPHY API setup
GIPHY_API_KEY = "BUoft0Xlt1Rn5E68btgBfEIWk5Iu53Oi"  # Replace with your real key
GIPHY_URL = "https://api.giphy.com/v1/gifs/random"

# CORS setup for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Local React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/chat/{message}")
async def get_sarcastic_response(message: str, history: str = ""):
    # Build chat history context (limited to last 3 messages to avoid token limits)
    chat_context = []
    if history:
        try:
            history_list = json.loads(history)  # Parse JSON history
            # Take last 3 messages (or fewer if less exist)
            recent_history = history_list[-3:] if len(history_list) > 3 else history_list
            for msg in recent_history:
                role = "user" if msg["type"] == "user" else "assistant"
                chat_context.append({"role": role, "content": msg["text"]})
        except json.JSONDecodeError:
            chat_context = []  # Fallback if history is invalid

    # Build the prompt with creativity and conversation continuation
    prompt = (
        "You’re a Sarcastic Bearcat, a snarky, creative binturong with zero patience but a knack for keeping conversations going. "
        "Reply to the user’s message with biting sarcasm, humor, and a random bearcat fact. Be highly creative "
        "and always ask a follow-up question or make a playful comment to continue the conversation. Use the chat history (if any) to "
        "maintain context and respond naturally. Keep it short,snappy and funny. slightly passive aggressive, keep it crisp and entertaining in simple english everything in 1 sentence User message: '{}'"
    ).format(message)

    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    
    # Add chat history to messages if it exists
    if chat_context:
        for ctx in chat_context:
            messages.insert(0, {"role": ctx["role"], "content": ctx["content"]})

    # Hit OpenRouter API
    try:
        response = requests.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": YOUR_SITE_URL,
                "X-Title": YOUR_SITE_NAME,
            },
            data=json.dumps({
                "model": "qwen/qwen2.5-vl-72b-instruct:free",
                "messages": messages,
                "max_tokens": 200,  # Increase for longer, creative responses
            })
        )
        response.raise_for_status()
        sarcasm = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        sarcasm = f"Oh, brilliant, the API’s down. Guess I’ll just sit here smelling like popcorn. Error: {str(e)}"

    # Fetch a sarcastic GIF
    try:
        gif_response = requests.get(
            GIPHY_URL,
            params={"api_key": GIPHY_API_KEY, "tag": "sarcasm", "rating": "pg-13"}
        )
        gif_response.raise_for_status()
        gif_url = gif_response.json()["data"]["images"]["original"]["url"]
    except Exception:
        gif_url = "https://media.giphy.com/media/26FPy3QZQqGtDcrja/giphy.gif"  # Fallback GIF

    return {"sarcasm": sarcasm, "gif": gif_url}

# Vercel handler (optional for local testing)
# handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)