import os
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, Request
from pydantic import BaseModel

router = APIRouter()

class MediaUploadOut(BaseModel):
    url: str

@router.post("/media/upload", response_model=MediaUploadOut)
async def upload_media(request: Request, file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1]
    filename = f"{uuid4().hex}{ext}"
    path = os.path.join("uploads", filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    url = str(request.url_for("static", path=filename))
    return {"url": url}
