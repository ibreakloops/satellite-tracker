import asyncio
import sys
sys.path.append('.') 

from backend.tle_fetcher import fetch_and_store_tles
from backend.database import SessionLocal
from backend.models import Satellite  # <--- CHANGE THIS

async def main():
    print("Starting manual fetch...")
    await fetch_and_store_tles()
    
    db = SessionLocal()
    count = db.query(Satellite).count()
    print(f"Satellites in DB after fetch: {count}")
    
    if count > 0:
        first_sat = db.query(Satellite).first()
        print(f"First sat: {first_sat.name} (NORAD: {first_sat.norad_id})")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(main())