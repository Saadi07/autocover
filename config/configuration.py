import os
from pathlib import Path
from dotenv import load_dotenv
import json

# Loading Enviornment Vairables
dotenv_path = Path("./config/.env")
load_dotenv(dotenv_path=dotenv_path)

BUBBLE_API_KEY = os.environ["BUBBLE_API_KEY"]
BUBBLE_API_URL = os.environ["BUBBLE_API_URL"]
CHARGEBEE_API_KEY = os.environ["CHARGEBEE_API_KEY"]
CHARGEBEE_WEBHOOK_SECRET = os.environ["CHARGEBEE_WEBHOOK_SECRET"]
VEHICLE_DATA_API_KEY = os.environ["VEHICLE_DATA_API_KEY"]
VEHICLE_DATAPACKAGE = os.environ["VEHICLE_DATAPACKAGE"]
SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
CLOSEIO_KEY = os.environ["CLOSEIO_KEY"]
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
AWS_REGION_NAME = os.environ["AWS_REGION_NAME"]

# Headers for Bubble.io
BUBBLE_HEADERS = {
    "Authorization": f"Bearer {BUBBLE_API_KEY}",
    "Content-Type": "application/json",
}
BUBBLE_HEADERS2 = {
    "Authorization": f"bearer {BUBBLE_API_KEY}",
    "Content-Type": "application/json",
}
