# 7. api/dev_user.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session, joinedload
from db.mysql import get_db
from db.models import User
from pydantic import BaseModel
from passlib.context import CryptContext
import os
from api.models.dev import UserEditSchema, UserCreateSchema, UserSubscriptionSchema
from dependencies.user import get_user_by_id
from dependencies.dev_auth import verify_dev_token
from repositories.api_usage import get_monthly_api_usage

router = APIRouter(
    tags=["Dev"],
    dependencies=[Depends(verify_dev_token)]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


from fastapi import HTTPException, status

@router.post("/users")
def create_user(user_data: UserCreateSchema, db: Session = Depends(get_db)):
    # Check if username already exists
    existing_user = db.query(User).filter_by(username=user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Hash the plaintext password
    hashed_password = pwd_context.hash(user_data.password)

    # Create user
    user = User(
        username=user_data.username,
        password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"status": "user created", "user_id": user.id}


@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.get("/users/{user_id}")
def view_user(user: User = Depends(get_user_by_id)):
    return {
        "id": user.id,
        "username": user.username,
        "subscriptions": [
            {
                "id": usub.subscription.id,
                "name": usub.subscription.name,
                "receipt_scans": usub.subscription.receipt_scans,
                "invoice_scans": usub.subscription.invoice_scans,
                "any_scans": usub.subscription.any_scans,
                "date_from": usub.date_from.isoformat(),
                "date_to": usub.date_to.isoformat(),
                "amount": usub.amount,
            }
            for usub in user.subscriptions
        ]
    }

@router.get("/users_usage_monthly")
def usage_stats(db: Session = Depends(get_db)):
    return get_monthly_api_usage(db) 


@router.put("/users/{user_id}")
def edit_user(
    user_id: int,
    data: UserEditSchema, 
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.system_prompt = data.get("system_prompt", user.system_prompt)
    db.commit()
    return {"status": "user updated"}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db.query(User).filter(User.id == user_id).delete()
    db.commit()
    return {"status": "user deleted"}

@router.get("/subscriptions")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.post("/users/subscription")
def user_subscription(data: UserSubscriptionSchema, db: Session = Depends(get_db)):
    # Check if subscription exists for the user in the same range
    existing = db.query(UserSubscription).filter(
        UserSubscription.user_id == data.user_id,
        UserSubscription.date_to >= data.date_from
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already has an active subscription in this period")

    new_subscription = UserSubscription(
        user_id=data.user_id,
        subscription_id=data.subscription_id,
        date_from=data.date_from,
        date_to=data.date_to,
        amount=data.amount,
        subscribed_at=datetime.utcnow()
    )

    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)

    return {
        "status": "subscription created",
        "data": {
            "id": new_subscription.id,
            "user_id": new_subscription.user_id,
            "subscription_id": new_subscription.subscription_id,
            "date_from": new_subscription.date_from,
            "date_to": new_subscription.date_to
        }
    }