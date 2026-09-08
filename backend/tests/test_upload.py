import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.csv_parser import CsvFormatError, extract_run_no, parse_shots_csv
from app.database import Base, get_db
from app.main import app

HEADER = (
    "id,t,dist,tof,p_hit,miss,kind,zone,drift_deg,enemy_speed,my_speed,"
    "hull_pitch,hull_roll,est_speed,dy,bias_range,bias_n,lon_shift\n"
)
ROW = "1,68.01,32.73,0.651,1.0,1.514,tank,rear,-11.74,2.45,0.13,1.42,-1.06,2.45,3.513,-8.54,3,0.0\n"


@pytest.fixture
def client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db", connect_args={"check_same_thread": False}
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_bom_header_is_stripped():
    """BOM 이 붙어 있어도 첫 컬럼을 id 로 읽어야 한다."""
    raw = ("\ufeff" + HEADER + ROW).encode("utf-8")
    meta, records = parse_shots_csv(raw, "shots (33).csv")
    assert records[0]["shot_no"] == 1
    assert meta["bias_range"] == -8.54


def test_empty_file_is_accepted():
    """한 발도 못 쏜 회차도 저장되어야 한다."""
    meta, records = parse_shots_csv(HEADER.encode(), "shots (37).csv")
    assert meta["shot_count"] == 0
    assert records == []
    assert meta["run_no"] == 37


def test_missing_column_rejected():
    raw = "id,t,dist\n1,2,3\n".encode()
    with pytest.raises(CsvFormatError):
        parse_shots_csv(raw, "bad.csv")


def test_extract_run_no():
    assert extract_run_no("shots (33).csv") == 33
    assert extract_run_no("shots.csv") is None


def test_upload_and_read_back(client):
    raw = ("\ufeff" + HEADER + ROW).encode("utf-8")
    res = client.post(
        "/api/experiments",
        files={"file": ("shots (33).csv", io.BytesIO(raw), "text/csv")},
        data={"name": "리드사격 적용", "note": "TargetTracker 붙임", "enemy_fire": "false"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["run_no"] == 33
    assert body["shot_count"] == 1
    assert body["enemy_fire"] is False

    shots = client.get(f"/api/experiments/{body['id']}/shots").json()
    assert shots[0]["miss"] == pytest.approx(1.514)
    assert shots[0]["dy"] == pytest.approx(3.513)


def test_non_csv_rejected(client):
    res = client.post(
        "/api/experiments",
        files={"file": ("a.txt", io.BytesIO(b"x"), "text/plain")},
        data={"name": "x"},
    )
    assert res.status_code == 400
