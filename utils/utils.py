from config.configuration import BUBBLE_API_URL , CHARGEBEE_WEBHOOK_SECRET , BUBBLE_HEADERS
import hashlib
import base64
import hmac
import requests

# Verify Chargebee webhook signature
def verify_chargebee_signature(payload, signature):
    secret = bytes(CHARGEBEE_WEBHOOK_SECRET, 'utf-8')
    payload = bytes(payload, 'utf-8')
    expected_signature = base64.b64encode(hmac.new(secret, payload, hashlib.sha256).digest()).decode()

    return expected_signature == signature

# Function to send data to Bubble.io
def send_to_bubble(data):
    print("data", data)
    response = requests.post(BUBBLE_API_URL, headers=BUBBLE_HEADERS, json=data)
    response.raise_for_status()
