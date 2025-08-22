from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session, joinedload
from db.mysql import get_db
from db.models import User, UserSubscription
import os

def get_user_by_id(user_id: int, db: Session = Depends(get_db)) -> User:
    user = db.query(User).options(
        joinedload(User.subscriptions).joinedload(UserSubscription.subscription)
    ).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user