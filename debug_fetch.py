import httpx
import asyncio

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

async def debug():
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(CELESTRAK_URL)
            print(f"Status Code: {response.status_code}")
            text = response.text
            
            # Print first 500 chars to see if it's HTML error or TLE data
            print("First 500 chars of response:")
            print(text[:500])
            
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            print(f"\nTotal non-empty lines: {len(lines)}")
            
            if len(lines) > 0:
                print("\nFirst 3 lines (should be a TLE block):")
                for i in range(min(3, len(lines))):
                    print(f"{i}: {lines[i]}")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug())