"""迷失之地寻路采样：跑一局迷失之地并记录每段移动，用于对比寻路改动前后的耗时。"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.base.operation.application import application_const
from one_dragon.base.operation.application_run_record import (
    AppRunRecord,
    AppRunRecordPeriod,
)
from one_dragon.base.operation.operation import Operation
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import os_utils
from zzz_lv.application.devtools.lost_void_navigation import lost_void_navigation_const
from zzz_lv.application.hollow_zero.lost_void import lost_void_const
from zzz_lv.application.hollow_zero.lost_void.context.lost_void_navigation_session import (
    LostVoidNavigationSession,
    RunOutcome,
)
from zzz_lv.application.hollow_zero.lost_void.lost_void_app import LostVoidApp
from zzz_lv.application.hollow_zero.lost_void.lost_void_run_record import (
    LostVoidRunRecord,
)
from zzz_lv.application.hollow_zero.lost_void.operation.lost_void_run_level import (
    LostVoidRunLevel,
)

if TYPE_CHECKING:
    from zzz_lv.application.hollow_zero.lost_void.lost_void_config import LostVoidConfig
    from zzz_lv.context.zzz_context import ZContext


class NavigationRunRecord(LostVoidRunRecord):
    """只在内存里的运行记录 不读写真实周常进度 周常已完成也照样跑。"""

    def __init__(self, config: LostVoidConfig, instance_idx: int) -> None:
        YamlConfig.__init__(self, lost_void_navigation_const.APP_ID, instance_idx=instance_idx, is_mock=True)
        self.app_id: str = lost_void_navigation_const.APP_ID
        self.config: LostVoidConfig = config
        self.game_refresh_hour_offset: int = 0
        self.record_period: AppRunRecordPeriod = AppRunRecordPeriod.WEEKLY
        self.dt: str = self.get_current_dt()
        self.run_time: str = '-'
        self.run_time_float: float = 0
        self.run_status: int = AppRunRecord.STATUS_WAIT

    @property
    def is_finished(self) -> bool:
        return False


class LostVoidNavigationApp(LostVoidApp):
    """
    沿用迷失之地应用的配置、队伍和副本 只跑一局
    采样写到 .debug/lost_void_navigation/runs/<run_id>/
    """

    def __init__(self, ctx: ZContext) -> None:
        config: LostVoidConfig = ctx.run_context.get_config(
            app_id=lost_void_const.APP_ID,
            instance_idx=ctx.current_instance_idx,
            group_id=application_const.DEFAULT_GROUP_ID,
        )
        super().__init__(ctx, run_record=NavigationRunRecord(config, ctx.current_instance_idx))
        self.app_id = lost_void_navigation_const.APP_ID
        self.op_name = lost_void_navigation_const.APP_NAME
        self._normal_finished: bool = False  # 是否正常通关回到入口

    def execute(self) -> OperationResult:
        """装上本局采样会话 结束或异常时都写终态并卸下。"""
        session = LostVoidNavigationSession(Path(os_utils.get_path_under_work_dir('.debug', 'lost_void_navigation')))
        self.ctx.lost_void.navigation_session = session
        outcome: RunOutcome = 'interrupted'
        # 画面定义沿用迷失之地应用的范围 本应用没有自己的画面
        self.ctx.screen_loader.enter_scope(lost_void_const.APP_ID)
        try:
            result = Operation.execute(self)
            if not self.ctx.run_context.is_context_stop:
                outcome = 'normal' if result.success and self._normal_finished and not session.level_failed else 'failed'
            return result
        finally:
            self.ctx.screen_loader.exit_scope()
            self.ctx.auto_battle_context.stop_auto_battle()
            self.ctx.controller.stop_moving_forward()
            session.finish(outcome)
            self.ctx.lost_void.navigation_session = None

    @node_from(from_name='前往迷失之地-入口')
    @operation_node(name='识别悬赏委托完成进度')
    def check_bounty_commission_before(self) -> OperationRoundResult:
        """不看悬赏进度 直接开始一局。"""
        if self.config.effective_mission_name == '矩阵行动':
            return self.round_success(self.STATUS_AGAIN_MATRIX)
        return self.round_success(self.STATUS_AGAIN)

    @node_from(from_name='层间移动', status=LostVoidRunLevel.STATUS_COMPLETE)
    @operation_node(name='通关后处理')
    def after_complete(self) -> OperationRoundResult:
        """回到入口就结束 不进入下一局。"""
        result = self._wait_for_lost_void_entry()
        if result.is_success:
            self._normal_finished = True
            return self.round_success('寻路采样本局结束')
        return result
