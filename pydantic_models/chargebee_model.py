from pydantic import BaseModel 

class ChargebeeEvent(BaseModel):
    event_type: str
    content: dict
