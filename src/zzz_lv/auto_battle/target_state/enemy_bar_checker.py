"""
敌人血条相关的像素识别 坐标都按 1080p

- BOSS 失衡条：右上角 BOSS 血条下方的细条
  左边空掉的部分是纯灰色 右边是一段颜色均匀的条 按右边那段的颜色区分状态
  - 积累中：黄到橙的渐变 长度就是失衡值
  - 失衡中：颜色在粉、青、黄之间循环 长度是剩余失衡时间
  - 失衡冷却：浅灰色 失衡结束后约 9 秒从满缩到 0 期间打不出失衡
- 异常积蓄圈：被锁定敌人头顶小血条右边的圆标
  中间图案表示属性 外圈从顶部顺时针点亮 点亮的比例就是积蓄进度
  流明的外圈分成四段 四段全亮就是满 段与段之间的缺口按亮处理
  圆标跟着敌人移动 大小也随镜头远近变化（实测约 1~2.5 倍）
  用它的黑色描边和左边的灰色三角做形状模板 按几种比例分别找
"""
from dataclasses import dataclass
from enum import Enum

import cv2
import numpy as np
from cv2.typing import MatLike


class StunPhase(Enum):

    BUILDING = '积累中'
    STUNNED = '失衡中'
    RECOVERING = '失衡冷却'


@dataclass
class StunResult:

    phase: StunPhase
    percent: int  # 积累中是失衡值 其余是剩余比例 0~100


@dataclass
class AnomalyBuildupResult:

    attribute: str  # 属性 物理 / 风 / 流明
    percent: int  # 积蓄进度 0~100


# 写入自动战斗的状态名 值都是 0~100
# 失衡条三种状态各对应一个 同一时间只保留一个
STUN_STATE_NAMES: dict[StunPhase, str] = {
    StunPhase.BUILDING: '强敌-失衡值',
    StunPhase.STUNNED: '强敌-失衡中',
    StunPhase.RECOVERING: '强敌-失衡冷却',
}
ANOMALY_ATTRIBUTES: tuple[str, ...] = ('物理', '风', '流明')
ANOMALY_STATE_PREFIX: str = '目标-异常积蓄-'
ENEMY_BAR_STATE_NAMES: list[str] = list(STUN_STATE_NAMES.values()) + [ANOMALY_STATE_PREFIX + i for i in ANOMALY_ATTRIBUTES]


# 失衡条
_STUN_LEFT: int = 1135
_STUN_RIGHT: int = 1638
_STUN_ROWS: slice = slice(73, 76)
_STUN_BORDER_ROWS: tuple[int, int] = (67, 81)  # 条上下的黑色描边 用来判断 UI 是否在画面上
_EMPTY_GRAY: int = 64

# 异常积蓄圆标 尺寸都是 1 倍大小时的值
_ICON_SEARCH_RECT: tuple[int, int, int, int] = (60, 130, 1860, 800)  # x1 y1 x2 y2 避开顶部血条和右下角按键
_ICON_SCALES: tuple[float, ...] = (1.0, 1.3, 1.7, 2.2, 2.8)
_ICON_TEMPLATE_CENTER: tuple[int, int] = (40, 16)  # 圆心在模板里的位置
_ICON_TEMPLATE_LEFT: int = 10  # 模板最左边是血条上的数字 每次不一样 不参与比较
_ICON_MATCH_THRESHOLD: float = 0.55
_ICON_OUTLINE_R: float = 13
_ICON_RING_R: tuple[float, ...] = (9.75, 10.5, 11.25)  # 在外圈宽度内取几个半径
_ICON_DISK_R: tuple[float, float] = (7.5, 8.5)  # 外圈和中心图案之间的暗色底
_ICON_CENTER_R: tuple[float, float, float] = (3, 4, 5)
_ICON_TRIANGLE_OFFSET: tuple[float, float] = (-15, 8)  # 左边灰色三角的中心

_RING_ANGLES: np.ndarray = np.deg2rad(np.arange(0, 360, 3))  # 从顶部开始顺时针
_OUTLINE_ANGLES: np.ndarray = np.deg2rad(np.arange(0, 360, 10))


