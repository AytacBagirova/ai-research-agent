from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db import init_db
from backend.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Server başlayanda cədvəlləri yarat.
    Server dayananda təmizlik işləri.
    """
    await init_db()
    print("✅ Veritabanı hazırdır!")
    yield
    print("🔴 Server dayanır...")


app = FastAPI(
    title="AI Research Agent",
    description="Autonomous research agent powered by Claude",
    version="1.0.0",
    lifespan=lifespan
)

# ==================================================
# CORS — Frontend-in backend-ə müraciət etməsinə icazə ver
# ==================================================
# Lovable-dan və ya localhost-dan gələn sorğulara icazə ver
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React dev server
        "http://localhost:5173",   # Vite dev server
        "http://localhost:8080",
        "https://*.lovable.app",   # Lovable deployment
    ],
    allow_credentials=True,
    allow_methods=["*"],           # GET, POST, DELETE...
    allow_headers=["*"],
)

# Bütün API endpointlərini qeydiyyata al
app.include_router(router)


@app.get("/")
async def root():
    """
    Health check — server işləyirmi?
    """
    return {"status": "ok", "message": "AI Research Agent işləyir!"}