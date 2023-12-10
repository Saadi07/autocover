from fastapi import FastAPI, HTTPException, Body, Header
from pydantic import BaseModel
import requests
import hmac
import hashlib
import base64

app = FastAPI()

# Bubble.io credentials
bubble_api_key = 'c17190332efe7b9d5eab556e26709f84'
bubble_api_url = 'https://claims-gurus.co.uk/version-test/api/1.1/obj/test-type'

# Headers for Bubble.io
bubble_headers = {
    'Authorization': f'Bearer {bubble_api_key}',
    'Content-Type': 'application/json'
}

# Chargebee credentials
chargebee_api_key = 'test_wlhvyK1x3BLGGhFd6sUJjIxybQvQ5TW2'

# Chargebee webhook secret key
chargebee_webhook_secret = 'your_chargebee_webhook_secret'  # Replace with your actual Chargebee webhook secret

# Model for Chargebee event data
class ChargebeeEvent(BaseModel):
    event_type: str
    content: dict

# Endpoint to receive Chargebee webhook events
@app.post("/chargebee-webhook")
async def chargebee_webhook(
    event: ChargebeeEvent = Body(...),
   # signature: str = Header(...),
):
    print("here" ,event)
    # Verify the webhook signature for security
    # if not verify_chargebee_signature(event.json(), signature):
    #     raise HTTPException(status_code=400, detail="Invalid Chargebee webhook signature")

    # Process Chargebee event and send to Bubble.io
    try:
        bubble_data = map_chargebee_event_to_bubble_data(event)
        send_to_bubble(bubble_data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Verify Chargebee webhook signature
def verify_chargebee_signature(payload, signature):
    secret = bytes(chargebee_webhook_secret, 'utf-8')
    payload = bytes(payload, 'utf-8')
    expected_signature = base64.b64encode(hmac.new(secret, payload, hashlib.sha256).digest()).decode()

    return expected_signature == signature

# Function to send data to Bubble.io
def send_to_bubble(data):
    response = requests.post(bubble_api_url, headers=bubble_headers, json=data)
    response.raise_for_status()

# Function to map Chargebee event data to Bubble.io format
def map_chargebee_event_to_bubble_data(chargebee_event):
    # Implement your mapping logic here based on the Chargebee event data
    # This is just a placeholder, customize it according to your needs
    return {
        'event_type': chargebee_event.event_type,
        'data': chargebee_event.content,
        # Add more fields as needed
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)