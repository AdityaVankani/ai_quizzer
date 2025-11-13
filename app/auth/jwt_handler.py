import time
import jwt
from decouple import config

# Load secret from .env or fallback to default
SECRET_KEY = config("JWT_SECRET", default="supersecretkey")
ALGORITHM = "HS256"
TOKEN_EXPIRY = 3600  # 1 hour

def signJWT(user_id: str):
    """
    Generate JWT token for a user.
    """
    payload = {
        "user_id": user_id,
        "expires": time.time() + TOKEN_EXPIRY
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

def decodeJWT(token: str):
    """
    Decode JWT token and verify expiry.
    """
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if decoded["expires"] < time.time():
            return None
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None