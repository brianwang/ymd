import os
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, Request, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

class MediaUploadOut(BaseModel):
    url: str

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}
_VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv"}

# 基本安全阈值（可按需挪到 Settings）
_MAX_IMAGE_BYTES = 10 * 1024 * 1024   # 10MB
_MAX_AUDIO_BYTES = 20 * 1024 * 1024   # 20MB
_MAX_VIDEO_BYTES = 100 * 1024 * 1024  # 100MB

def _guess_kind_by_ext(ext: str) -> str | None:
    if ext in _IMAGE_EXTS:
        return "image"
    if ext in _AUDIO_EXTS:
        return "audio"
    if ext in _VIDEO_EXTS:
        return "video"
    return None

def _max_bytes_for_kind(kind: str) -> int:
    if kind == "image":
        return _MAX_IMAGE_BYTES
    if kind == "audio":
        return _MAX_AUDIO_BYTES
    if kind == "video":
        return _MAX_VIDEO_BYTES
    return 0

@router.post("/media/upload", response_model=MediaUploadOut)
async def upload_media(request: Request, file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1].lower()
    kind = _guess_kind_by_ext(ext)
    if not kind:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型，仅支持图片/音频/视频",
        )
    ct = (file.content_type or "").lower()
    if ct and ct != "application/octet-stream":
        if kind == "image" and not ct.startswith("image/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件类型不匹配：期望图片")
        if kind == "audio" and not ct.startswith("audio/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件类型不匹配：期望音频")
        if kind == "video" and not ct.startswith("video/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件类型不匹配：期望视频")
    max_bytes = _max_bytes_for_kind(kind)
    filename = f"{uuid4().hex}{ext}"
    path = os.path.join("uploads", filename)
    written = 0
    try:
        with open(path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"文件过大：{kind} 最大支持 {max_bytes // (1024 * 1024)}MB",
                    )
                f.write(chunk)
    except HTTPException:
        # 清理半写入文件
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        raise
    if written <= 0:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="空文件不可上传")
    url = str(request.url_for("static", path=filename))
    return {"url": url}
