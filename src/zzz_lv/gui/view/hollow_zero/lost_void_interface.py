from qfluentwidgets import FluentIcon

from one_dragon_qt.view.app_run_interface import AppRunInterface
from one_dragon_qt.widgets.pivot_navi_interface import PivotNavigatorInterface
from zzz_lv.application.hollow_zero.lost_void import lost_void_const
from zzz_lv.context.zzz_context import ZContext
from zzz_lv.gui.view.hollow_zero.lost_void_challenge_config_interface import (
    LostVoidChallengeConfigInterface,
)
from zzz_lv.gui.view.hollow_zero.lost_void_setting_interface import (
    LostVoidSettingInterface,
)
from zzz_lv.gui.view.one_dragon.predefined_team_interface import PredefinedTeamInterface


class LostVoidRunInterface(AppRunInterface):

    def __init__(self, ctx: ZContext, parent=None) -> None:
        self.ctx: ZContext = ctx
        AppRunInterface.__init__(
            self,
            ctx=ctx,
            app_id=lost_void_const.APP_ID,
            object_name='lost_void_run_interface',
            nav_text_cn='运行',
            parent=parent,
        )


class LostVoidInterface(PivotNavigatorInterface):
    """
    迷失之地主界面 集中放运行、配置、挑战配置和预备编队
    """

    def __init__(self, ctx: ZContext, parent=None) -> None:
        self.ctx: ZContext = ctx
        PivotNavigatorInterface.__init__(
            self,
            object_name='lost_void_interface',
            parent=parent,
            nav_text_cn='迷失之地',
            nav_icon=FluentIcon.GAME,
        )

    def create_sub_interface(self) -> None:
        self.add_sub_interface(LostVoidRunInterface(self.ctx))
        self.add_sub_interface(LostVoidSettingInterface(self.ctx))
        self.add_sub_interface(LostVoidChallengeConfigInterface(self.ctx))
        self.add_sub_interface(PredefinedTeamInterface(self.ctx))
