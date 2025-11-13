from fastapi import Header, HTTPException, Depends
from typing import Optional
from app.auth.jwt_handler import decodeJWT

def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Extract and validate JWT from Authorization header.
    Expected format: Bearer <token>
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = parts[1]
    decoded = decodeJWT(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return decoded["user_id"]