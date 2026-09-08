"""API 입출력 스키마."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ExperimentCreate(BaseModel):
    name: str
    note: str = ""
    enemy_fire: bool = False
    moving_fire: bool = True
    probe_no_los: bool = False


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    run_no: Optional[int]
    note: str
    enemy_fire: bool
    moving_fire: bool
    probe_no_los: bool
    bias_range: Optional[float]
    bias_n: Optional[int]
    lon_shift: Optional[float]
    shot_count: int
    source_filename: str
    created_at: datetime


class ShotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shot_no: Optional[int]
    t: Optional[float]
    dist: Optional[float]
    tof: Optional[float]
    miss: Optional[float]
    kind: Optional[str]
    zone: Optional[str]
    drift_deg: Optional[float]
    enemy_speed: Optional[float]
    est_speed: Optional[float]
    dy: Optional[float]
