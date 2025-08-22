from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from db.mysql import get_db
import os

security = HTTPBearer()

def verify_dev_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    if token != os.getenv("DEVELOPER_TOKEN"):
        raise HTTPException(status_code=403, detail="Not allowed")
