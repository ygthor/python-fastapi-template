# utils/logging_middleware.py

import json
import time
import uuid
from datetime import datetime
from typing import Optional, Tuple
from fastapi import FastAPI, Request, Response, UploadFile
from starlette.types import Message
from sqlalchemy.orm import Session
from db.mysql import SessionLocal, insert_row
import logging

logger = logging.getLogger(__name__)

def extract_json(raw_response: str) -> dict:
    # Extract the first JSON block (ignoring <think> and other text)
    match = re.search(r"\{.*\}", raw_response, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON found in response")
    
    # Parse and validate JSON
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        # Fallback: Remove all <think> tags and retry
        clean_text = re.sub(r"<think>.*?</think>", "", raw_response, flags=re.DOTALL)
        return json.loads(re.search(r"\{.*\}", clean_text, flags=re.DOTALL).group())

async def extract_file_metadata(request: Request) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    file_type = filename = None
    file_size_bytes = None

    print("extract_file_metadata")

    try:
        form = await request.form()
        file = form.get("file")
        
        
        if hasattr(file, "filename") and hasattr(file, "content_type"):
            content = await file.read()
            await file.seek(0)
            print("xxxx")
            print(file.filename)
            return file.content_type, file.filename, len(content)
    except Exception as e:
        print("YYYYY")
        logger.warning(f"Failed to extract file metadata: {e}")
    return None, None, None




async def extract_request_body(request: Request) -> Optional[str]:
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()
            return json.dumps(data)
    except Exception as e:
        logger.warning(f"Failed to extract JSON body: {e}")
    return None


async def capture_response_data(response: Response) -> Tuple[bytes, Optional[str]]:
    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    try:
        decoded = body.decode("utf-8")
    except UnicodeDecodeError:
        decoded = None

    return body, decoded


def rebuild_response(original: Response, body: bytes) -> Response:
    return Response(
        content=body,
        status_code=original.status_code,
        headers=dict(original.headers),
        media_type=original.media_type
    )


def log_api_call(
    db: Session,
    request: Request,
    response: Response,
    duration_ms: int,
    file_type: Optional[str],
    filename: Optional[str],
    file_size_bytes: Optional[int],
    user_id: Optional[str],
    request_data: Optional[str],
    response_data: Optional[str]
):
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()
    status_code = response.status_code
    response_success = 200 <= status_code < 300

    insert_row("api_call_logs", {
        "endpoint": str(request.url.path),
        "method": request.method,
        "request_time": now,
        "response_time": now,
        "duration_ms": duration_ms,
        "status_code": status_code,
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent", "")[:512],
        "file_type": file_type,
        "filename": filename,
        "file_size_bytes": file_size_bytes,
        "response_success": response_success,
        "error_message": None,
        "user_id": user_id,
        "request_id": request_id,
        "request_data": request_data,
        "response_data": response_data
    })


def add_logging_middleware(app: FastAPI):
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        start_time = time.time()

        # Optional: Skip logging for docs/static
        if request.url.path.startswith("/docs") or request.url.path.startswith("/static"):
            return await call_next(request)


        # Save the original body
        body = await request.body()

        # Rebuild a request with a fresh body stream for FastAPI to read later
        async def receive() -> Message:
            return {"type": "http.request", "body": body}

        request = Request(request.scope, receive)
        
        # Get response FIRST
        response = await call_next(request)

        content_type = request.headers.get("content-type", "")

        file_type = filename = request_data = response_data = None
        file_size_bytes = None

        # Extract request info
        if request.method == "POST":
            if "multipart/form-data" in content_type:
                file_type, filename, file_size_bytes = await extract_file_metadata(request)
            elif "application/json" in content_type:
                request_data = await extract_request_body(request)


        # Capture & rebuild response if JSON
        response_body = None
        if "application/json" in response.headers.get("content-type", ""):
            response_body, response_data = await capture_response_data(response)
            response = rebuild_response(response, response_body)

        # Log the data
        duration_ms = int((time.time() - start_time) * 1000)
        with SessionLocal() as db:
            log_api_call(
                db=db,
                request=request,
                response=response,
                duration_ms=duration_ms,
                file_type=file_type,
                filename=filename,
                file_size_bytes=file_size_bytes,
                user_id=getattr(request.state, "user", None).id if hasattr(request.state, "user") else None,
                request_data=request_data,
                response_data=response_data
            )

        return response
