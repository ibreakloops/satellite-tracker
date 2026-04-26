# backend/tle_fetcher.py
import httpx
import logging
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Satellite
import datetime

logger = logging.getLogger(__name__)

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

def parse_tle_block(lines):
    """Parses a 3-line TLE block into dict."""
    if len(lines) < 3:
        return None
    
    name = lines[0].strip()
    line1 = lines[1].strip()
    line2 = lines[2].strip()
    
    # Validate TLE format
    if not line1.startswith('1 ') or not line2.startswith('2 '):
        return None

    try:
        norad_id_str = line1[2:7]
        norad_id = int(norad_id_str)
    except ValueError as e:
        logger.warning(f"Failed to parse NORAD ID from '{line1}': {e}")
        return None
        
    return {
        "norad_id": norad_id,
        "name": name,
        "line1": line1,
        "line2": line2
    }

async def fetch_and_store_tles():
    """Fetches TLEs from CelesTrak and stores/updates in DB."""
    logger.info("Starting TLE fetch...")
    
    # Add User-Agent to avoid 403
    headers = {
        "User-Agent": "SatelliteTracker/1.0 (owllet@mac)"
    }
    
    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        try:
            response = await client.get(CELESTRAK_URL)
            
            # Check if we got a 403 or other error
            if response.status_code != 200:
                logger.error(f"CelesTrak returned status {response.status_code}: {response.text[:200]}")
                return

            text = response.text
            
            # Quick check if response is actually TLE data
            if not text.strip().startswith(('1 ', '2 ', 'ISS')):
                logger.warning(f"Response does not look like TLE data: {text[:200]}")
                return
            
            # Split by newlines and group into blocks of 3
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            
            db = SessionLocal()
            count = 0
            errors = 0
            try:
                for i in range(0, len(lines), 3):
                    block = lines[i:i+3]
                    data = parse_tle_block(block)
                    if data:
                        existing = db.query(Satellite).filter(Satellite.norad_id == data['norad_id']).first()
                        if existing:
                            existing.name = data['name']
                            existing.line1 = data['line1']
                            existing.line2 = data['line2']
                            existing.updated_at = datetime.datetime.utcnow()
                        else:
                            new_sat = Satellite(**data)
                            db.add(new_sat)
                        count += 1
                    else:
                        errors += 1
                
                db.commit()
                logger.info(f"Updated/Stored {count} satellites. Skipped {errors} blocks.")
            except Exception as e:
                db.rollback()
                logger.error(f"DB Error during TLE store: {e}", exc_info=True)
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Fetch Error: {e}", exc_info=True)