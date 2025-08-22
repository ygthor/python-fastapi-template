# 6. api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db.mysql import get_db
from db.models import User
from pydantic import BaseModel
from core.security import hash_password, verify_password, create_token
import logging
from datetime import datetime
from api.models.login_request import LoginRequest

router = APIRouter(tags=["Auth"])

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/login", response_model=dict)
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    try:
        # Query user from database
        user = db.query(User).filter(User.username == data.username).first()
        if not user:
            logger.warning(f"Login attempt with non-existent username: {data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not verify_password(data.password, user.password):
            logger.warning(f"Invalid password attempt for username: {data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate JWT token
        token = create_token(user.id)
        logger.info(f"Successful login for username: {data.username} at {datetime.utcnow()}")

        # Set cache-control to prevent caching of sensitive data
        return {
            "token": token,
            "user_id": user.id,
            "message": "Login successful"
        }

    except Exception as e:
        logger.error(f"Login error for username {data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )