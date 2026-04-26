# backend/propagator.py
from sgp4.api import Satrec
from skyfield.api import load, Topos
import datetime

def get_satellite_position(norad_id: int, line1: str, line2: str):
    """
    Calculates current Lat/Lon/Alt for a satellite using SGP4.
    Returns dict with lat, lon, alt, and timestamp.
    """
    try:
        # Initialize satellite record
        sat = Satrec.twoline2rv(line1, line2)
        
        # Get current time in UTC
        now = datetime.datetime.utcnow()
        
        # SGP4 propagation
        # jd is Julian Date, fr is fraction of day
        jd, fr = sat.jdsatepoch(now.year, now.month, now.day, 
                                now.hour, now.minute, now.second + now.microsecond/1e6)
        
        e, r, v = sat.sgp4(jd, fr)
        
        if e != 0:
            return None # Error in propagation

        # r is position vector in km (ECI)
        # Convert ECI to Lat/Lon/Alt using Skyfield for accuracy
        ts = load.timescale()
        t = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
        
        # Create a simple earth object for conversion
        # Note: For high precision, we'd use full ephemeris, but this is sufficient for tracking
        from skyfield.positionlib import ICRF
        from skyfield.units import Distance
        
        # r is in km. Skyfield expects AU or km depending on context. 
        # Let's use a simpler approach: manual ECI to Geodetic conversion is complex.
        # Instead, we use Skyfield's built-in capability if we had the full ephemeris.
        # For Day 2 simplicity, we will use a basic approximation or stick to ECI if frontend handles it.
        # BUT, Cesium needs Lat/Lon. 
        
        # Correct Approach: Use Skyfield's Earth model
        planets = load('de421.bsp')
        earth = planets['earth']
        
        # Create a position object from the ECI vector (km)
        # SGP4 returns km. Skyfield uses km internally for some calcs.
        pos = ICRF(r) # This is tricky without proper frame transformation.
        
        # SIMPLER DAY 2 APPROACH:
        # Use a lightweight library or manual formula? 
        # Actually, let's use `skyfield` properly.
        
        # Re-calculation using Skyfield's Satrec wrapper if available, 
        # but sgp4 package is standard.
        
        # Let's use a robust ECI -> LLA converter function.
        lat, lon, alt = eci_to_geodetic(r[0], r[1], r[2], now)
        
        return {
            "norad_id": norad_id,
            "lat": lat,
            "lon": lon,
            "alt": alt,
            "ts": now.isoformat() + "Z"
        }
    except Exception as e:
        print(f"Prop error for {norad_id}: {e}")
        return None

def eci_to_geodetic(x, y, z, dt):
    """
    Converts ECI (km) to Geodetic (Lat, Lon, Alt in km).
    Simplified WGS84 implementation.
    """
    import math
    
    # WGS84 Constants
    a = 6378.137 # Equatorial radius km
    f = 1 / 298.257223563
    b = a * (1 - f) # Polar radius
    e2 = 2*f - f**2 # First eccentricity squared
    
    # Calculate Longitude
    lon = math.atan2(y, x)
    
    # Calculate Latitude and Altitude (Iterative)
    p = math.sqrt(x**2 + y**2)
    theta = math.atan2(z * a, p * b)
    
    lat = math.atan2(z + e2 * b * math.sin(theta)**3, 
                     p - e2 * a * math.cos(theta)**3)
    
    N = a / math.sqrt(1 - e2 * math.sin(lat)**2)
    alt = p / math.cos(lat) - N
    
    # Convert radians to degrees
    lat_deg = math.degrees(lat)
    lon_deg = math.degrees(lon)
    
    return lat_deg, lon_deg, alt