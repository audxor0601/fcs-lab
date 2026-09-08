"""테이블 정의.

experiment 하나 = 사격 실험 1회차 = shots CSV 파일 하나.
shot 은 그 회차에서 쏜 개별 탄이다.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    run_no = Column(Integer, nullable=True)  # 파일명의 (33) 같은 번호
    note = Column(Text, default="")  # 이번 회차에 무엇을 바꿨는지 — 직접 적는다

    # CSV 에 안 담기는 실험 조건. 이게 없으면 회차 비교가 무의미해진다.
    enemy_fire = Column(Boolean, default=False)
    moving_fire = Column(Boolean, default=True)
    probe_no_los = Column(Boolean, default=False)

    # CSV 전 행에 동일하게 박혀 있는 값이라 회차 속성으로 올렸다.
    bias_range = Column(Float, nullable=True)
    bias_n = Column(Integer, nullable=True)
    lon_shift = Column(Float, nullable=True)

    shot_count = Column(Integer, default=0)
    source_filename = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    shots = relationship(
        "Shot", back_populates="experiment", cascade="all, delete-orphan"
    )


class Shot(Base):
    __tablename__ = "shots"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(
        Integer, ForeignKey("experiments.id", ondelete="CASCADE"), index=True
    )

    shot_no = Column(Integer)  # CSV 의 id 컬럼. 회차 안에서의 발사 순번
    t = Column(Float)  # 발사 시각 [s]
    dist = Column(Float)  # 사거리 [m]
    tof = Column(Float)  # 비과시간 [s]
    p_hit = Column(Float)
    miss = Column(Float)  # 탄착 오차 [m] — 핵심 성능 지표
    kind = Column(String(20))  # tank / terrain
    zone = Column(String(20))  # front / rear / side
    drift_deg = Column(Float)
    enemy_speed = Column(Float)  # 표적 실제 속도 [m/s]
    my_speed = Column(Float)
    hull_pitch = Column(Float)
    hull_roll = Column(Float)
    est_speed = Column(Float)  # 추정 속도 [m/s]
    dy = Column(Float)  # 표적과의 고저차 [m]

    experiment = relationship("Experiment", back_populates="shots")
