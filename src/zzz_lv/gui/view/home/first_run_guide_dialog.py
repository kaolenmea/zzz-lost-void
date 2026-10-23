from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget
from qfluentwidgets import BodyLabel, FluentIcon, MessageBoxBase, SubtitleLabel

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.operation.application import application_const
from one_dragon.utils.i18_utils import gt
from one_dragon_qt.utils.config_utils import get_prop_adapter
from one_dragon_qt.widgets.setting_card.combo_box_setting_card import (
    ComboBoxSettingCard,
)
from one_dragon_qt.widgets.setting_card.spin_box_setting_card import (
    SpinBoxSettingCard,
)
from zzz_lv.application.hollow_zero.lost_void import lost_void_const
from zzz_lv.application.hollow_zero.lost_void.lost_void_config import (
    PLAN_RUN_TIMES_MAX,
    PLAN_RUN_TIMES_MIN,
    LostVoidConfig,
    LostVoidTaskEnum,
)

if TYPE_CHECKING:
    from zzz_lv.context.zzz_context import ZContext


class FirstRunGuideDialog(MessageBoxBase):
    """
    发布包第一次运行时的快速设置：只问三件事，其余都用默认值。
    选项直接写进迷失之地配置，之后可以在「迷失之地」页修改。
    """

    MAX_TEAM_NO: int = 20  # 与运行页的预备编队数量一致

    def __init__(self, ctx: ZContext, parent: QWidget | None = None) -> None:
        MessageBoxBase.__init__(self, parent)
        self.ctx: ZContext = ctx
        self.cancelButton.hide()
        self.yesButton.setText(gt('完成'))
        self.widget.setMinimumWidth(560)

        config: LostVoidConfig = ctx.run_context.get_config(
            app_id=lost_void_const.APP_ID,
            instance_idx=ctx.current_instance_idx,
            group_id=application_const.DEFAULT_GROUP_ID,
        )

        self.viewLayout.addWidget(SubtitleLabel(gt('快速设置')))
        tip = BodyLabel(
            gt('开始前请确认：游戏分辨率为 1920×1080（窗口或全屏均可）；设置只问这三项，其余都用推荐值。')
        )
        tip.setWordWrap(True)
        self.viewLayout.addWidget(tip)

        self.task_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.FLAG, title='刷取目标',
            content='推荐「完成悬赏委托」；想刷首通和以太活性奖励选「战线肃清」',
            options_enum=LostVoidTaskEnum,
        )
        self.task_type_opt.init_with_adapter(get_prop_adapter(config, 'extra_task'))
        self.viewLayout.addWidget(self.task_type_opt)

        self.plan_run_times_opt = SpinBoxSettingCard(
            icon=FluentIcon.SYNC, title='计划刷取次数',
            content='通关达到这个次数后自动停止',
            minimum=PLAN_RUN_TIMES_MIN, maximum=PLAN_RUN_TIMES_MAX,
        )
        self.plan_run_times_opt.init_with_adapter(get_prop_adapter(config, 'plan_run_times'))
        self.viewLayout.addWidget(self.plan_run_times_opt)

        team_no_opts = [ConfigItem('不选择', value=0, desc='沿用游戏当前编队')] + [
            ConfigItem(f'编队{i}', value=i) for i in range(1, FirstRunGuideDialog.MAX_TEAM_NO + 1)
        ]
        self.team_no_opt = ComboBoxSettingCard(
            icon=FluentIcon.PEOPLE, title='预备编队',
            content='出战前自动选择游戏里的「编队 N」；不确定就保持「不选择」',
            options_list=team_no_opts,
        )
        self.team_no_opt.init_with_adapter(get_prop_adapter(config, 'predefined_team_no'))
        self.viewLayout.addWidget(self.team_no_opt)
