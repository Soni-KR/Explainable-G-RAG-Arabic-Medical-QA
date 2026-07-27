import os
from dotenv import load_dotenv
import requests

load_dotenv()

key = os.getenv("GROQ_API_KEY")

r = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {key}"},
    json={
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "Reply in JSON."}],
        "response_format": {"type": "json_object"},
    },
)

print(r.status_code)
print(r.text)