from fastapi import HTTPException, Body, APIRouter
from config.logger import logger
from pydantic_models.chargebee_model import ChargebeeEvent
from  services.event_service import chargebee_payment_success_service

event_router = APIRouter(
    prefix="/api/event",
    tags=["file"],
    responses={404: {"description": "Not found"}},
)



@event_router.post("/chargebee-payment-success")
def chargebee_payment_success_router(event: ChargebeeEvent = Body(...)):
    try:
        chargebee_event = dict(event)
        if chargebee_event['event_type'] == 'payment_succeeded':
            chargebee_payment_success_service(chargebee_event)
        print("Here")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error occurred while processing chargebee event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


