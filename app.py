"""Dispute Defender - helps PayPal sellers respond to buyer disputes.

Run:  py app.py   then open http://localhost:5000
Needs paypal_client.py and ai_agent.py in the same folder.
"""
import json
import pathlib
import uuid
import re
from datetime import datetime

import requests
from flask import Flask, jsonify, render_template, request
from jinja2 import DictLoader

import paypal_client as pp
from ai_agent import build_evidence_plan
import assistant

app = Flask(__name__)

CACHE = pathlib.Path("plans")
CACHE.mkdir(exist_ok=True)
PLACEHOLDER = re.compile(r"\[[^\]]+\]")


# ---------- helpers ----------
@app.template_filter("nice_date")
def nice_date(v):
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00")).strftime("%b %d, %Y")
    except Exception:
        return v or "none"


@app.template_filter("label")
def label(v):
    return (v or "").replace("_", " ").capitalize()


def money(d):
    a = (d or {}).get("dispute_amount") or {}
    return f"{a.get('value', '?')} {a.get('currency_code', '')}".strip()


# ---------- pages ----------
@app.get("/")
def index():
    try:
        items = pp.list_disputes()
        error = None
    except Exception as e:  # show a readable message instead of a stack trace
        items, error = [], f"Could not load disputes from PayPal: {e}"
    return render_template("index.html", items=items, error=error, money=money)


@app.get("/dispute/<did>")
def dispute(did):
    try:
        d = pp.get_dispute(did)
    except Exception as e:
        return render_template("index.html", items=[], error=f"Could not load {did}: {e}", money=money), 502
    types = ((d.get("allowed_response_options") or {}).get("accept_claim") or {}).get("accept_claim_types") or []
    return render_template("dispute.html", d=d, amount=money(d), messages=d.get("messages", []),
                           can_refund="REFUND" in types)


# ---------- API ----------
@app.post("/api/plan/<did>")
def api_plan(did):
    f = CACHE / f"{did}.json"
    if f.exists() and not request.args.get("refresh"):
        return jsonify(json.loads(f.read_text(encoding="utf-8")))
    try:
        plan = build_evidence_plan(pp.get_dispute(did))
    except Exception as e:
        return jsonify(error=f"Could not build the plan: {e}"), 502
    f.write_text(json.dumps(plan), encoding="utf-8")
    return jsonify(plan)


@app.post("/api/send/<did>")
def api_send(did):
    msg = ((request.get_json(silent=True) or {}).get("message") or "").strip()
    if not msg:
        return jsonify(error="The message is empty."), 400
    if PLACEHOLDER.search(msg):
        return jsonify(error="Replace every [bracketed] placeholder with real details first."), 400
    try:
        pp.send_message(did, msg)
    except requests.HTTPError as e:
        return jsonify(error=f"PayPal rejected the message: {e.response.text[:300]}"), 502
    except Exception as e:
        return jsonify(error=f"Could not send: {e}"), 502
    return jsonify(ok=True)


