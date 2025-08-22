from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Form, Depends
from fastapi.responses import StreamingResponse,JSONResponse
from dependencies.auth import inject_user_into_request
from services.ai_service import AiService
from db.models import User
from pydantic import BaseModel
from typing import Optional, Dict, List

router = APIRouter(tags=["AI Features"])


@router.post("/status")
async def status(user: User = Depends(inject_user_into_request)):
    return {"message":"ok"}

@router.post("/receipt-parser")
async def receipt_parser(image: UploadFile = File(...), user: User = Depends(inject_user_into_request)):
    ai_service = AiService()
    return await ai_service.receipt_parser(image)

@router.post("/resume-parser")
async def resume_parser(
    document: UploadFile = File(...),
    positions: Optional[List[str]] = Form(None),  # <-- important!
    user: User = Depends(inject_user_into_request)
):
    ai_service = AiService()
    return await ai_service.resume_parser(document=document, positions=positions)

@router.post("/vclaim-parser")
async def vclaim_parser(
    custom_fields: Optional[str] = Form(None),  # Accept JSON string
    image: UploadFile = File(...),
    user: User = Depends(inject_user_into_request)
):
    import json
    parsed_fields = json.loads(custom_fields) if custom_fields else None

    ai_service = AiService()
    return await ai_service.vclaim_parser(image, parsed_fields)



class SummaryInput(BaseModel):
    text: str

@router.post("/chat")
async def chat(data: SummaryInput, user: User = Depends(inject_user_into_request)):
    ai_service = AiService()
    result = await ai_service.chat(data.text)
    return { "result": result }