def check_boss_stun(screen: MatLike) -> StunResult | None:
    """
    识别 BOSS 失衡条

    Args:
        screen: 1080p RGB 游戏画面

    Returns:
        StunResult | None: 画面上没有失衡条（没有 BOSS、连携或终结技演出把 UI 藏起来）时返回 None
    """
    span = screen[:, _STUN_LEFT:_STUN_RIGHT + 1]
    for row in _STUN_BORDER_ROWS:
        if span[row].max(axis=1).mean() > 40:
            return None

    bar = span[_STUN_ROWS].astype(np.int16).mean(axis=0)  # 每一列的平均色
    total = bar.shape[0]
    gray = (np.abs(bar - _EMPTY_GRAY) <= 12).all(axis=1)

    # 灰色在左 彩色在右
    filled_len = total - int(gray.sum())
    if filled_len < 5:  # 右端几个像素的杂色当作空条
        return StunResult(StunPhase.BUILDING, 0)
    if filled_len < total and gray[:total - filled_len].mean() < 0.95:
        return None
    if gray[total - filled_len:].mean() > 0.05:
        return None

    percent = filled_len * 100 // total
    r, g, b = np.median(bar[total - filled_len:], axis=0)
    spread = max(r, g, b) - min(r, g, b)
    if r >= 200 and b <= 60 and 90 <= g <= 245:
        return StunResult(StunPhase.BUILDING, percent)
    if spread <= 25 and 120 <= r <= 200:
        return StunResult(StunPhase.RECOVERING, percent)
    if spread >= 60:
        return StunResult(StunPhase.STUNNED, percent)
    return None


class AnomalyBuildupChecker:

    def __init__(self, icon_template: MatLike):
        """
        Args:
            icon_template: 异常积蓄圆标模板原图 RGB
        """
        dark = self._to_dark_map(icon_template)
        self._template: MatLike = cv2.resize(dark, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)

        # 圆里面的属性图案和最左边的数字不参与比较
        h, w = icon_template.shape[:2]
        ys, xs = np.mgrid[0:h, 0:w]
        keep = (np.hypot(xs - _ICON_TEMPLATE_CENTER[0], ys - _ICON_TEMPLATE_CENTER[1]) >= _ICON_RING_R[1] + 0.5) & (xs >= _ICON_TEMPLATE_LEFT)
        self._mask: MatLike = cv2.resize(keep.astype(np.uint8) * 255, (self._template.shape[1], self._template.shape[0]),
                                         interpolation=cv2.INTER_NEAREST)

    def check(self, screen: MatLike) -> AnomalyBuildupResult | None:
        """
        识别被锁定敌人头顶的异常积蓄圈

        Args:
            screen: 1080p RGB 游戏画面

        Returns:
            AnomalyBuildupResult | None: 没找到圆标、被挡住或属性认不出时返回 None
        """
        icon = self.find_icon(screen)
        if icon is None:
            return None
        cx, cy, scale = icon

        center_r = tuple(r * scale for r in _ICON_CENTER_R)
        attribute = _classify_attribute(_sample_circle(screen, cx, cy, center_r, _OUTLINE_ANGLES).mean(axis=0))
        if attribute is None:
            return None

        disk_r = tuple(r * scale for r in _ICON_DISK_R)
        disk = np.percentile(_sample_circle(screen, cx, cy, disk_r, _RING_ANGLES).max(axis=1), 20)
        ring_r = tuple(r * scale for r in _ICON_RING_R)
        ring = _sample_circle(screen, cx, cy, ring_r, _RING_ANGLES, keep_radius=True).max(axis=2).max(axis=0)
        lit = ring >= max(disk * 1.7, disk + 50)  # 每个角度在带状区域里取最亮的点

        # 从顶部顺时针 找最远的一个亮点 要求顶部到它之间至少 3/4 是亮的
        # 这样能跨过流明圈的分段缺口、伤害数字和特效挡住的一小段 又不会越过亮段的终点
        lit_ratio = np.cumsum(lit) / np.arange(1, len(lit) + 1)
        lit_end = np.nonzero(lit & (lit_ratio >= 0.75) & (np.cumsum(lit) >= 2))[0]
        lit_cnt = int(lit_end[-1]) + 1 if len(lit_end) > 0 else 0
        return AnomalyBuildupResult(attribute, lit_cnt * 100 // len(lit))

    def find_icon(self, screen: MatLike) -> tuple[int, int, float] | None:
        """
        按几种比例用形状模板找圆标 再在全分辨率下微调圆心

        Returns:
            tuple[int, int, float] | None: 圆心坐标和圆标大小比例
        """
        x1, y1, x2, y2 = _ICON_SEARCH_RECT
        dark = self._to_dark_map(screen[y1:y2, x1:x2])

        # 模板是 1 倍大小缩小一半 所以 s 倍大小的圆标要把画面缩小到 0.5 / s
        best_match: tuple[float, int, int, float] | None = None
        for scale in _ICON_SCALES:
            fx = 0.5 / scale
            part = cv2.resize(dark, None, fx=fx, fy=fx, interpolation=cv2.INTER_AREA)
            if part.shape[0] < self._template.shape[0] or part.shape[1] < self._template.shape[1]:
                continue
            result = cv2.matchTemplate(part, self._template, cv2.TM_CCOEFF_NORMED, mask=self._mask)
            result = np.nan_to_num(result, nan=-1, posinf=-1, neginf=-1)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if best_match is None or max_val > best_match[0]:
                cx = x1 + round((max_loc[0] + _ICON_TEMPLATE_CENTER[0] * 0.5) / fx)
                cy = y1 + round((max_loc[1] + _ICON_TEMPLATE_CENTER[1] * 0.5) / fx)
                best_match = (max_val, cx, cy, scale)

        if best_match is None or best_match[0] < _ICON_MATCH_THRESHOLD:
            return None
        _, cx, cy, scale = best_match

        height, width = screen.shape[:2]
        margin = int(_ICON_OUTLINE_R * scale) + 6
        if not (margin <= cx < width - margin and margin <= cy < height - margin):
            return None

        # 比例只有几个档位 圆心也有缩小匹配的误差
        # 在附近同时搜圆心和描边半径 描边是最暗的一圈 用实测半径换算准确的比例
        offset = max(3, round(scale * 3))
        r_min = _ICON_OUTLINE_R * scale * 0.8
        r_max = _ICON_OUTLINE_R * scale * 1.25
        best: tuple[float, int, int, float] | None = None
        for dx in range(-offset, offset + 1):
            for dy in range(-offset, offset + 1):
                for outline_r in np.arange(r_min, r_max, 0.5):
                    outline = _sample_circle(screen, cx + dx, cy + dy, (outline_r,), _OUTLINE_ANGLES).max(axis=1).mean()
                    if best is None or outline < best[0]:
                        best = (outline, cx + dx, cy + dy, outline_r)
        _, cx, cy, outline_r = best
        scale = outline_r / _ICON_OUTLINE_R

        # 左边必须有灰色三角 排除技能按键这类同样是黑边圆形的东西
        tx = round(cx + _ICON_TRIANGLE_OFFSET[0] * scale)
        ty = round(cy + _ICON_TRIANGLE_OFFSET[1] * scale)
        triangle = screen[ty - 1:ty + 2, tx - 1:tx + 2].reshape(-1, 3).astype(np.int16)
        if (triangle.max(axis=1) - triangle.min(axis=1)).mean() > 30:
            return None
        return cx, cy, scale

    @staticmethod
    def _to_dark_map(image: MatLike) -> MatLike:
        """
        转成「比周围暗」的二值图
        用局部自适应阈值 半透明特效盖在圆标上整体变亮时描边仍然算暗
        """
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 25)