# ---------- templates (inline so the app is one file) ----------
BASE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{% block title %}Dispute Defender{% endblock %}</title>
<style>
:root{--bg:#f2f4f7;--card:#fff;--ink:#17283c;--muted:#5b6b7d;--line:#d5dce5;--blue:#0a4fd6;
--amber:#8a5200;--amberbg:#fff4dc;--red:#a4262c;--redbg:#fde8e8;--green:#17663f;--greenbg:#e3f4ea}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 "Segoe UI",system-ui,sans-serif}
.top{display:flex;align-items:center;justify-content:space-between;padding:14px 24px;background:var(--card);border-bottom:1px solid var(--line)}
.brand{font-weight:700;font-size:19px;color:var(--ink);text-decoration:none}
.env{font-size:13px;color:var(--amber);background:var(--amberbg);padding:3px 10px;border-radius:999px}
main{max-width:1080px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:18px;margin:0 0 10px}
.sub{color:var(--muted);margin:0 0 22px}
a{color:var(--blue)}a:focus-visible,button:focus-visible,textarea:focus-visible{outline:3px solid var(--blue);outline-offset:2px}
.row{display:grid;grid-template-columns:2fr 1fr 1.3fr 1fr;gap:12px;align-items:center;padding:14px 16px;background:var(--card);border:1px solid var(--line);border-radius:8px;margin-bottom:8px;text-decoration:none;color:var(--ink)}
.row:hover{border-color:var(--blue)}
.row .k{color:var(--muted);font-size:14px}
.chip{display:inline-block;font-size:13px;padding:2px 9px;border-radius:999px;background:var(--amberbg);color:var(--amber)}
.chip.ok{background:var(--greenbg);color:var(--green)}.chip.bad{background:var(--redbg);color:var(--red)}
.cols{display:grid;grid-template-columns:minmax(260px,1fr) 1.7fr;gap:22px;align-items:start}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:18px 20px;margin-bottom:16px}
dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:6px 14px}dt{color:var(--muted)}dd{margin:0;word-break:break-word}
button{font:inherit;font-weight:600;border:0;border-radius:8px;padding:10px 18px;cursor:pointer;background:var(--blue);color:#fff}
button:disabled{background:#b8c2d1;cursor:not-allowed}
button.ghost{background:transparent;color:var(--blue);border:1px solid var(--blue)}
ul.check{list-style:none;padding:0;margin:0}
ul.check li{display:flex;gap:10px;align-items:flex-start;padding:7px 0;border-bottom:1px solid var(--line)}
ul.check li:last-child{border-bottom:0}
.callout{padding:12px 14px;border-radius:8px;background:var(--amberbg);color:var(--amber)}
.callout.err{background:var(--redbg);color:var(--red)}.callout.good{background:var(--greenbg);color:var(--green)}
textarea{width:100%;min-height:150px;font:inherit;padding:12px;border:1px solid var(--line);border-radius:8px;resize:vertical}
.msg{padding:10px 0;border-bottom:1px solid var(--line)}.msg:last-child{border:0}
.muted{color:var(--muted)}.actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:10px}
@media(max-width:800px){.cols{grid-template-columns:1fr}.row{grid-template-columns:1fr 1fr}}
</style></head><body>
<header class="top"><a class="brand" href="/">Dispute Defender</a><span class="env">PayPal sandbox</span></header>
<main>{% block body %}{% endblock %}</main></body></html>"""

INDEX = """{% extends "base.html" %}{% block body %}
<h1>Open disputes</h1>
<p class="sub">Pick a dispute to see what PayPal needs from you and what evidence you still have to gather.</p>
{% if error %}<div class="callout err">{{ error }}</div>{% endif %}
{% for x in items %}
<a class="row" href="/dispute/{{ x.dispute_id }}">
  <div><strong>{{ x.reason|label }}</strong><div class="k">{{ x.dispute_id }}</div></div>
  <div>{{ money(x) }}</div>
  <div><span class="chip">{{ x.status|label }}</span></div>
  <div class="k">Respond by {{ x.seller_response_due_date|nice_date }}</div>
</a>
{% else %}{% if not error %}<div class="card">No disputes yet. Open one from a sandbox buyer account in the PayPal Resolution Center, then refresh this page.</div>{% endif %}{% endfor %}
{% endblock %}"""

DISPUTE = """{% extends "base.html" %}{% block body %}
<p><a href="/">Back to disputes</a></p>
<h1>{{ d.reason|label }}</h1>
<p class="sub">{{ amount }} &middot; {{ d.dispute_id }}</p>
<div class="cols">
 <div>
  <div class="card"><h2>What PayPal shows</h2>
   <dl>
    <dt>Status</dt><dd><span class="chip">{{ d.status|label }}</span></dd>
    <dt>Stage</dt><dd>{{ d.dispute_life_cycle_stage|label }}</dd>
    <dt>Opened</dt><dd>{{ d.create_time|nice_date }}</dd>
    <dt>Respond by</dt><dd>{{ d.seller_response_due_date|nice_date }}</dd>
    <dt>Channel</dt><dd>{{ d.dispute_channel|label }}</dd>
   </dl></div>
  <div class="card"><h2>Messages so far</h2>
   {% for m in messages %}<div class="msg"><strong>{{ m.posted_by|label }}</strong> <span class="muted">{{ m.time_posted|nice_date }}</span><div>{{ m.content }}</div></div>
   {% else %}<p class="muted">No messages yet.</p>{% endfor %}</div>
 </div>
 <div>
  <div class="card" id="plan-card"><h2>Your response plan</h2>
   <p class="muted">The assistant reads this dispute and tells you what PayPal wants and what evidence to gather. It never invents evidence.</p>
   <button id="build">Build response plan</button>
   <div id="plan-status" class="muted" role="status"></div>
  </div>
  <div class="card" id="assist"><h2>Ask the assistant</h2>
   <p class="muted">Upload what you have (screenshots, PDFs, text files), then ask what to send. It only uses facts from the dispute and your files.</p>
   <div class="actions"><input type="file" id="file" aria-label="Upload evidence file"><button class="ghost" id="upload">Upload</button></div>
   <div id="assist-status" class="muted" role="status"></div>
   <ul class="check" id="files"></ul>
   <div id="log" aria-live="polite"></div>
   <textarea id="ask" style="min-height:70px;margin-top:10px" aria-label="Ask the assistant" placeholder="For example: Based on my files, what should I tell the buyer?"></textarea>
   <div class="actions"><button id="askbtn">Ask</button></div>
  </div>
  <div id="plan" hidden>
   <div class="card"><h2>What this dispute means</h2><p id="explain"></p><p class="muted" id="dtype"></p></div>
   <div class="card"><h2>Evidence to gather</h2><ul class="check" id="checklist"></ul></div>
   <div class="callout" id="risk" style="margin-bottom:16px"></div>
  </div>
  <div class="card" id="reply-card"><h2>Reply to the buyer</h2>
    <p class="muted">Fill in every [bracketed] part with real details. Sending unlocks when none are left.</p>
    <textarea id="draft" aria-label="Reply to the buyer"></textarea>
    <div class="actions"><button id="send" disabled>Send reply to buyer</button><span id="gate" class="muted"></span></div>
    <div id="result" role="status" style="margin-top:10px"></div>
  </div>
  {% if can_refund %}<div class="card" id="refund-card"><h2>Rather make it right?</h2>
   <p class="muted">If you can't back the sale up with evidence, refunding the buyer in full resolves this quickly and keeps the customer. PayPal refunds them from your account and closes the dispute in their favor.</p>
   <button class="ghost" id="refund">Refund buyer in full</button>
   <div id="refund-result" role="status" style="margin-top:10px"></div>
  </div>{% endif %}
 </div>
</div>
<script>
const id = {{ d.dispute_id|tojson }};
const $ = s => document.querySelector(s);
const PH = /\\[[^\\]]+\\]/g;
function gate(){
  const left = ($('#draft').value.match(PH) || []).length;
  $('#send').disabled = left > 0 || !$('#draft').value.trim();
  $('#gate').textContent = left ? left + " placeholder" + (left>1?"s":"") + " left to fill in" : "";
}
function render(p){
  $('#explain').textContent = p.plain_explanation || "";
  const dl = Date.parse(p.deadline_note);
  $('#dtype').textContent = isNaN(dl) ? (p.deadline_note || "") : "Respond by " + new Date(dl).toLocaleDateString(undefined, {year:"numeric", month:"short", day:"numeric"});
  const miss = new Set(p.missing_evidence || []);
  const ul = $('#checklist'); ul.innerHTML = "";
  (p.evidence_checklist || []).forEach(t => {
    const li = document.createElement("li");
    const chip = document.createElement("span");
    chip.className = "chip " + (miss.has(t) ? "bad" : "ok");
    chip.textContent = miss.has(t) ? "Missing" : "Found";
    const txt = document.createElement("span"); txt.textContent = t;
    li.append(chip, txt); ul.append(li);
  });
  $('#risk').textContent = p.risk_note || "";
  $('#draft').value = p.draft_response || "";
  $('#plan').hidden = false; gate();
}
$('#build').onclick = async () => {
  $('#build').disabled = true; $('#plan-status').textContent = "Reading the dispute...";
  try {
    const r = await fetch("/api/plan/" + encodeURIComponent(id), {method:"POST"});
    const j = await r.json();
    if(!r.ok) throw new Error(j.error || "Request failed");
    render(j); $('#plan-status').textContent = "";
  } catch(e){ $('#plan-status').textContent = e.message; }
  $('#build').disabled = false;
};
$('#draft').addEventListener("input", gate);
$('#send').onclick = async () => {
  $('#send').disabled = true;
  const r = await fetch("/api/send/" + encodeURIComponent(id), {method:"POST",
    headers:{"Content-Type":"application/json"}, body: JSON.stringify({message: $('#draft').value})});
  const j = await r.json();
  const box = $('#result'); box.className = "callout " + (r.ok ? "good" : "err");
  box.textContent = r.ok ? "Reply sent to the buyer." : (j.error || "Could not send.");
  if(!r.ok) gate();
};

