import os, time, requests
from dotenv import load_dotenv

load_dotenv()
BASE = "https://api-m.sandbox.paypal.com"
_token = {"value": None, "exp": 0}

def get_token():
    if _token["value"] and time.time() < _token["exp"] - 60:
        return _token["value"]
    r = requests.post(
        f"{BASE}/v1/oauth2/token",
        auth=(os.environ["PAYPAL_CLIENT_ID"], os.environ["PAYPAL_CLIENT_SECRET"]),
        data={"grant_type": "client_credentials"},
        timeout=20,
    )
    r.raise_for_status()
    j = r.json()
    _token.update(value=j["access_token"], exp=time.time() + j["expires_in"])
    return _token["value"]

def _h():
    return {"Authorization": f"Bearer {get_token()}", "Content-Type": "application/json"}

def list_disputes():
    r = requests.get(f"{BASE}/v1/customer/disputes", headers=_h(), timeout=20)
    r.raise_for_status()
    return r.json().get("items", [])

def get_dispute(dispute_id):
    r = requests.get(f"{BASE}/v1/customer/disputes/{dispute_id}", headers=_h(), timeout=20)
    r.raise_for_status()
    return r.json()

def send_message(dispute_id, message):
    r = requests.post(f"{BASE}/v1/customer/disputes/{dispute_id}/send-message",
                      headers=_h(), json={"message": message}, timeout=20)
    r.raise_for_status()
    return r.json()