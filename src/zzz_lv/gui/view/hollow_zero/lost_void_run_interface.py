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
from one_dragon_qt.widgets.setting_card.spin_box_setting_card import (
    SpinBoxSettingCard,
)
from one_dragon_qt.widgets.setting_card.switch_setting_card import SwitchSettingCard
from zzz_lv.application.hollow_zero.lost_void import lost_void_const
from zzz_lv.application.hollow_zero.lost_void.lost_void_config import (
    AETHER_ACTIVITY_MAX,
    PLAN_RUN_TIMES_MAX,
    PLAN_RUN_TIMES_MIN,
    LostVoidAetherActivityModeEnum,
    LostVoidConfig,
    LostVoidDifficultyEnum,
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

    MAX_TEAM_NO: int = 20  # 与本地预备编队记录的数量一致

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

        self.task_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.FLAG,
            title='刷取目标',
            content='挑战配置随目标自动切换',
            options_enum=LostVoidTaskEnum,
        )
        self.task_type_opt.value_changed.connect(self._update_run_record_display)
        self.task_type_opt.value_changed.connect(self._update_aether_enabled)
        task_group.addSettingCard(self.task_type_opt)

        self.difficulty_opt = ComboBoxSettingCard(
            icon=FluentIcon.SPEED_HIGH, title='难度',
            content='仅「获取大部分菲林奖励」生效；难度越高越难，难度六需要游戏里已解锁',
            options_enum=LostVoidDifficultyEnum,
        )
        task_group.addSettingCard(self.difficulty_opt)

        self.plan_run_times_opt = SpinBoxSettingCard(
            icon=FluentIcon.SYNC, title='计划刷取次数',
            content='通关达到这个次数后停止，下次启动重新计数',
            minimum=PLAN_RUN_TIMES_MIN, maximum=PLAN_RUN_TIMES_MAX,
        )
        self.plan_run_times_opt.value_changed.connect(self._on_plan_run_times_changed)
        task_group.addSettingCard(self.plan_run_times_opt)

        self.aether_mode_opt = ComboBoxSettingCard(
            icon=FluentIcon.SPEED_HIGH, title='活性增幅',
            content='仅「获取大部分菲林奖励」生效；活性越高敌人越强，不熟悉请保持「不选」',
            options_enum=LostVoidAetherActivityModeEnum,
        )
        self.aether_mode_opt.value_changed.connect(self._update_aether_target_enabled)
        task_group.addSettingCard(self.aether_mode_opt)

        self.aether_target_opt = SpinBoxSettingCard(
            icon=FluentIcon.UP, title='活性点数',
            content='「指定点数」时选到这个点数为止，未解锁的增幅不能选',
            minimum=1, maximum=AETHER_ACTIVITY_MAX,
        )
        task_group.addSettingCard(self.aether_target_opt)

        self.run_record_opt = PushSettingCard(icon=FluentIcon.HISTORY, title='运行记录', text=gt('重置记录'))
        self.run_record_opt.clicked.connect(self._on_reset_record_clicked)
        task_group.addSettingCard(self.run_record_opt)

        team_group = SettingCardGroup(gt('预备编队'))
        left.add_widget(team_group)

        team_no_opts = [ConfigItem('不选择', value=0, desc='沿用游戏当前编队')] + [
            ConfigItem(f'编队{i}', value=i) for i in range(1, LostVoidRunInterface.MAX_TEAM_NO + 1)
        ]
        self.team_no_opt = ComboBoxSettingCard(
            icon=FluentIcon.PEOPLE,
            title='预备编队',
            content='战线肃清、特遣调查出战前选择游戏里的「编队 N」',
            options_list=team_no_opts,
        )
        team_group.addSettingCard(self.team_no_opt)

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

        self.depth_avoid_opt = SwitchSettingCard(
            icon=FluentIcon.MOVE, title='深度避障',
            content='需要放置深度模型；寻路时提前绕开障碍物，效果不好可关闭，回到撞墙后再脱困',
        )
        run_group.addSettingCard(self.depth_avoid_opt)

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
        self.mission_opt.init_with_adapter(get_prop_adapter(self.config, 'effective_mission_name'))
        self.task_type_opt.init_with_adapter(get_prop_adapter(self.config, 'extra_task'))
        self.team_no_opt.init_with_adapter(get_prop_adapter(self.config, 'predefined_team_no'))
        self.difficulty_opt.init_with_adapter(get_prop_adapter(self.config, 'polychrome_difficulty'))
        self.plan_run_times_opt.init_with_adapter(get_prop_adapter(self.config, 'plan_run_times'))
        self.aether_mode_opt.init_with_adapter(get_prop_adapter(self.config, 'aether_activity_mode'))
        self.aether_target_opt.init_with_adapter(get_prop_adapter(self.config, 'aether_activity_target'))
        self._update_aether_enabled()
        self._update_advanced_visibility()
        self.depth_avoid_opt.init_with_adapter(get_prop_adapter(self.config, 'depth_avoid_enabled'))
        self._update_run_record_display()

        self.after_done_opt.blockSignals(True)
        self.after_done_opt.setValue(self.ctx.one_dragon_config.after_done)
        self.after_done_opt.blockSignals(False)

    def _update_advanced_visibility(self) -> None:
        """没开高级设置时只显示常用项 副本跟随刷取目标 深度避障用默认值"""
        advanced = self.ctx.env_config.advanced_mode
        self.mission_opt.setVisible(advanced)
        self.depth_avoid_opt.setVisible(advanced)

    def _update_aether_enabled(self) -> None:
        """难度和活性增幅只在菲林目标生效 点数只在「指定点数」时有用"""
        self.difficulty_opt.setEnabled(self.config.is_polychrome_mode)
        self.aether_mode_opt.setEnabled(self.config.is_polychrome_mode)
        self._update_aether_target_enabled()

    def _update_aether_target_enabled(self) -> None:
        is_target = self.config.aether_activity_mode == LostVoidAetherActivityModeEnum.TARGET.value.value
        self.aether_target_opt.setEnabled(self.config.is_polychrome_mode and is_target)

    def _on_plan_run_times_changed(self) -> None:
        """改了计划次数 重新开始计数"""
        self.run_record.plan_done_times = 0
        self._update_run_record_display()

    def _update_mission_options(self) -> None:
        self.mission_opt.blockSignals(True)
        mission_list: list[str] = self.ctx.compendium_service.get_lost_void_mission_name_list()
        self.mission_opt.set_options_by_list([ConfigItem(mission_name) for mission_name in mission_list])
        self.mission_opt.blockSignals(False)

    def _update_run_record_display(self) -> None:
        """刷新当前目标的副本和运行状态。"""
        self.mission_opt.setValue(self.config.effective_mission_name, emit_signal=False)
        self.mission_opt.setEnabled(not self.config.is_polychrome_mode)
        self.mission_opt.setContent('随「获取大部分菲林奖励」目标自动选择战线肃清' if self.config.is_polychrome_mode else '')
        if self.config.is_polychrome_mode and self.run_record.polychrome_notice:
            content = self.run_record.polychrome_notice
        elif self.run_record.is_finished:
            content = f'本周已完成「{self.config.extra_task}」 如错误可重置'
        else:
            content = f'本周通关次数: {self.run_record.weekly_run_times}'
        content += f'；本轮已刷 {self.run_record.plan_done_times} / 计划 {self.config.plan_run_times} 次'
        self.run_record_opt.setContent(content)

    def _on_reset_record_clicked(self) -> None:
        self.run_record.reset_record()
        self.run_record.reset_for_weekly()
        self.run_record.polychrome_notice = ''
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
