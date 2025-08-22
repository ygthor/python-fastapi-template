from pydantic import BaseModel
from datetime import date
from typing import Optional

class UserCreateSchema(BaseModel):
    username: str
    password: str

class UserEditSchema(BaseModel):
    user_id: str
    password: str

class UserSubscriptionSchema(BaseModel):
    user_id: int
    subscription_id: int
    date_from: date
    date_to: date
    amount: Optional[float] = None