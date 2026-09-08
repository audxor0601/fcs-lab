"""실험 회차 업로드/조회 API."""
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..csv_parser import CsvFormatError, parse_shots_csv
from ..database import get_db

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


@router.post("", response_model=schemas.ExperimentOut, status_code=201)
def upload_experiment(
    file: UploadFile = File(...),
    name: str = Form(...),
    note: str = Form(""),
    enemy_fire: bool = Form(False),
    moving_fire: bool = Form(True),
    probe_no_los: bool = Form(False),
    db: Session = Depends(get_db),
):
    """shots CSV 한 개를 실험 1회차로 등록한다."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "CSV 파일만 올릴 수 있습니다.")

    raw = file.file.read()
    try:
        meta, records = parse_shots_csv(raw, file.filename)
    except CsvFormatError as e:
        raise HTTPException(422, str(e)) from e

    exp = models.Experiment(
        name=name,
        note=note,
        enemy_fire=enemy_fire,
        moving_fire=moving_fire,
        probe_no_los=probe_no_los,
        **meta,
    )
    db.add(exp)
    db.flush()  # exp.id 를 얻기 위해

    db.add_all([models.Shot(experiment_id=exp.id, **r) for r in records])
    db.commit()
    db.refresh(exp)
    return exp


@router.get("", response_model=List[schemas.ExperimentOut])
def list_experiments(db: Session = Depends(get_db)):
    return (
        db.query(models.Experiment)
        .order_by(models.Experiment.run_no.desc().nullslast())
        .all()
    )


@router.get("/{exp_id}", response_model=schemas.ExperimentOut)
def get_experiment(exp_id: int, db: Session = Depends(get_db)):
    exp = db.get(models.Experiment, exp_id)
    if not exp:
        raise HTTPException(404, "해당 회차가 없습니다.")
    return exp


@router.get("/{exp_id}/shots", response_model=List[schemas.ShotOut])
def get_shots(exp_id: int, db: Session = Depends(get_db)):
    exp = db.get(models.Experiment, exp_id)
    if not exp:
        raise HTTPException(404, "해당 회차가 없습니다.")
    return exp.shots


@router.delete("/{exp_id}", status_code=204)
def delete_experiment(exp_id: int, db: Session = Depends(get_db)):
    exp = db.get(models.Experiment, exp_id)
    if not exp:
        raise HTTPException(404, "해당 회차가 없습니다.")
    db.delete(exp)
    db.commit()
