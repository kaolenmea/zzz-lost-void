from zzz_lv.application.hollow_zero.lost_void.operation.lost_void_move_by_det import (
    LostVoidMoveByDet,
)

MIN_DIFF = LostVoidMoveByDet.ESCAPE_DEPTH_MIN_DIFF


def test_left_clearly_emptier_goes_left() -> None:
    # 行越大障碍越近 左侧平均行小 = 左侧更空
    assert LostVoidMoveByDet.pick_escape_side_by_depth([300, 320], [600, 620], MIN_DIFF) is True


def test_right_clearly_emptier_goes_right() -> None:
    assert LostVoidMoveByDet.pick_escape_side_by_depth([600, 620], [300, 320], MIN_DIFF) is False


def test_small_difference_returns_none() -> None:
    assert LostVoidMoveByDet.pick_escape_side_by_depth([400, 405], [410, 415], MIN_DIFF) is None


def test_empty_side_returns_none() -> None:
    assert LostVoidMoveByDet.pick_escape_side_by_depth([], [400], MIN_DIFF) is None
    assert LostVoidMoveByDet.pick_escape_side_by_depth([400], [], MIN_DIFF) is None
