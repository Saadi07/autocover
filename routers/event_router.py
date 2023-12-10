from fastapi import FastAPI, HTTPException, Body, Header  , APIRouter ,Depends
from pydantic_models.chargebee_model import ChargebeeEvent
from config.logger import logger
from services.event_service import map_chargebee_event_to_bubble_data
from utils.utils import send_to_bubble

event_router = APIRouter(
    prefix="/api/event",
    tags=["file"],
    responses={404: {"description": "Not found"}},
)


@event_router.post("/chargebee-webhook")
async def chargebee_webhook(event: ChargebeeEvent = Body(...)):
    try:
        bubble_data = map_chargebee_event_to_bubble_data(event)
        send_to_bubble(bubble_data)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error occcured while processing chargebee event : {e}")
        raise HTTPException(status_code=500, detail=str(e))

