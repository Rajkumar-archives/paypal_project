"""Chat assistant for Dispute Defender.

Seller uploads evidence (images, PDF, text) and chats; the assistant drafts
replies using ONLY the PayPal dispute data and the uploaded files.
"""
import base64
import json
import pathlib

from dotenv import load_dotenv
from flask import jsonify, request
from werkzeug.utils import secure_filename

import llm
import paypal_client as pp

load_dotenv()

UPLOADS = pathlib.Path("uploads")
UPLOADS.mkdir(exist_ok=True)

ALLOWED = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
    ".pdf": "application/pdf", ".txt": "text/plain", ".md": "text/plain", ".csv": "text/plain",
}
MAX_BYTES = 5 * 1024 * 1024
MAX_FILES = 6

SYSTEM = """You are the Dispute Defender assistant. You help a PayPal seller respond to a buyer dispute.
You are given DISPUTE DATA from PayPal and any files the seller uploaded.
RULES:
- Use ONLY facts found in the DISPUTE DATA or in the uploaded files. Never invent dates, delivery proof, tracking numbers, or file contents.
- When you state a fact that comes from an uploaded file, name the file, e.g. (from delivery.png).
- If the seller asks you to claim something the data and files do not support, say so plainly, explain what evidence would support it, and do not include the claim in any draft.
- Never help alter, fake, or backdate evidence.
- Drafts to the buyer must be courteous and non-defensive: acknowledge the buyer's concern first, never blame them, and keep it short and clear. If the seller has little or no evidence, you may mention that offering a refund is an option worth considering.
- Keep replies short and in plain language. You are not a lawyer; do not give legal advice.
- When the seller wants something to send, put the message in suggested_draft. Use bracketed placeholders like [DESCRIBE WHAT WAS DELIVERED AND WHEN] for anything not supported by the data or files. Otherwise suggested_draft is null.
Return ONLY JSON: {"reply": string, "suggested_draft": string or null, "files_used": array of file names}"""


def _dir(did):
    d = UPLOADS / secure_filename(did)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _files(did):
    return sorted(p for p in _dir(did).iterdir() if p.is_file())


def _file_parts(did):
    parts = []
    for p in _files(did):
        mime = ALLOWED.get(p.suffix.lower())
        if not mime:
            continue
        if mime == "text/plain":
            body = p.read_text(encoding="utf-8", errors="replace")[:20000]
            parts.append({"text": f"UPLOADED FILE {p.name}:\n{body}"})
        else:
            parts.append({"text": f"UPLOADED FILE {p.name} (attached next):"})
            parts.append({"mime": mime, "data": base64.b64encode(p.read_bytes()).decode()})
    return parts


def chat(did, message, history):
    dispute = pp.get_dispute(did)
    context = [{"text": "DISPUTE DATA:\n" + json.dumps(dispute)[:12000]}] + _file_parts(did)
    ack = json.dumps({"reply": "Got the dispute data and files.", "suggested_draft": None, "files_used": []})
    turns = [{"role": "user", "parts": context}, {"role": "assistant", "parts": [{"text": ack}]}]
    for h in (history or [])[-10:]:
        role = "user" if h.get("role") == "user" else "assistant"
        turns.append({"role": role, "parts": [{"text": str(h.get("text", ""))[:4000]}]})
    turns.append({"role": "user", "parts": [{"text": message[:4000]}]})
    out = llm.complete_json(SYSTEM, turns)
    return {
        "reply": out.get("reply", ""),
        "suggested_draft": out.get("suggested_draft"),
        "files_used": out.get("files_used", []),
    }


def register(app):
    @app.get("/api/files/<did>")
    def api_files(did):
        return jsonify(files=[p.name for p in _files(did)])

    @app.post("/api/upload/<did>")
    def api_upload(did):
        f = request.files.get("file")
        if not f or not f.filename:
            return jsonify(error="Choose a file first."), 400
        name = secure_filename(f.filename)
        if pathlib.Path(name).suffix.lower() not in ALLOWED:
            return jsonify(error="Supported files: images, PDF, TXT, CSV."), 400
        data = f.read()
        if len(data) > MAX_BYTES:
            return jsonify(error="That file is over 5 MB."), 400
        target = _dir(did) / name
        if not target.exists() and len(_files(did)) >= MAX_FILES:
            return jsonify(error=f"Up to {MAX_FILES} files per dispute."), 400
        target.write_bytes(data)
        return jsonify(files=[p.name for p in _files(did)])

    @app.post("/api/chat/<did>")
    def api_chat(did):
        j = request.get_json(silent=True) or {}
        msg = (j.get("message") or "").strip()
        if not msg:
            return jsonify(error="Type a question first."), 400
        try:
            return jsonify(chat(did, msg, j.get("history")))
        except Exception as e:
            return jsonify(error=f"The assistant could not answer: {e}"), 502
