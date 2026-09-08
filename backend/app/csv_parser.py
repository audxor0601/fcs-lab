"""shots CSV 파서.

시뮬레이터가 내려주는 파일에는 두 가지 함정이 있다.
1) UTF-8 BOM 이 붙어 있어 그냥 읽으면 첫 컬럼명이 'id' 가 아니라 '\ufeffid' 가 된다.
2) 한 발도 못 쏜 회차는 헤더만 있고 데이터가 0행이다.
둘 다 여기서 막는다.
"""
import io
import re

import pandas as pd

REQUIRED_COLUMNS = [
    "id", "t", "dist", "tof", "p_hit", "miss", "kind", "zone",
    "drift_deg", "enemy_speed", "my_speed", "hull_pitch", "hull_roll",
    "est_speed", "dy", "bias_range", "bias_n", "lon_shift",
]

# experiment 로 올라가는 컬럼 (전 행이 같은 값)
EXPERIMENT_LEVEL = ["bias_range", "bias_n", "lon_shift"]


class CsvFormatError(ValueError):
    """CSV 형식이 기대와 다를 때."""


def extract_run_no(filename: str):
    """'shots (33).csv' 에서 33 을 뽑는다. 없으면 None."""
    m = re.search(r"\((\d+)\)", filename or "")
    return int(m.group(1)) if m else None


def parse_shots_csv(raw: bytes, filename: str = ""):
    """CSV 바이트를 받아 (실험 조건 dict, 사격 기록 list) 로 돌려준다."""
    try:
        # utf-8-sig 로 읽으면 BOM 이 있든 없든 알아서 벗겨진다.
        df = pd.read_csv(io.BytesIO(raw), encoding="utf-8-sig")
    except Exception as e:
        raise CsvFormatError(f"CSV 를 읽지 못했습니다: {e}") from e

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise CsvFormatError(f"필수 컬럼이 없습니다: {', '.join(missing)}")

    meta = {
        "run_no": extract_run_no(filename),
        "source_filename": filename,
        "shot_count": len(df),
        "bias_range": None,
        "bias_n": None,
        "lon_shift": None,
    }

    # 0행이어도 에러 없이 빈 회차로 저장한다. 못 쏜 것도 기록이다.
    if df.empty:
        return meta, []

    for col in EXPERIMENT_LEVEL:
        uniques = df[col].dropna().unique()
        if len(uniques) > 1:
            raise CsvFormatError(
                f"'{col}' 이 한 파일 안에서 여러 값입니다({list(uniques)}). "
                "실험 조건이 도중에 바뀐 파일로 보입니다."
            )
        if len(uniques) == 1:
            meta[col] = uniques[0].item()

    shot_cols = [c for c in REQUIRED_COLUMNS if c not in EXPERIMENT_LEVEL]
    records = df[shot_cols].rename(columns={"id": "shot_no"}).to_dict("records")

    # NaN 은 JSON 으로 못 내보내므로 None 으로 바꾼다.
    for r in records:
        for k, v in r.items():
            if pd.isna(v):
                r[k] = None

    return meta, records
