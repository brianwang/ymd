import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api import auth, users, points, media, posts, admin, events, admin_events, coliving_inquiries, admin_coliving_inquiries

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="uploads"), name="static")

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(points.router, prefix=f"{settings.API_V1_STR}/points", tags=["points"])
app.include_router(media.router, prefix=f"{settings.API_V1_STR}", tags=["media"])
app.include_router(posts.router, prefix=f"{settings.API_V1_STR}", tags=["posts"])
app.include_router(events.router, prefix=f"{settings.API_V1_STR}", tags=["events"])
app.include_router(coliving_inquiries.router, prefix=f"{settings.API_V1_STR}", tags=["coliving"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(admin_events.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin-events"])
app.include_router(admin_coliving_inquiries.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin-coliving"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Nomad Island API"}
