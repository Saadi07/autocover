from fastapi import FastAPI, HTTPException, Body, Header  , APIRouter ,Depends
from pydantic_models.chargebee_model import ChargebeeEvent
from config.logger import logger
from services.event_service import map_customer_data, map_vehicle_data
from utils.utils import send_to_bubble, get_vehicle_info

event_router = APIRouter(
    prefix="/api/event",
    tags=["file"],
    responses={404: {"description": "Not found"}},
)


@event_router.post("/chargebee-webhook")
def chargebee_webhook(event: ChargebeeEvent = Body(...)):
    try:
        
        chargebee_event = dict(event)
        
        if chargebee_event['event_type'] == 'payment_succeeded':
            # print(chargebee_event )
            customer_data = map_customer_data(chargebee_event)
            print("customer data", customer_data)
            res = send_to_bubble(customer_data, data_type='User')
            #print(res, type(res))
            if res['status'] == 'success':
                vehicle_reg_number = chargebee_event['content']['subscription'].get('cf_Vehicle Registration Number (Licence Plate)*', '')
                print("get_vehicle data----------------", vehicle_reg_number)
                vehicle_info = get_vehicle_info(vehicle_reg_number)
                vehicle_data = map_vehicle_data(vehicle_info, res['id'], chargebee_event)
                print("vehicle_data: ",vehicle_data)
                if (vehicle_data):
                    print("sending vehicle data")
                    res = send_to_bubble(vehicle_data, data_type='Vehicle')
                #print("vehicle data",vehicle_info)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error occcured while processing chargebee event : {e}")
        raise HTTPException(status_code=500, detail=str(e))

