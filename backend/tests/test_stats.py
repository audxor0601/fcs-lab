import pytest

from app import stats


def test_median_beats_mean_with_outlier():
    """terrain 오폭 한 발이 평균을 흔들어도 중앙값은 버텨야 한다."""
    misses = [0.8, 0.9, 1.0, 1.1, 24.7]
    s = stats.summarize(misses)
    assert s["median"] == 1.0
    assert s["mean"] > 5
    assert stats.mean_median_gap_warning(s) is not None


def test_no_warning_when_balanced():
    s = stats.summarize([1.0, 1.1, 0.9, 1.2])
    assert stats.mean_median_gap_warning(s) is None


def test_small_sample_marked_unreliable():
    assert stats.summarize([1.0] * 7)["reliable"] is False
    assert stats.summarize([1.0] * 10)["reliable"] is True


def test_empty_input():
    s = stats.summarize([])
    assert s["n"] == 0 and s["median"] is None
    assert stats.mean_median_gap_warning(s) is None


def test_none_values_are_dropped():
    s = stats.summarize([1.0, None, 3.0])
    assert s["n"] == 2


def test_pearson_needs_variation():
    assert stats.pearson([1, 1, 1], [1, 2, 3]) is None
    assert stats.pearson([1, 2], [1, 2]) is None
    assert stats.pearson([1, 2, 3], [1, 2, 3]) == 1.0


def test_weak_corr_is_not_oversold():
    """상관이 약하면 관계를 주장하면 안 된다."""
    assert "보이지 않습니다" in stats.describe_corr(-0.127, 30)


def test_small_n_blocks_interpretation():
    assert "약합니다" in stats.describe_corr(0.9, 5)


def test_group_by_zone():
    rows = [
        {"zone": "front", "miss": 1.0},
        {"zone": "front", "miss": 2.0},
        {"zone": "side", "miss": 0.5},
    ]
    out = stats.group_by(rows, "zone")
    assert out[0]["zone"] == "side"  # 중앙값 오름차순
    assert out[1]["n"] == 2


def test_speed_profile():
    assert stats.speed_profile([2.4, 2.5, 2.6]) == 2.5
    assert stats.speed_profile([]) is None


def test_speed_doubling_blocks_comparison():
    """표적 속도가 2배면 난이도가 달라 비교할 수 없다."""
    assert stats.comparable_speed(2.5, 4.9) is False
    assert stats.comparable_speed(2.5, 2.6) is True


def test_missing_speed_does_not_block():
    """근거가 없으면 막지 않는다."""
    assert stats.comparable_speed(None, 4.9) is True


def test_speed_mix_warning():
    assert stats.speed_mix_warning([2.5, 5.0]) is not None
    assert stats.speed_mix_warning([2.5, 2.6]) is None
    assert stats.speed_mix_warning([2.5]) is None


# ── 기록 무결성 ──────────────────────────────────────────────


def test_integrity_clean_run():
    """id 가 빈틈없이 이어지면 발사 수와 기록 수가 같다."""
    i = stats.record_integrity(list(range(1, 13)))
    assert i["fired"] == 12 and i["recorded"] == 12
    assert i["unmatched"] == 0 and i["ok"] is True
    assert stats.integrity_warning(i) is None


def test_integrity_detects_single_gap():
    """33회차 실제 케이스 — 기록 31발, id 1~32, 25번이 빈다."""
    nos = [n for n in range(1, 33) if n != 25]
    i = stats.record_integrity(nos)
    assert i["fired"] == 32
    assert i["recorded"] == 31
    assert i["unmatched"] == 1
    assert i["missing_ids"] == [25]
    assert i["ok"] is False
    msg = stats.integrity_warning(i, hits=29)
    assert "발사 32발" in msg and "기록은 31발" in msg
    assert "93.5%" in msg and "90.6%" in msg


def test_integrity_detects_consecutive_gap():
    """30회차 실제 케이스 — 14~16번 세 발이 통째로 빈다."""
    nos = [n for n in range(1, 21) if n not in (14, 15, 16)]
    i = stats.record_integrity(nos)
    assert i["fired"] == 20 and i["unmatched"] == 3
    assert "14~16번" in stats.integrity_warning(i)


def test_integrity_detects_duplicates():
    i = stats.record_integrity([1, 2, 2, 3])
    assert i["duplicated"] == 1 and i["ok"] is False
    assert "중복" in stats.integrity_warning(i)


def test_integrity_empty_run():
    i = stats.record_integrity([])
    assert i["fired"] == 0 and i["ok"] is True
    assert stats.integrity_warning(i) is None


def test_integrity_cannot_see_tail_loss():
    """마지막 발부터 끊긴 경우는 잡지 못한다. 한계를 못으로 박아 둔다."""
    i = stats.record_integrity(list(range(1, 31)))  # 실제로는 32발 쐈다고 해도
    assert i["fired"] == 30 and i["ok"] is True


def test_hit_rate_by_fired_is_lower():
    assert stats.hit_rate_by_fired(29, 31) == 93.5
    assert stats.hit_rate_by_fired(29, 32) == 90.6
    assert stats.hit_rate_by_fired(1, 0) is None
