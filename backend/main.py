from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import engine, Base, get_db, init_db
from .tle_fetcher import fetch_and_store_tles
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Satellite Tracker API")

@app.on_event("startup")
def startup_event():
    init_db()
    asyncio.create_task(fetch_and_store_tles())
    asyncio.create_task(periodic_refresh())

async def periodic_refresh():
    while True:
        await asyncio.sleep(43200) 
        await fetch_and_store_tles()

@app.get("/")
def read_root():
    return {"status": "online", "service": "Satellite Tracker"}