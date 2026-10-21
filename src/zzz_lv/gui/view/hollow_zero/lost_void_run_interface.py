from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, PushSettingCard, SettingCardGroup

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.one_dragon_config import AfterDoneOpEnum
from one_dragon.base.operation.application import application_const
from one_dragon.base.operation.one_dragon_finalizer import (
    AfterDoneRequest,
    execute_after_done,
)
from one_dragon.utils import cmd_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from one_dragon_qt.utils.config_utils import get_prop_adapter
from one_dragon_qt.view.app_run_interface import SplitAppRunInterface
from one_dragon_qt.widgets.column import Column
from one_dragon_qt.widgets.setting_card.combo_box_setting_card import (
    ComboBoxSettingCard,
)
from one_dragon_qt.widgets.setting_card.spin_box_setting_card import SpinBoxSettingCard
from zzz_lv.application.hollow_zero.lost_void import lost_void_const
from zzz_lv.application.hollow_zero.lost_void.lost_void_challenge_config import (
    LostVoidChallengeConfig,
    get_all_lost_void_challenge_config,
)
from zzz_lv.application.hollow_zero.lost_void.lost_void_config import (
    LostVoidConfig,
    LostVoidTaskEnum,
)
from zzz_lv.application.hollow_zero.lost_void.lost_void_run_record import (
    LostVoidRunRecord,
)

if TYPE_CHECKING:
    from zzz_lv.context.zzz_context import ZContext


