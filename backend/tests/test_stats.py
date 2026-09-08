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
