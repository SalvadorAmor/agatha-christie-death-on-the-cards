from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from sqlmodel import SQLModel

from app.controllers.detective_set import set_router
from app.controllers.game import game_router
from app.controllers.player import player_router
from app.database.engine import db_engine
from app.controllers.card import card_router
from app.controllers.secret import secret_router
from app.controllers.websocket import ws_router
from app.controllers.event_table import event_table_router
from app.controllers.chat import chat_router

from fastapi.middleware.cors import CORSMiddleware

authorized_hostsregex = r"http://.*:.*|ws://.*:.*"

authorized_hosts = [
    'http://localhost:3000',
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(db_engine)
    yield

base_app = FastAPI(lifespan=lifespan)
base_app.add_middleware(middleware_class=CORSMiddleware, allow_origin_regex=authorized_hostsregex, allow_methods=["*"])


base_app.include_router(game_router)
base_app.include_router(card_router)
base_app.include_router(player_router)
base_app.include_router(secret_router)
base_app.include_router(set_router)
base_app.include_router(event_table_router)
base_app.include_router(chat_router)
base_app.include_router(ws_router)

def main():
    uvicorn.run(app=base_app, host='0.0.0.0', port=8000)

if __name__ == '__main__':
    main()