class LostVoidRunInterface(SplitAppRunInterface):
    """
    迷失之地运行页 左侧放常用配置 右侧放开始/停止和日志
    """

    def __init__(self, ctx: ZContext, parent: QWidget | None = None) -> None:
        self.ctx: ZContext = ctx
        self._runner_finished_connected: bool = False
        SplitAppRunInterface.__init__(
            self,
            ctx=ctx,
            app_id=lost_void_const.APP_ID,
            object_name='lost_void_run_interface',
            nav_text_cn='运行',
            parent=parent,
        )

    def get_left_widget(self) -> QWidget:
        left = Column()

        task_group = SettingCardGroup(gt('刷取设置'))
        left.add_widget(task_group)

        self.mission_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='挑战副本')
        task_group.addSettingCard(self.mission_opt)

        self.challenge_config_opt = ComboBoxSettingCard(
            icon=FluentIcon.PEOPLE,
            title='挑战配置',
            content='配队、鸣徽和藏品选择，可在「挑战配置」页修改',
        )
        task_group.addSettingCard(self.challenge_config_opt)

        self.task_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.FLAG,
            title='刷取目标',
            options_enum=LostVoidTaskEnum,
        )
        self.task_type_opt.value_changed.connect(self._update_run_record_display)
        task_group.addSettingCard(self.task_type_opt)

        self.daily_plan_times_opt = SpinBoxSettingCard(
            icon=FluentIcon.CALENDAR,
            title='每天进入次数',
            content='分摊到每天运行',
        )
        task_group.addSettingCard(self.daily_plan_times_opt)

        self.weekly_plan_times_opt = SpinBoxSettingCard(icon=FluentIcon.CALENDAR, title='每周进入次数')
        self.weekly_plan_times_opt.setVisible(False)
        task_group.addSettingCard(self.weekly_plan_times_opt)

        self.run_record_opt = PushSettingCard(icon=FluentIcon.HISTORY, title='运行记录', text=gt('重置记录'))
        self.run_record_opt.clicked.connect(self._on_reset_record_clicked)
        task_group.addSettingCard(self.run_record_opt)

        run_group = SettingCardGroup(gt('运行设置'))
        left.add_widget(run_group)

        self.after_done_opt = ComboBoxSettingCard(
            icon=FluentIcon.POWER_BUTTON,
            title='结束后',
            content='正常跑完后执行；未打开游戏时会按设置里的游戏路径自动启动',
            options_enum=AfterDoneOpEnum,
        )
        self.after_done_opt.value_changed.connect(self._on_after_done_changed)
        run_group.addSettingCard(self.after_done_opt)

        left.add_stretch(1)
        return left

    def on_interface_shown(self) -> None:
        SplitAppRunInterface.on_interface_shown(self)
        if not self._runner_finished_connected:
            self.app_runner.finished.connect(self._on_app_runner_finished)
            self._runner_finished_connected = True

        self.config: LostVoidConfig = self.ctx.run_context.get_config(
            app_id=lost_void_const.APP_ID,
            instance_idx=self.ctx.current_instance_idx,
            group_id=application_const.DEFAULT_GROUP_ID,
        )
        self.run_record: LostVoidRunRecord = self.ctx.run_context.get_run_record(
            instance_idx=self.ctx.current_instance_idx,
            app_id=lost_void_const.APP_ID,
        )

        self._update_mission_options()
        self._update_challenge_config_options()
        self.mission_opt.init_with_adapter(get_prop_adapter(self.config, 'mission_name'))
        self.challenge_config_opt.init_with_adapter(get_prop_adapter(self.config, 'challenge_config'))
        self.task_type_opt.init_with_adapter(get_prop_adapter(self.config, 'extra_task'))
        self.daily_plan_times_opt.init_with_adapter(get_prop_adapter(self.config, 'daily_plan_times'))
        self.weekly_plan_times_opt.init_with_adapter(get_prop_adapter(self.config, 'weekly_plan_times'))
        self._update_run_record_display()

        self.after_done_opt.blockSignals(True)
        self.after_done_opt.setValue(self.ctx.one_dragon_config.after_done)
        self.after_done_opt.blockSignals(False)

    def _update_mission_options(self) -> None:
        self.mission_opt.blockSignals(True)
        mission_list: list[str] = self.ctx.compendium_service.get_lost_void_mission_name_list()
        self.mission_opt.set_options_by_list([ConfigItem(mission_name) for mission_name in mission_list])
        self.mission_opt.blockSignals(False)

    def _update_challenge_config_options(self) -> None:
        config_list: list[LostVoidChallengeConfig] = get_all_lost_void_challenge_config()
        self.challenge_config_opt.set_options_by_list([
            ConfigItem(config.module_name, config.module_name)
            for config in config_list
        ])

    def _update_run_record_display(self) -> None:
        if self.run_record.bounty_commission_complete:
            content = '已完成悬赏委托 如错误可重置'
        elif self.run_record.period_reward_complete:
            content = '已完成刷取周期奖励 如错误可重置'
        elif self.run_record.eval_point_complete:
            content = '已完成刷取业绩 如错误可重置'
        else:
            content = f'通关次数 本日: {self.run_record.daily_run_times}, 本周: {self.run_record.weekly_run_times}'
        self.run_record_opt.setContent(content)
        self.weekly_plan_times_opt.setVisible(self.config.extra_task == LostVoidTaskEnum.WEEKLY_PLAN_TIMES.value.value)

    def _on_reset_record_clicked(self) -> None:
        self.run_record.reset_record()
        self.run_record.reset_for_weekly()
        log.info('重置成功')
        self._update_run_record_display()

    def _on_after_done_changed(self, idx: int, value: str) -> None:
        self.ctx.one_dragon_config.after_done = value
        if value != AfterDoneOpEnum.SHUTDOWN.value.value:
            cmd_utils.cancel_shutdown_sys()

    def _on_app_runner_finished(self) -> None:
        # 运行结束后刷新通关次数
        self._update_run_record_display()

        after_done = self.ctx.one_dragon_config.after_done
        if after_done == AfterDoneOpEnum.NONE.value.value:
            return
        execute_after_done(
            self.ctx,
            self.app_runner.run_result,
            AfterDoneRequest(
                close_game=after_done == AfterDoneOpEnum.CLOSE_GAME.value.value,
                shutdown_seconds=(
                    60 if after_done == AfterDoneOpEnum.SHUTDOWN.value.value else None
                ),
                hibernate=after_done == AfterDoneOpEnum.HIBERNATE.value.value,
                sleep=after_done == AfterDoneOpEnum.SLEEP.value.value,
            ),
        )
