from pydantic import BaseModel

# Pydantic model for request validation
class LoginRequest(BaseModel):
    username: str
    password: str