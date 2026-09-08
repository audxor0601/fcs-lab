"""DB 연결 설정.

개발 중에는 SQLite 파일 하나로 돌린다. 배포할 때는 DATABASE_URL 환경변수만
PostgreSQL 주소로 바꾸면 되고, 아래 코드는 손대지 않는다.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fcs_lab.db")

# check_same_thread 는 SQLite 전용 옵션이다. Postgres 로 바꾸면 빼야 한다.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 의존성. 요청 하나당 세션 하나를 열고 끝나면 닫는다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
