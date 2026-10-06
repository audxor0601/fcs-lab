"""통계 계산.

라우터에서 분리한 이유: 계산 규칙은 API 모양과 상관없이 테스트할 수 있어야 한다.

여기서 지키는 원칙 두 가지.
1) 대표값은 중앙값을 먼저 쓴다. terrain 오폭 한 발이 평균을 크게 흔들기 때문이다.
2) 표본이 적으면 수치와 함께 신뢰도 경고를 같이 돌려준다.
   7발짜리 회차의 평균을 31발짜리와 나란히 놓으면 잘못된 결론이 나온다.
"""
import statistics
from typing import List, Optional

# 이보다 표본이 적으면 경고를 붙인다.
MIN_RELIABLE_N = 10
# 상관계수가 이 값보다 작으면 "관계 없음"으로 본다.
WEAK_CORR = 0.3


def _clean(values: List[Optional[float]]) -> List[float]:
    return [v for v in values if v is not None]


def hit_rate(rows: List[dict]) -> dict:
    """명중률. kind == "tank" 가 표적 명중, "terrain" 은 지형 착탄(빗나감)이다.

    p_hit 은 발사 직전에 계산한 예측 확률이라 실제 결과가 아니다. 쓰지 않는다.
    """
    total = len(rows)
    if total == 0:
        return {"shots": 0, "hits": 0, "misses": 0, "hit_rate": None,
                "hit_rate_reliable": False}

    hits = sum(1 for r in rows if r.get("kind") == "tank")
    return {
        "shots": total,
        "hits": hits,
        "misses": total - hits,
        "hit_rate": round(hits / total * 100, 1),
        "hit_rate_reliable": total >= MIN_RELIABLE_N,
    }


def summarize(misses: List[Optional[float]]) -> dict:
    """오차 목록 하나를 요약한다."""
    vals = _clean(misses)
    n = len(vals)
    if n == 0:
        return {"n": 0, "median": None, "mean": None, "best": None,
                "worst": None, "stdev": None, "reliable": False}

    return {
        "n": n,
        "median": round(statistics.median(vals), 3),
        "mean": round(statistics.fmean(vals), 3),
        "best": round(min(vals), 3),
        "worst": round(max(vals), 3),
        "stdev": round(statistics.stdev(vals), 3) if n > 1 else None,
        "reliable": n >= MIN_RELIABLE_N,
    }


def mean_median_gap_warning(summary: dict) -> Optional[str]:
    """평균과 중앙값이 크게 벌어지면 이상치가 있다는 뜻이다."""
    if not summary["n"] or summary["median"] is None:
        return None
    med, mean = summary["median"], summary["mean"]
    if med > 0 and mean / med >= 2.0:
        return (f"평균({mean})이 중앙값({med})의 2배를 넘습니다. "
                "빗나간 몇 발이 평균을 끌어올린 상태이므로 중앙값으로 판단하십시오.")
    return None


def pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    """상관계수. 표본이 3개 미만이거나 한쪽이 상수면 None."""
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    xv = [p[0] for p in pairs]
    yv = [p[1] for p in pairs]
    if len(set(xv)) < 2 or len(set(yv)) < 2:
        return None
    try:
        return round(statistics.correlation(xv, yv), 3)
    except statistics.StatisticsError:
        return None


def describe_corr(r: Optional[float], n: int) -> str:
    """상관계수를 사람이 읽을 문장으로. 과잉해석을 막는 게 목적이다."""
    if r is None:
        return "표본이 부족해 판단할 수 없습니다."
    if n < MIN_RELIABLE_N:
        return f"표본 {n}발로는 판단 근거가 약합니다."
    if abs(r) < WEAK_CORR:
        return "뚜렷한 관계가 보이지 않습니다."
    direction = "커질수록 오차가 커집니다" if r > 0 else "커질수록 오차가 작아집니다"
    strength = "강한" if abs(r) >= 0.7 else "어느 정도"
    return f"{strength} 관계가 있습니다 — 값이 {direction}."


def group_by(rows: List[dict], key: str) -> List[dict]:
    """zone 또는 kind 같은 항목별로 묶어 요약한다."""
    buckets: dict = {}
    for r in rows:
        buckets.setdefault(r.get(key) or "unknown", []).append(r.get("miss"))

    out = []
    for name, misses in buckets.items():
        s = summarize(misses)
        s[key] = name
        out.append(s)
    return sorted(out, key=lambda d: (d["median"] is None, d["median"]))


# ── 실험 조건 비교 ────────────────────────────────────────────
# 표적 속도가 다르면 난이도가 다르다. 같은 오차라도 의미가 다르므로
# 나란히 놓고 비교하면 안 된다.
SPEED_RATIO_TOLERANCE = 1.25


def speed_profile(speeds: List[Optional[float]]) -> Optional[float]:
    """회차의 대표 표적 속도. 중앙값을 쓴다."""
    vals = _clean(speeds)
    return round(statistics.median(vals), 2) if vals else None


