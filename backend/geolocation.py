import httpx
from typing import Optional, Dict


async def get_location_from_ip(ip_address: str) -> Optional[Dict]:
    """Get location from IP address"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://ip-api.com/json/{ip_address}")
            if response.status_code == 200:
                data = response.json()
                return {
                    "country": data.get("country"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon")
                }
    except:
        return None
    return None


# Add to FastAPI main.py
@app.get("/api/detect-location")
async def detect_location(request: Request):
    """Detect user location from IP"""
    client_ip = request.client.host
    location = await get_location_from_ip(client_ip)

    if location:
        # Map city/region to district (requires district mapping database)
        # This is a simplified version
        return {"detected_location": location}

    return {"message": "Location detection failed"}
