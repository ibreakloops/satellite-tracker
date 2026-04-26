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
    
    # Extract NORAD ID from Line 1 (characters 3-7)
    try:
        norad_id = int(line1[2:7])
    except ValueError:
        return None
        
    return {
        "norad_id": norad_id,
        "name": name,
        "line1": line1,
        "line2": line2
    }

async def fetch_and_store_tles():
    """Fetches TLEs from CelesTrak and stores/updates in DB."""
    logger