# backend/main.py
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from .database import engine, Base, get_db, init_db
from .tle_fetcher import fetch_and_store_tles
from .models import Satellite  # <--- IMPORT THIS
from .propagator import get_satellite_position
import asyncio
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Satellite Tracker API")

@app.on_event("startup")
def startup_event():
    init_db()
    # Trigger initial fetch
    asyncio.create_task(fetch_and_store_tles())
    # Schedule periodic refresh (every 12 hours = 43200 seconds)
    asyncio.create_task(periodic_refresh())

async def periodic_refresh():
    while True:
        await asyncio.sleep(43200) 
        await fetch_and_store_tles()

@app.get("/")
def read_root():
    return {"status": "online", "service": "Satellite Tracker"}

# DEBUG ENDPOINT
@app.get("/api/debug/sats")
def debug_sats(db: Session = Depends(get_db)):
    sats = db.query(Satellite).limit(5).all()
    return [{"id": s.id, "norad": s.norad_id, "name": s.name} for s in sats]

@app.get("/api/satellites/{norad_id}/position")
def get_position(norad_id: int, db: Session = Depends(get_db)):
    sat = db.query(Satellite).filter(Satellite.norad_id == norad_id).first()
    if not sat:
        return {"error": "Satellite not found"}
    
    pos = get_satellite_position(sat.norad_id, sat.line1, sat.line2)
    if not pos:
        return {"error": "Propagation failed"}
    
    return pos

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Wait for client to send tracked IDs
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                track_ids = payload.get("track", [25544])
            except:
                track_ids = [25544]

            # Fetch satellites from DB
            db = next(get_db())
            positions = []
            for nid in track_ids:
                sat = db.query(Satellite).filter(Satellite.norad_id == nid).first()
                if sat:
                    pos = get_satellite_position(sat.norad_id, sat.line1, sat.line2)
                    if pos:
                        positions.append(pos)
            
            if positions:
                await websocket.send_json(positions)
            
            await asyncio.sleep(2) # Update every 2 seconds
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    finally:
        db.close()