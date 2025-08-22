from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from db.mysql import get_db
from db.models import User
import os
from core.security import decode_token
from jose import JWTError

security = HTTPBearer(auto_error=True)  # This enables Swagger integration

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Middleware-safe user injector
async def inject_user_into_request(
    request: Request, 
    user: User = Depends(get_current_user)
) -> User:
    request.state.user = user
    return user