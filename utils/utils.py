from config.configuration import BUBBLE_API_URL , CHARGEBEE_WEBHOOK_SECRET , BUBBLE_HEADERS
import hashlib
import base64
import hmac
import requests
import json

ApiKey = "a8df5fce-086c-4431-b897-a6b1e5d000b4"
DataPackage = "VehicleData"
VRM = "KM14AKK"

# Verify Chargebee webhook signature
def verify_chargebee_signature(payload, signature):
    secret = bytes(CHARGEBEE_WEBHOOK_SECRET, 'utf-8')
    payload = bytes(payload, 'utf-8')
    expected_signature = base64.b64encode(hmac.new(secret, payload, hashlib.sha256).digest()).decode()

    return expected_signature == signature

# Function to send data to Bubble.io
def send_to_bubble(data, data_type):
    #print("data", data)
    response = requests.post(BUBBLE_API_URL+data_type, headers=BUBBLE_HEADERS, json=data)
    print("bubble response: ",response.text)
    return json.loads(response.text)

def get_vehicle_info(vehicle_reg_no):
    ResponseJSON = ""
 
    # Create payload dictionary
    Payload = {
       "v" : 2, # Package version
       "api_nullitems" : 1, # Return null items
       "key_vrm" : vehicle_reg_no, # Vehicle registration mark
	   "auth_apikey" : ApiKey # Set the API Key
    }
 
    # Create GET Request (Include payload & headers)
    r = requests.get('https://uk1.ukvehicledata.co.uk/api/datapackage/{}'.format(DataPackage), params = Payload)
    print(r)
 
    # Check for a successful response
    if r.status_code == requests.codes.ok:
       # -> Request was successful
 
       # Response JSON Object
       ResponseJSON = r.json()
       #print(ResponseJSON)
       return ResponseJSON
 
    else:
       # -> Request was not successful
       ErrorContent = 'Status Code: {}, Reason: {}'.format(r.status_code, r.reason)
       print(ErrorContent)