from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.auth.jwt_handler import signJWT, decodeJWT

router = APIRouter()

class UserLoginSchema(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(user: UserLoginSchema):
    """
    Mock login — accepts any username/password.
    Returns JWT token valid for 1 hour.
    """
    token = signJWT(user.username)
    return {
        "message": f"Welcome {user.username} 👋",
        "access_token": token["access_token"],
        "token_type": "bearer"
    }

@router.get("/validate")
def validate_token(token: str):
    """
    Validate a given JWT token.
    """
    decoded = decodeJWT(token)
    if decoded:
        return {"status": "valid", "user": decoded["user_id"]}
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired token")