def comparable_speed(a: Optional[float], b: Optional[float]) -> bool:
    """두 회차의 표적 속도가 같은 조건으로 볼 만한가."""
    if a is None or b is None or a <= 0 or b <= 0:
        return True  # 판단할 근거가 없으면 막지 않는다
    hi, lo = max(a, b), min(a, b)
    return hi / lo <= SPEED_RATIO_TOLERANCE


def speed_mix_warning(speeds: List[Optional[float]]) -> Optional[str]:
    """여러 회차를 함께 볼 때 표적 속도가 섞였는지 본다."""
    vals = [s for s in speeds if s is not None and s > 0]
    if len(vals) < 2:
        return None
    hi, lo = max(vals), min(vals)
    if hi / lo <= SPEED_RATIO_TOLERANCE:
        return None
    return (f"표적 속도가 회차마다 다릅니다 ({lo} ~ {hi} m/s, 최대 {hi/lo:.1f}배). "
            "속도가 빠를수록 맞히기 어려우므로, 오차만 놓고 회차를 비교하면 "
            "느린 조건이 유리해 보입니다. 속도가 비슷한 회차끼리 묶어서 보십시오.")


# ── 사격 자세 ────────────────────────────────────────────────
# 아군이 서서 쏘는지 달리면서 쏘는지에 따라 난이도가 다르다.
MOVING_SPEED = 1.0  # m/s — 이 이상이면 움직이는 중으로 본다
MOVING_SHARE = 0.15  # 이 비율 이상이 움직이며 쏜 사격이면 기동 사격 회차

def firing_posture(my_speeds: List[Optional[float]]) -> Optional[str]:
    """회차의 사격 자세.

    중앙값은 쓸 수 없다. 기동 사격 회차에도 잠시 멈춰서 쏜 탄이 많아
    중앙값이 0 근처로 내려간다. 움직이며 쏜 탄의 '비율'로 판정한다.
    """
    vals = _clean(my_speeds)
    if not vals:
        return None
    share = sum(1 for v in vals if v >= MOVING_SPEED) / len(vals)
    return "기동" if share >= MOVING_SHARE else "정지"


# ── 기록 무결성 ──────────────────────────────────────────────
# 시뮬레이터는 발사할 때마다 id 를 1씩 올린다. 그런데 착탄 정보가 들어오지
# 않으면 그 발의 행 자체가 빠진다. 행 수만 세면 분모가 조용히 줄어들고
# 명중률이 저절로 올라간다. id 가 건너뛴 자리를 찾아 따로 센다.


def record_integrity(shot_nos: List[Optional[int]]) -> dict:
    """발사 번호가 이어지는지 본다.

    발사 수 = max(id), 기록 수 = 행 수, 미기록 = 그 사이에 빠진 id.
    한계: 마지막 발부터 끊긴 경우는 잡지 못한다. 중간이 비어야 보인다.
    """
    nums = [int(n) for n in shot_nos if n is not None]
    recorded = len(nums)
    uniq = sorted(set(nums))
    if not uniq:
        return {"recorded": 0, "fired": 0, "unmatched": 0,
                "missing_ids": [], "duplicated": 0, "ok": True}

    fired = uniq[-1]
    present = set(uniq)
    missing = [i for i in range(1, fired + 1) if i not in present]
    return {
        "recorded": recorded,
        "fired": fired,
        "unmatched": len(missing),
        "missing_ids": missing,
        "duplicated": recorded - len(uniq),
        "ok": not missing and recorded == len(uniq),
    }


def _id_ranges(ids: List[int]) -> str:
    """[14,15,16,25] -> '14~16번, 25번'"""
    if not ids:
        return ""
    parts, start, prev = [], ids[0], ids[0]
    for i in ids[1:] + [None]:
        if i is not None and i == prev + 1:
            prev = i
            continue
        parts.append(f"{start}번" if start == prev else f"{start}~{prev}번")
        if i is not None:
            start = prev = i
    return ", ".join(parts)


def integrity_warning(info: dict, hits: Optional[int] = None) -> Optional[str]:
    """분모가 어긋났을 때 무엇이 왜곡되는지까지 말한다."""
    msgs = []
    if info["unmatched"]:
        msg = (f"발사 {info['fired']}발 중 기록은 {info['recorded']}발입니다. "
               f"{_id_ranges(info['missing_ids'])} 기록이 없습니다.")
        if hits is not None and info["fired"]:
            by_rec = round(hits / info["recorded"] * 100, 1) if info["recorded"] else None
            by_fired = round(hits / info["fired"] * 100, 1)
            msg += (f" 기록 기준 명중률 {by_rec}%, 발사 기준 {by_fired}%입니다. "
                    "빠진 발을 빼고 계산하면 실제보다 높게 나옵니다.")
        else:
            msg += " 빠진 발을 빼고 계산하면 명중률이 실제보다 높게 나옵니다."
        msgs.append(msg)
    if info["duplicated"]:
        msgs.append(f"같은 발사 번호가 {info['duplicated']}건 중복됩니다. "
                    "파일이 두 번 이어붙었을 수 있습니다.")
    return " ".join(msgs) or None


def hit_rate_by_fired(hits: int, fired: int) -> Optional[float]:
    """발사 수를 분모로 한 보수적 명중률."""
    return round(hits / fired * 100, 1) if fired else None
