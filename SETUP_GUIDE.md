# Dispute Defender: Complete Setup Guide (no experience needed)

This guide assumes you have never run a program like this before. Follow the steps in order. It takes about 30-40 minutes. Everything uses **free** accounts and fake "sandbox" money. No real money or real customer data is ever involved.

**Don't want to set anything up?** Open the live demo link in the README instead. Part 8 below tells you how to try it.

---

## What this app does (in plain words)
When a buyer files a complaint ("dispute") against a seller on PayPal, the seller often doesn't know what to do. Dispute Defender:
1. Shows the seller their disputes.
2. Explains in plain language what the dispute means and what evidence is needed.
3. Lets the seller upload evidence (screenshots, PDFs) and chat with an AI assistant that writes a polite reply using **only real facts**. If a fact is missing, the reply keeps a `[placeholder]` and **cannot be sent** until it is filled in.
4. Lets the seller refund the buyer in one click when they can't prove their side, which is fairer to the customer and closes the dispute fast.

---

## Part 1: Install Python (one time)
1. Go to https://www.python.org/downloads/ and download Python for Windows.
2. Open the installer. **Tick the box "Add python.exe to PATH"** at the bottom, then click Install Now.
3. When finished, open the **Start menu**, type `powershell`, press Enter. In the blue window, type `py --version` and press Enter. You should see something like `Python 3.12.x`. If you see an error, restart your computer and try again.

## Part 2: Get the project files
1. On the project's GitHub page, click the green **Code** button, then **Download ZIP**.
2. Right-click the downloaded ZIP, choose **Extract All**, and extract to a simple place such as `C:\dispute-defender`.
3. Open that folder. You should see files like `app.py`, `llm.py`, `README.md`.

## Part 3: Install the program's helpers
1. In File Explorer, open the project folder. Click the address bar at the top, type `powershell`, and press Enter. A blue window opens **inside that folder**.
2. Type this and press Enter (wait until it finishes):
```
py -m pip install -r requirements.txt
```

## Part 4: Create a free PayPal developer account and test accounts
1. Go to https://developer.paypal.com and log in or sign up (a normal free PayPal login works).
2. Make sure the **Sandbox** toggle (top left) is on, not Live.
3. In the left menu click **Testing Tools > Sandbox Accounts**, then **Create account**.
4. Create **two** accounts, **both with Country set to United States**:
   - one **Business** account (this is the seller)
   - one **Personal** account (this is the buyer)

   Important: accounts created with another country (for example India) can be blocked from sending test payments. Use United States.
5. Next to each account, click the three dots, then **View/Edit account**, and note its email and password. You'll need the Personal one later.

## Part 5: Create the PayPal "app" and copy its keys
1. In the left menu click **Apps & Credentials**. Make sure **Sandbox** is selected.
2. Click **Create App**. Name it `dispute-defender`, type **Merchant**, and for the sandbox account choose your **United States Business** account (very important).
3. On the app page, scroll to **Features** and tick **Customer disputes** and **Transaction search**. Click **Save Changes**.
4. Near the top of the app page you'll see **Client ID** and **Secret** (click **Show** to reveal the Secret). Keep this page open. Treat these like passwords: never post them publicly.

## Part 6: Get a free AI key
1. Go to Google AI Studio (https://aistudio.google.com) and sign in with a Google account.
2. Open **API keys** and click **Create API key**. Copy it.
3. Pick a model name to use. A good free choice is a "Flash" or "Flash-Lite" model, for example `gemini-2.5-flash-lite`. If the app later says the model was not found, pick another Flash model name listed in AI Studio.

## Part 7: Put your keys in the settings file
1. In the project folder find `.env.example`. (If Windows shows it as `env.example`, rename it to `.env.example` first.)
2. In your blue PowerShell window (still inside the project folder), run:
```
copy .env.example .env
notepad .env
```
3. Notepad opens. Fill in the values **right after the `=` sign, with no spaces and no quotes**:
```
PAYPAL_CLIENT_ID=paste your Client ID here
PAYPAL_CLIENT_SECRET=paste your Secret here
AI_PROVIDER=gemini
AI_MODEL=gemini-2.5-flash-lite
AI_API_KEY=paste your Google AI key here
```
4. Save the file (Ctrl+S) and close Notepad.

Tip: copy each value with the copy icons on the websites. If you get "invalid_client" errors later, one of the PayPal values was copied wrongly: re-copy both.

## Part 8: Start the app
1. In the blue window, run:
```
py app.py
```
2. Leave this window open. Open your web browser and go to: **http://localhost:5000**
3. You'll see "Open disputes". It will be empty until you create a test dispute (next part).

## Part 9: Create a test dispute (pretend to be a buyer)
1. Open a **private/incognito browser window**. Go to https://sandbox.paypal.com and log in with your **Personal** sandbox account (email and password from Part 4).
2. Click **Send and Request**, enter your **Business** account's email, send **$20** with a note such as "logo design".
3. Click **Activity**, open that payment, and choose **Report a problem**. Fill in the form, pick a reason such as "I didn't get what I paid for", and **submit it all the way to the end**.
4. Go back to http://localhost:5000 and refresh. Your dispute appears.

## Part 10: Use the app
1. Click the dispute.
2. Click **Build response plan**. You'll see what the dispute means, a checklist of evidence (marked **Missing** when you haven't provided it), and an honest risk note.
3. **Ask the assistant:** upload a screenshot, PDF or text file that proves your work, then ask something like "What should I tell the buyer?" Click **Use as my reply** to move its draft into the reply box.
4. In the reply box, replace every `[bracketed]` part with real details. The **Send reply to buyer** button stays grey until none are left.
5. Click **Send reply to buyer**.
6. If you can't prove your side, click **Refund buyer in full**. This refunds the buyer and closes the dispute, and it **cannot be undone**.

## Stopping and restarting
- To stop: click the blue window and press **Ctrl + C**.
- To start again: open PowerShell in the project folder and run `py app.py`.

## Troubleshooting
| What you see | What to do |
|---|---|
| `py` is not recognized | Reinstall Python and tick "Add python.exe to PATH" (Part 1), then restart the computer. |
| `invalid_client` / authentication failed | Re-copy the PayPal Client ID and Secret into `.env`. Make sure Sandbox was selected, and that the app belongs to your Business account. |
| The dispute list is empty | The dispute must be against the **same Business account** your app was created on. Create the payment and dispute again (Part 9). |
| "Model not found" from the AI | Change `AI_MODEL` in `.env` to another Flash model from AI Studio, then restart. |
| Send money is blocked in the sandbox | Your test accounts must be created with Country = United States. |
| The refund button is missing | PayPal only shows it when the dispute allows it. Try a newer dispute. |
| Port 5000 already in use | Close other copies of the app, or restart the computer. |

## Safety notes
- This runs in PayPal's **sandbox**: fake money, fake accounts.
- Never share your `.env` file or post your keys. The project's `.gitignore` keeps `.env` out of GitHub.
- For real disputes, use an AI provider whose data terms you trust. The free tier used here may use requests to improve its products, so use test data only.
