import re

from zzz_lv.application.hollow_zero.lost_void.lost_void_config import (
    AETHER_ACTIVITY_MAX,
)

ROW_COUNT: int = 4  # 活性增幅列表一屏显示的行数
MAX_CLICK_TIMES: int = 24  # 单次最多点击次数 防止识别异常时一直点

CLICK_SELECTED: str = '已选中'
CLICK_UNDO: str = '点数减少'
CLICK_INVALID: str = '点数没变'


def parse_points(text: str) -> int | None:
    """
    从「以太活性：无活性增幅 3 / 9」这类文字里读出已选点数
    :return: 点数 识别不出返回 None
    """
    match = re.search(r'(\d+)\s*[/／]\s*(\d+)', text.replace('丨', '/').replace('|', '/'))
    if match is None:
        return None
    points = int(match.group(1))
    if points > AETHER_ACTIVITY_MAX:
        return None
    return points


def is_locked(tag_text: str) -> bool:
    """行右侧的标签是「LOCK」说明还没解锁 不能选"""
    return 'LOCK' in tag_text.upper().replace(' ', '')


def pick_row(row_text_list: list[str], tag_text_list: list[str], tried: set[str]) -> int | None:
    """
    在当前屏里找下一行要点的活性增幅
    :param row_text_list: 每行的增幅文字 没有这一行则为空串
    :param tag_text_list: 每行右侧标签的文字
    :param tried: 已经点过的增幅文字
    :return: 行下标 没有可点的行返回 None
    """
    for idx, (row_text, tag_text) in enumerate(zip(row_text_list, tag_text_list, strict=False)):
        if len(row_text) == 0 or row_text in tried:
            continue
        if is_locked(tag_text):
            continue
        return idx
    return None


def judge_click(before: int, after: int) -> str:
    """
    点击一行之后 按点数变化判断这次点击的效果
    点数变多 = 选中了；变少 = 点到了已经选中的行 被取消了 需要再点一次还原；没变 = 这行点不动
    """
    if after > before:
        return CLICK_SELECTED
    if after < before:
        return CLICK_UNDO
    return CLICK_INVALID
