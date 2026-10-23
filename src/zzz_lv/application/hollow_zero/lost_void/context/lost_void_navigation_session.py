"""寻路采样：一局内每段移动的结果、卡住原因、按键和截图，用于对比寻路改动前后的耗时。"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock
from typing import Literal
from uuid import uuid4

import cv2
import numpy as np

NavigationOutcome = Literal['arrived', 'failed', 'interrupted', 'combat', 'target_changed']
NavigationStuckReason = Literal['scene_static', 'icon_static', 'target_lost', 'search_exhausted']
RunOutcome = Literal['normal', 'failed', 'interrupted']
NavigationEventName = Literal[
    'run_start', 'run_end', 'move_start', 'frame', 'action', 'stuck', 'move_end', 'level_end',
]


@dataclass(frozen=True)
class NavigationTarget:
    """截图中当前追踪目标的位置。"""

    name: str
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class NavigationAction:
    """移动按键或镜头变化；横向转动正数表示右转。"""

    keys: tuple[str, ...] = ()
    turn_dx: float = 0
    duration_seconds: float = 0
    operation: str = 'stop'


class LostVoidNavigationSession:
    """一局的采样记录 写到 runs/<run_id>/ 下 不修改全局 debug 或用户配置。"""

    def __init__(self, base_dir: Path) -> None:
        """建立本局目录并写入开始事件。"""
        self.run_id: str = uuid4().hex
        self.level_id: str = ''
        self.movement_id: str = ''
        self.started_at: float = time.time()
        self.last_frame_at: float = 0
        self.last_action: NavigationAction = NavigationAction()
        self.level_failed: bool = False
        self.closed: bool = False
        run_dir = base_dir.resolve() / 'runs' / self.run_id
        self.image_dir: Path = run_dir / 'images'
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.event_path: Path = run_dir / 'events.jsonl'
        self._write_lock: Lock = Lock()
        self.emit('run_start')

    def emit(self, event: NavigationEventName, timestamp: float | None = None, **details: object) -> None:
        """追加一条带同局、楼层和移动编号的事件。"""
        record = {
            'event': event, 'timestamp': time.time() if timestamp is None else timestamp,
            'run_id': self.run_id, 'level_id': self.level_id, 'movement_id': self.movement_id,
            **details,
        }
        with self._write_lock, self.event_path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + '\n')

    def begin_level(self) -> None:
        """为新一次层间操作生成编号。"""
        self.level_id = uuid4().hex
        self.movement_id = ''
        self.level_failed = False

    def begin_move(self, target_type: str) -> None:
        """记录一段完整移动的开始。"""
        self.movement_id = uuid4().hex
        self.last_frame_at = 0
        self.last_action = NavigationAction()
        self.emit('move_start', target_type=target_type)

    def action(self, action: NavigationAction) -> None:
        """记录已经发出的控制请求。"""
        self.last_action = action
        self.emit('action', **asdict(action))

    def frame(self, screen: np.ndarray, timestamp: float, target: NavigationTarget | None, force: bool = False) -> None:
        """每秒至多保存一张画面 右下角 UID 涂黑。"""
        if not force and timestamp - self.last_frame_at < 1:
            return
        self.last_frame_at = timestamp
        image_path = self.image_dir / f'{self.movement_id}_{round(timestamp * 1000)}.jpg'
        image = screen.copy()
        height, width = image.shape[:2]
        image[round(1059 * height / 1080):height, round(1814 * width / 1920):width] = 0
        success, encoded = cv2.imencode('.jpg', cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
                                         [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not success:
            raise OSError('无法编码寻路采样截图')
        encoded.tofile(str(image_path))
        self.emit('frame', timestamp=timestamp, image_path=str(image_path),
                  target=asdict(target) if target is not None else None,
                  action=asdict(self.last_action))

    def finish(self, outcome: RunOutcome) -> None:
        """一局终态只记录一次，停止与失败不能记为正常完成。"""
        if self.closed:
            return
        self.emit('run_end', outcome=outcome, duration_seconds=time.time() - self.started_at)
        self.closed = True