def _sample_circle(
    screen: MatLike,
    cx: int,
    cy: int,
    radius_list: tuple[float, ...],
    angles: np.ndarray,
    keep_radius: bool = False,
) -> np.ndarray:
    """
    在若干半径的圆周上采样像素 角度 0 为正上方 顺时针增加

    Returns:
        np.ndarray: keep_radius 时形状为 (半径数, 角度数, 3) 否则把所有半径的采样点拼在一起 (n, 3)
    """
    samples = []
    for r in radius_list:
        xs = np.rint(cx + r * np.sin(angles)).astype(int)
        ys = np.rint(cy - r * np.cos(angles)).astype(int)
        samples.append(screen[ys, xs].astype(np.int16))
    stacked = np.stack(samples)
    return stacked if keep_radius else stacked.reshape(-1, 3)


def _classify_attribute(rgb: np.ndarray) -> str | None:
    """
    按圆标中心图案的平均色判断属性 目前只认得实战截图里见过的三种
    """
    hsv = cv2.cvtColor(np.uint8([[np.clip(rgb, 0, 255)]]), cv2.COLOR_RGB2HSV)[0, 0]
    hue, sat, val = int(hsv[0]), int(hsv[1]), int(hsv[2])
    if sat < 60 or val < 80:
        return None
    if 15 <= hue <= 35:
        return '物理'
    if 85 <= hue <= 115:
        return '风'
    if 140 <= hue <= 175:
        return '流明'
    return None
