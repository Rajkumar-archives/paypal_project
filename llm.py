"""The one place Dispute Defender talks to an AI provider.

Configure in .env (existing GEMINI_* names still work):
  AI_PROVIDER=gemini | openai     (openai = any OpenAI-compatible chat API)
  AI_MODEL=...                    (falls back to GEMINI_MODEL)
  AI_API_KEY=...                  (falls back to GEMINI_API_KEY)
  AI_BASE_URL=...                 (openai provider only, default https://api.openai.com/v1)

Swapping providers means changing .env, not the app. The company that adopts
this brings its own provider, key and data terms.

Turns look like: {"role": "user"|"assistant",
                  "parts": [{"text": "..."} | {"mime": "image/png", "data": "<base64>"}]}
"""
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()


def _cfg():
    provider = os.getenv("AI_PROVIDER", "gemini").lower()
    model = os.getenv("AI_MODEL") or os.getenv("GEMINI_MODEL")
    key = os.getenv("AI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not model or not key:
        raise RuntimeError("Set AI_MODEL and AI_API_KEY (or GEMINI_MODEL and GEMINI_API_KEY) in .env")
    return provider, model, key


def _gemini(system, turns, temperature, model, key):
    contents = []
    for t in turns:
        parts = []
        for p in t["parts"]:
            if "text" in p:
                parts.append({"text": p["text"]})
            else:
                parts.append({"inline_data": {"mime_type": p["mime"], "data": p["data"]}})
        contents.append({"role": "model" if t["role"] == "assistant" else "user", "parts": parts})
    body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {"responseMimeType": "application/json", "temperature": temperature},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    r = requests.post(url, headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                      json=body, timeout=90)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _openai(system, turns, temperature, model, key):
    messages = [{"role": "system", "content": system}]
    for t in turns:
        if t["role"] == "assistant":
            messages.append({"role": "assistant", "content": " ".join(p.get("text", "") for p in t["parts"])})
            continue
        content = []
        for p in t["parts"]:
            if "text" in p:
                content.append({"type": "text", "text": p["text"]})
            elif p["mime"].startswith("image/"):
                content.append({"type": "image_url",
                                "image_url": {"url": f"data:{p['mime']};base64,{p['data']}"}})
            else:
                content.append({"type": "text", "text": "[A file of this type could not be sent to this provider.]"})
        messages.append({"role": "user", "content": content})
    base = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    r = requests.post(f"{base}/chat/completions",
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                      json={"model": model, "messages": messages, "temperature": temperature,
                            "response_format": {"type": "json_object"}},
                      timeout=90)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def complete_json(system, turns, temperature=0.2):
    """Send the conversation, return the model's JSON answer as a dict."""
    provider, model, key = _cfg()
    if provider == "gemini":
        text = _gemini(system, turns, temperature, model, key)
    elif provider == "openai":
        text = _openai(system, turns, temperature, model, key)
    else:
        raise RuntimeError(f"Unknown AI_PROVIDER '{provider}'. Use gemini or openai.")
    return json.loads(text)
