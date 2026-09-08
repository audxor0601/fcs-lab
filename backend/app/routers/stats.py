"""통계 조회 API."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, stats
from ..database import get_db

router = APIRouter(prefix="/api/stats", tags=["stats"])

# miss 와의 관계를 살펴볼 변수들
CORR_FIELDS = {
    "dy": "표적과의 고저차 [m]",
    "dist": "사거리 [m]",
    "drift_deg": "편류각 [deg]",
    "enemy_speed": "표적 속도 [m/s]",
    "speed_err": "속도 추정 오차 [m/s]",
}


def _shot_rows(shots, exclude_terrain: bool) -> List[dict]:
    """Shot 객체를 계산용 dict 로 편다. terrain(지형 오폭) 제외 여부를 여기서 건다."""
    rows = []
    for s in shots:
        if exclude_terrain and s.kind == "terrain":
            continue
        speed_err = (
            abs(s.est_speed - s.enemy_speed)
            if s.est_speed is not None and s.enemy_speed is not None
            else None
        )
        rows.append({
            "miss": s.miss, "kind": s.kind, "zone": s.zone,
            "dy": s.dy, "dist": s.dist, "drift_deg": s.drift_deg,
            "enemy_speed": s.enemy_speed, "speed_err": speed_err,
        })
    return rows


@router.get("/runs")
def runs_overview(
    exclude_terrain: bool = Query(True, description="지형 오폭을 뺄지"),
    db: Session = Depends(get_db),
):
    """회차별 요약. 대시보드 첫 화면에 쓸 데이터."""
    experiments = (
        db.query(models.Experiment).order_by(models.Experiment.run_no).all()
    )

    out = []
    for exp in experiments:
        rows = _shot_rows(exp.shots, exclude_terrain)
        summary = stats.summarize([r["miss"] for r in rows])
        out.append({
            "experiment_id": exp.id,
            "name": exp.name,
            "run_no": exp.run_no,
            "note": exp.note,
            "enemy_fire": exp.enemy_fire,
            "total_shots": exp.shot_count,
            "analyzed_shots": len(rows),
            "terrain_excluded": exp.shot_count - len(rows) if exclude_terrain else 0,
            **summary,
            "warning": stats.mean_median_gap_warning(summary),
        })

    # 조건이 다른 회차가 섞여 있으면 통째로 경고한다. 섞어서 평균 내면 의미가 없다.
    conditions = {(e["enemy_fire"],) for e in out}
    notice = None
    if len(conditions) > 1:
        notice = ("실험 조건(적 사격 여부)이 다른 회차가 섞여 있습니다. "
                  "조건별로 나눠서 보십시오.")

    return {"runs": out, "notice": notice}


@router.get("/experiments/{exp_id}")
def experiment_detail(
    exp_id: int,
    exclude_terrain: bool = Query(True),
    db: Session = Depends(get_db),
):
    """한 회차를 깊이 본다 — 전체 요약, zone별, 변수별 상관."""
    exp = db.get(models.Experiment, exp_id)
    if not exp:
        raise HTTPException(404, "해당 회차가 없습니다.")

    rows = _shot_rows(exp.shots, exclude_terrain)
    overall = stats.summarize([r["miss"] for r in rows])

    correlations = []
    misses = [r["miss"] for r in rows]
    for field, label in CORR_FIELDS.items():
        r = stats.pearson([row[field] for row in rows], misses)
        correlations.append({
            "field": field,
            "label": label,
            "r": r,
            "interpretation": stats.describe_corr(r, overall["n"]),
        })

    return {
        "experiment_id": exp.id,
        "name": exp.name,
        "run_no": exp.run_no,
        "note": exp.note,
        "overall": overall,
        "warning": stats.mean_median_gap_warning(overall),
        "by_zone": stats.group_by(rows, "zone"),
        "correlations": correlations,
    }


@router.get("/compare")
def compare_runs(
    ids: List[int] = Query(..., description="비교할 회차 id (2개 이상)"),
    exclude_terrain: bool = Query(True),
    db: Session = Depends(get_db),
):
    """회차 두 개 이상을 나란히 놓고 비교한다."""
    if len(ids) < 2:
        raise HTTPException(400, "비교하려면 회차를 2개 이상 골라야 합니다.")

    items = []
    for exp_id in ids:
        exp = db.get(models.Experiment, exp_id)
        if not exp:
            raise HTTPException(404, f"회차 id {exp_id} 가 없습니다.")
        rows = _shot_rows(exp.shots, exclude_terrain)
        summary = stats.summarize([r["miss"] for r in rows])
        items.append({
            "experiment_id": exp.id, "name": exp.name, "run_no": exp.run_no,
            "note": exp.note, "enemy_fire": exp.enemy_fire,
            **summary,
            "by_zone": stats.group_by(rows, "zone"),
        })

    verdict = _compare_verdict(items)
    return {"items": items, "verdict": verdict}


def _compare_verdict(items: List[dict]) -> str:
    """비교 결과를 한 문장으로. 판단 근거가 약하면 약하다고 말한다."""
    usable = [i for i in items if i["median"] is not None]
    if len(usable) < 2:
        return "비교할 만한 사격 기록이 없는 회차가 있습니다."

    if {i["enemy_fire"] for i in usable} != {usable[0]["enemy_fire"]}:
        return "적 사격 조건이 서로 다른 회차입니다. 오차를 직접 비교하면 안 됩니다."

    best = min(usable, key=lambda i: i["median"])
    worst = max(usable, key=lambda i: i["median"])
    gap = worst["median"] - best["median"]

    if not all(i["reliable"] for i in usable):
        thin = [str(i["run_no"]) for i in usable if not i["reliable"]]
        return (f"{best['name']} 이 중앙값 {best['median']} m 로 가장 좋지만, "
                f"{', '.join(thin)}회차는 표본이 적어 확정할 수 없습니다.")

    if gap < 0.1:
        return "회차 간 차이가 0.1 m 미만입니다. 의미 있는 차이로 보기 어렵습니다."

    return (f"{best['name']} 이 중앙값 {best['median']} m 로 가장 좋습니다 "
            f"({worst['name']} 대비 {round(gap, 2)} m 우수).")
