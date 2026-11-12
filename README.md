# Dispute Defender

AI help for PayPal sellers who get a buyer dispute, built so the customer is treated fairly too.

**Live demo:** <PASTE YOUR URL HERE> (PayPal **sandbox** data only)

## The problem
Sellers and freelancers (especially cross-border) lose money to disputes because PayPal's decisions feel opaque: they don't know what PayPal wants, what evidence to gather, or how to reply before the deadline. Many replies are defensive or unsupported, which makes disputes slower and more painful for buyers as well.

## What it does
- **Dispute inbox:** pulls live disputes from the PayPal Disputes API (reason, amount, stage, response deadline, messages).
- **Response plan:** an AI reads the dispute and explains it in plain language, lists the evidence to gather, marks what is missing, and gives an honest risk note.
- **Evidence-aware assistant:** the seller uploads screenshots, PDFs or text files and chats. Drafts use only facts from the dispute data and the uploaded files, and name the file behind each fact. It refuses to claim anything the evidence doesn't support.
- **Gated reply:** drafts use `[placeholders]` for anything unsupported. The Send button (and the server) stay locked until every placeholder is replaced with real details, so nothing invented reaches the buyer.
- **Make it right:** one click refunds the buyer in full through PayPal's accept-claim call, which closes the dispute quickly and keeps the customer. The button only appears when PayPal lists the action as allowed for that dispute.
- **Buyer-friendly tone:** drafts acknowledge the buyer's concern first and never blame them.

## How PayPal is used
OAuth client credentials, then in the sandbox: `GET /v1/customer/disputes`, `GET /v1/customer/disputes/{id}`, `POST .../send-message`, `POST .../accept-claim`.

## How AI is used
All AI calls go through one file, `llm.py`. The demo runs on a free Gemini key with sandbox data only. A company adopting this brings its own provider, model and key via `.env` (`AI_PROVIDER=gemini` or `openai` for any OpenAI-compatible API). Gemini is the fully tested provider. Use a provider under your own data agreements for real dispute data.

## Run it locally
**New to this? Follow the step-by-step [SETUP_GUIDE.md](SETUP_GUIDE.md).** The short version:
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in your PayPal sandbox Client ID/Secret and AI settings.
3. `python app.py`, then open http://localhost:5000

To get a dispute to test with: in the PayPal sandbox, use a US Personal account to pay a US Business account (the one your app belongs to), then open a dispute from Activity > Report a problem. Enable **Customer disputes** and **Transaction search** on the app.

## Judges: quick test
1. Open the live demo and click the dispute.
2. Click **Build response plan**, then ask the assistant to draft a reply (try uploading a small text or image file first).
3. Try sending the draft with placeholders left in: it is blocked.

## Limits and roadmap
- Sandbox only. Buyer-side screens need buyer-level API permissions we don't have.
- Uploaded files inform the drafts but are not yet attached to the PayPal message (PayPal supports multipart attachments; planned).
- Planned: webhooks for new disputes and deadlines, buyer-facing status updates, partial-refund suggestions.

MIT licensed.
