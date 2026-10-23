import pytest

from zzz_lv.application.hollow_zero.lost_void import lost_void_aether_activity as aa


@pytest.mark.parametrize(('text', 'expected'), [
    ('以太活性：无活性增幅0/9', 0),
    ('以太活性：无活性增幅 0 / 9', 0),
    ('以太活性：活性增幅 3 / 9', 3),
    ('9/9', 9),
    ('以太活性：无活性增幅', None),
    ('', None),
    ('12 / 9', None),
])
def test_parse_points(text: str, expected: int | None) -> None:
    assert aa.parse_points(text) == expected


@pytest.mark.parametrize(('text', 'expected'), [
    ('LOCK', True), ('lock', True), ('L OCK', True), ('500', False), ('', False),
])
def test_is_locked(text: str, expected: bool) -> None:
    assert aa.is_locked(text) == expected


def test_pick_row_skips_locked_empty_and_tried() -> None:
    row_texts = ['增幅甲', '增幅乙', '', '增幅丁']
    tag_texts = ['500', 'LOCK', '', '500']
    assert aa.pick_row(row_texts, tag_texts, set()) == 0
    assert aa.pick_row(row_texts, tag_texts, {'增幅甲'}) == 3
    assert aa.pick_row(row_texts, tag_texts, {'增幅甲', '增幅丁'}) is None


def test_pick_row_all_locked() -> None:
    assert aa.pick_row(['甲', '乙'], ['LOCK', 'LOCK'], set()) is None


@pytest.mark.parametrize(('before', 'after', 'expected'), [
    (0, 1, aa.CLICK_SELECTED),
    (2, 1, aa.CLICK_UNDO),
    (3, 3, aa.CLICK_INVALID),
])
def test_judge_click(before: int, after: int, expected: str) -> None:
    assert aa.judge_click(before, after) == expected
