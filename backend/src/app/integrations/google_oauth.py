import httpx
from app.config.settings import settings

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"


async def verify_google_token(id_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_TOKEN_INFO_URL,
            params={"id_token": id_token},
        )

    if response.status_code != 200:
        raise ValueError("Invalid Google token")

    data = response.json()

    if data.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise ValueError("Token audience mismatch")

    return {
        "email": data["email"],
        "name": data.get("name", ""),
        "provider_id": data["sub"],
    }
