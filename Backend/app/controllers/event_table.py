from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.database.engine import db_session

from app.services.event_table import EventTableFilter, PublicEventTable, EventTableService

event_table_router = APIRouter(prefix="/api/event_table")

@event_table_router.post('/search', response_model=list[PublicEventTable])
def event_table_search(dto: EventTableFilter, session: Session = Depends(db_session)):
    service = EventTableService()
    events = service.search(session=session, filterby=dto.model_dump(exclude_none=True))
    return events