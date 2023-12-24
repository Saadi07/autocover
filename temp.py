import requests
 
# Set Variables
ApiKey = "a8df5fce-086c-4431-b897-a6b1e5d000b4"
DataPackage = "VehicleData"
VRM = "KM14AKK"
ResponseJSON = ""
 
# Create payload dictionary
Payload = {
       "v" : 2, # Package version
       "api_nullitems" : 1, # Return null items
       "key_vrm" : VRM, # Vehicle registration mark
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
       print(ResponseJSON)
 
else:
       # -> Request was not successful
       ErrorContent = 'Status Code: {}, Reason: {}'.format(r.status_code, r.reason)