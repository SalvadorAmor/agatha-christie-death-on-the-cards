from sqlalchemy import create_engine
from sqlmodel import Session
from app.settings import settings

db_engine = create_engine(url=settings.db_url, max_overflow=0, pool_size=30)

def db_session():
    with Session(db_engine) as session:
            yield session