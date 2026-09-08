"""FCS Lab API 진입점."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import experiments, stats

# 개발 단계에서는 테이블을 코드로 만든다.
# 스키마가 굳어지면 Alembic 마이그레이션으로 옮길 것.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FCS Lab", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(experiments.router)
app.include_router(stats.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# 화면은 이 서버가 직접 내려준다.
# 브라우저에서 파일을 직접 열면 CORS 에 막히기 때문이다.
STATIC_DIR = Path(__file__).parent.parent / "static"
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
