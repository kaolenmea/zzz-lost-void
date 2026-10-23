from qfluentwidgets import FluentIcon

from one_dragon_qt.widgets.pivot_navi_interface import PivotNavigatorInterface
from zzz_lv.context.zzz_context import ZContext
from zzz_lv.gui.view.hollow_zero.lost_void_run_interface import LostVoidRunInterface


class LostVoidInterface(PivotNavigatorInterface):
    """
    迷失之地主界面 只有运行页（含常用配置） 挑战配置随刷取目标自动切换
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
        self.run_interface: LostVoidRunInterface = LostVoidRunInterface(self.ctx)
        self.add_sub_interface(self.run_interface)

    def start_running(self) -> None:
        """
        切到运行页并开始运行 给主页的开始按钮使用
        """
        self.stacked_widget.setCurrentWidget(self.run_interface)
        self.run_interface.run_app()