const hist = [];
async function loadFiles(){
  const r = await fetch("/api/files/" + encodeURIComponent(id));
  const j = await r.json();
  const ul = $('#files'); ul.innerHTML = "";
  (j.files || []).forEach(n => { const li = document.createElement("li"); li.textContent = n; ul.append(li); });
}
$('#upload').onclick = async () => {
  const f = $('#file').files[0];
  if(!f){ $('#assist-status').textContent = "Choose a file first."; return; }
  const fd = new FormData(); fd.append("file", f);
  const r = await fetch("/api/upload/" + encodeURIComponent(id), {method:"POST", body: fd});
  const j = await r.json();
  $('#assist-status').textContent = r.ok ? "Uploaded " + f.name : (j.error || "Upload failed.");
  if(r.ok){ $('#file').value = ""; loadFiles(); }
};
function bubble(who, text, draft){
  const d = document.createElement("div"); d.className = "msg";
  const b = document.createElement("strong"); b.textContent = who;
  const p = document.createElement("div"); p.textContent = text;
  d.append(b, p);
  if(draft){
    const u = document.createElement("button"); u.className = "ghost"; u.textContent = "Use as my reply"; u.style.marginTop = "8px";
    u.onclick = () => { $('#draft').value = draft; gate(); $('#reply-card').scrollIntoView({behavior:"smooth"}); };
    d.append(u);
  }
  $('#log').append(d);
}
$('#askbtn').onclick = async () => {
  const text = $('#ask').value.trim(); if(!text) return;
  bubble("You", text); $('#ask').value = ""; $('#askbtn').disabled = true;
  try{
    const r = await fetch("/api/chat/" + encodeURIComponent(id), {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({message:text, history:hist})});
    const j = await r.json();
    if(!r.ok) throw new Error(j.error || "Request failed");
    hist.push({role:"user", text: text}, {role:"assistant", text: j.reply});
    bubble("Assistant", j.reply, j.suggested_draft);
  }catch(e){ bubble("Assistant", e.message); }
  $('#askbtn').disabled = false;
};
loadFiles();
if($('#refund')) $('#refund').onclick = async () => {
  if(!confirm("Refund " + {{ amount|tojson }} + " to the buyer and close this dispute in their favor? This cannot be undone.")) return;
  $('#refund').disabled = true;
  const r = await fetch("/api/refund/" + encodeURIComponent(id), {method:"POST", headers:{"Content-Type":"application/json"}, body: "{}"});
  const j = await r.json();
  const box = $('#refund-result'); box.className = "callout " + (r.ok ? "good" : "err");
  box.textContent = r.ok ? "Buyer refunded in full and the dispute is closed." : (j.error || "Could not refund.");
  if(!r.ok) $('#refund').disabled = false;
};
</script>
{% endblock %}"""

app.jinja_loader = DictLoader({"base.html": BASE, "index.html": INDEX, "dispute.html": DISPUTE})

@app.post("/api/refund/<did>")
def api_refund(did):
    """Accept the buyer's claim with a full refund (PayPal refunds the buyer and closes the dispute)."""
    j = request.get_json(silent=True) or {}
    note = (j.get("note") or "").strip() or (
        "We're sorry this didn't go as expected. We're refunding you in full to make it right."
    )
    last = None
    for reason in ("REASON_NOT_SET", "NOT_ABLE_TO_WIN"):
        try:
            r = requests.post(
                f"{pp.BASE}/v1/customer/disputes/{did}/accept-claim",
                headers={**pp._h(), "PayPal-Request-Id": str(uuid.uuid4())},
                json={"note": note[:2000], "accept_claim_reason": reason, "accept_claim_type": "REFUND"},
                timeout=20,
            )
            r.raise_for_status()
            return jsonify(ok=True)
        except requests.HTTPError as e:
            last = e.response.text[:300]
            if e.response.status_code not in (400, 422):
                break
        except Exception as e:
            last = str(e)
            break
    return jsonify(error=f"PayPal rejected the refund: {last}"), 502


assistant.register(app)

if __name__ == "__main__":
    app.run(debug=True)
