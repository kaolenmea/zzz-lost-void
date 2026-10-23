from zzz_lv.application.hollow_zero.lost_void.context.lost_void_depth_estimator import (
    LostVoidDepthEstimator,
)

MAX_OFFSET = 6
BLOCKED = 700  # 近处挡路
OPEN_FAR = 400  # 不挡路 障碍很远


def _rows(**overrides: int) -> list[int]:
    """16 列 默认都挡路 用 c11=500 这样的关键字覆盖某几列"""
    rows = [BLOCKED] * LostVoidDepthEstimator.COLUMN_NUM
    for key, value in overrides.items():
        rows[int(key[1:])] = value
    return rows


def test_target_column_open_needs_no_aim() -> None:
    rows = _rows(c12=500)
    assert LostVoidDepthEstimator.choose_aim_column(rows, 12, None, MAX_OFFSET) is None


def test_empty_rows_needs_no_aim() -> None:
    assert LostVoidDepthEstimator.choose_aim_column([], 12, None, MAX_OFFSET) is None


def test_farther_clear_column_beats_nearer_one() -> None:
    # 11 列刚好不挡路 13 列很空 代价 11: 590+15 13: 400+15
    rows = _rows(c11=590, c13=OPEN_FAR)
    assert LostVoidDepthEstimator.choose_aim_column(rows, 12, None, MAX_OFFSET) == 13


def test_closer_to_target_wins_when_clearance_is_similar() -> None:
    rows = _rows(c11=500, c14=500)
    assert LostVoidDepthEstimator.choose_aim_column(rows, 12, None, MAX_OFFSET) == 11


def test_keeps_previous_column_when_cost_is_close() -> None:
    # 11 列代价 515 13 列代价 505 差在 AIM_KEEP_MARGIN 以内
    rows = _rows(c11=500, c13=490)
    assert LostVoidDepthEstimator.choose_aim_column(rows, 12, 11, MAX_OFFSET) == 11


def test_switches_previous_column_when_much_worse() -> None:
    rows = _rows(c11=590, c13=OPEN_FAR)
    assert LostVoidDepthEstimator.choose_aim_column(rows, 12, 11, MAX_OFFSET) == 13


def test_previous_column_now_blocked_is_dropped() -> None:
    rows = _rows(c13=OPEN_FAR)
    assert LostVoidDepthEstimator.choose_aim_column(rows, 12, 11, MAX_OFFSET) == 13


def test_character_columns_are_not_candidates() -> None:
    # 6~9 列是角色所在的列 从头顶往上扫 行很小但不能当作空的
    rows = _rows(c6=424, c7=424, c4=500)
    assert LostVoidDepthEstimator.choose_aim_column(rows, 5, None, MAX_OFFSET) == 4


def test_no_open_column_within_range_returns_none() -> None:
    rows = _rows(c0=OPEN_FAR)
    assert LostVoidDepthEstimator.choose_aim_column(rows, 12, None, MAX_OFFSET) is None
