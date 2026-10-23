from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    FluentIcon,
    IconWidget,
    InfoBarIcon,
    PrimaryPushButton,
    PushButton,
    SimpleCardWidget,
    StrongBodyLabel,
    SubtitleLabel,
    TitleLabel,
    TransparentPushButton,
)

from one_dragon.base.operation.application import application_const
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface
from zzz_lv.application.hollow_zero.lost_void import lost_void_const
from zzz_lv.context.zzz_context import ZContext
from zzz_lv.gui.dialog.pre_flight_check_dialog import (
    PreFlightCheckDialog,
    check_pre_flight,
)

if TYPE_CHECKING:
    from zzz_lv.application.hollow_zero.lost_void.lost_void_config import (
        LostVoidConfig,
    )
    from zzz_lv.application.hollow_zero.lost_void.lost_void_run_record import (
        LostVoidRunRecord,
    )

# 卡片内边距与间距
_CARD_MARGIN = 20
_CARD_SPACING = 12

# 次要文字颜色（浅色主题, 深色主题）
_SECONDARY_TEXT_COLOR = ('#606060', '#a0a0a0')


class InfoGrid(QWidget):
    """
    两列的「名称 - 值」信息表 名称用次要文字色
    """

    def __init__(self, keys: list[str], parent: QWidget | None = None) -> None:
        QWidget.__init__(self, parent=parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(24)
        layout.setVerticalSpacing(8)
        layout.setColumnStretch(1, 1)

        self._value_labels: dict[str, BodyLabel] = {}
        for row, key in enumerate(keys):
            key_label = CaptionLabel(gt(key))
            key_label.setTextColor(*_SECONDARY_TEXT_COLOR)
            value_label = BodyLabel('-')
            value_label.setWordWrap(True)
            layout.addWidget(key_label, row, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(value_label, row, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._value_labels[key] = value_label

    def set_value(self, key: str, value: str) -> None:
        self._value_labels[key].setText(value)


class FeatureCard(SimpleCardWidget):
    """
    功能卡片 标题 + 说明 + 当前配置信息 + 底部操作按钮
    """

    def __init__(self, icon: FluentIcon, title: str, description: str, info_keys: list[str],
                 parent: QWidget | None = None) -> None:
        SimpleCardWidget.__init__(self, parent=parent)
        self.setBorderRadius(8)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(_CARD_MARGIN, _CARD_MARGIN, _CARD_MARGIN, _CARD_MARGIN)
        layout.setSpacing(_CARD_SPACING)

        header = QHBoxLayout()
        header.setSpacing(12)
        icon_widget = IconWidget(icon)
        icon_widget.setFixedSize(28, 28)
        header.addWidget(icon_widget, 0, Qt.AlignmentFlag.AlignTop)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.addWidget(SubtitleLabel(gt(title)))
        desc_label = CaptionLabel(gt(description))
        desc_label.setTextColor(*_SECONDARY_TEXT_COLOR)
        desc_label.setWordWrap(True)
        title_col.addWidget(desc_label)
        header.addLayout(title_col, 1)
        layout.addLayout(header)

        layout.addSpacing(4)
        self.info_grid = InfoGrid(info_keys)
        layout.addWidget(self.info_grid)
        layout.addStretch(1)

        self.btn_row = QHBoxLayout()
        self.btn_row.setSpacing(8)
        self.btn_row.addStretch(1)
        layout.addLayout(self.btn_row)

    def add_button(self, btn: QWidget) -> None:
        self.btn_row.addWidget(btn)


class ReadinessCard(SimpleCardWidget):
    """
    运行准备状态 全部就绪时只显示一行 有问题时逐条列出并提供跳转按钮
    """

    def __init__(self, home: HomeInterface, parent: QWidget | None = None) -> None:
        SimpleCardWidget.__init__(self, parent=parent)
        self.setBorderRadius(8)
        self._home: HomeInterface = home

        layout = QVBoxLayout(self)
        layout.setContentsMargins(_CARD_MARGIN, 16, _CARD_MARGIN, 16)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(12)
        self.status_icon = IconWidget(InfoBarIcon.SUCCESS)
        self.status_icon.setFixedSize(20, 20)
        header.addWidget(self.status_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        self.status_title = StrongBodyLabel()
        header.addWidget(self.status_title, 0, Qt.AlignmentFlag.AlignVCenter)
        self.status_desc = CaptionLabel()
        self.status_desc.setTextColor(*_SECONDARY_TEXT_COLOR)
        header.addWidget(self.status_desc, 1, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(header)

        # 问题列表 每次刷新重建
        self.issue_widget = QWidget()
        self.issue_layout = QVBoxLayout(self.issue_widget)
        self.issue_layout.setContentsMargins(32, 0, 0, 0)
        self.issue_layout.setSpacing(4)
        layout.addWidget(self.issue_widget)

    def update_issues(self, issues: list[tuple[str, str, str | None]]) -> None:
        while self.issue_layout.count():
            item = self.issue_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

        if not issues:
            self.status_icon.setIcon(InfoBarIcon.SUCCESS)
            self.status_title.setText(gt('准备就绪'))
            self.status_desc.setText(gt('游戏路径和识别模型都已配置'))
            self.issue_widget.setVisible(False)
            return

        self.status_icon.setIcon(InfoBarIcon.WARNING)
        self.status_title.setText(f"{gt('有')} {len(issues)} {gt('项需要处理')}")
        self.status_desc.setText(gt('不处理也可以继续运行，但可能失败'))
        for message, target_name, sub_name in issues:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(BodyLabel(message), 1)
            goto_btn = TransparentPushButton(FluentIcon.RIGHT_ARROW, gt('前往'))
            goto_btn.clicked.connect(
                lambda _checked=False, t=target_name, s=sub_name: self._home.goto_interface(t, s)
            )
            row_layout.addWidget(goto_btn)
            self.issue_layout.addWidget(row)
        self.issue_widget.setVisible(True)


class HomeInterface(VerticalScrollInterface):
    """
    主页 显示运行准备状态、两个功能的当前配置和入口
    """

    def __init__(self, ctx: ZContext, parent=None) -> None:
        self.ctx: ZContext = ctx
        self.main_window = parent
        VerticalScrollInterface.__init__(
            self,
            content_widget=None,
            object_name='home_interface',
            nav_text_cn='主页',
            nav_icon=FluentIcon.HOME,
            parent=parent,
        )
        self._ready_signal_connected: bool = False

    def get_content_widget(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 16, 24, 0)
        layout.setSpacing(16)

        layout.addLayout(self._init_header())

        self.readiness_card = ReadinessCard(self)
        layout.addWidget(self.readiness_card)

        card_row = QHBoxLayout()
        card_row.setSpacing(16)
        card_row.addWidget(self._init_lost_void_card(), 1)
        card_row.addWidget(self._init_battle_assistant_card(), 1)
        layout.addLayout(card_row)

        self.hotkey_label = CaptionLabel()
        self.hotkey_label.setTextColor(*_SECONDARY_TEXT_COLOR)
        layout.addWidget(self.hotkey_label)

        layout.addStretch(1)
        return content

    def _init_header(self) -> QHBoxLayout:
        header = QHBoxLayout()

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title_col.addWidget(TitleLabel(gt(self.ctx.project_config.project_name)))
        subtitle = BodyLabel(gt('绝区零 迷失之地与战斗助手自动化'))
        subtitle.setTextColor(*_SECONDARY_TEXT_COLOR)
        title_col.addWidget(subtitle)
        header.addLayout(title_col, 1)

        github_btn = TransparentPushButton(FluentIcon.GITHUB, 'GitHub')
        github_btn.clicked.connect(self._on_github_clicked)
        header.addWidget(github_btn, 0, Qt.AlignmentFlag.AlignTop)

        return header

    def _init_lost_void_card(self) -> FeatureCard:
        self.lost_void_card = FeatureCard(
            icon=FluentIcon.GAME,
            title='迷失之地',
            description='自动进入迷失之地，完成选队、移动、选鸣徽与战斗',
            info_keys=['挑战副本', '挑战配置', '刷取目标', '通关次数'],
        )

        self.lost_void_setting_btn = PushButton(FluentIcon.SETTING, gt('配置'))
        self.lost_void_setting_btn.clicked.connect(self._on_lost_void_setting_clicked)
        self.lost_void_card.add_button(self.lost_void_setting_btn)

        self.lost_void_start_btn = PrimaryPushButton(FluentIcon.PLAY, gt('开始运行'))
        self.lost_void_start_btn.clicked.connect(self._on_lost_void_start_clicked)
        self.lost_void_card.add_button(self.lost_void_start_btn)

        return self.lost_void_card

    def _init_battle_assistant_card(self) -> FeatureCard:
        self.battle_card = FeatureCard(
            icon=FluentIcon.ROBOT,
            title='战斗助手',
            description='手动游玩时使用：自动战斗，或只在敌人攻击时自动闪避',
            info_keys=['战斗配置', '闪避方式', '后台模式'],
        )

        self.battle_open_btn = PrimaryPushButton(FluentIcon.RIGHT_ARROW, gt('打开战斗助手'))
        self.battle_open_btn.clicked.connect(self._on_battle_open_clicked)
        self.battle_card.add_button(self.battle_open_btn)

        return self.battle_card

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        check_resource_updates = getattr(self.main_window, 'check_resource_updates', None)
        if callable(check_resource_updates):
            check_resource_updates()

        # 启动时 ctx 还在后台初始化 初始化完成后再刷新一次
        if not self._ready_signal_connected and self.main_window is not None:
            self.main_window.app_setting_manager.ready.connect(self._refresh_display)
            self._ready_signal_connected = True

        self._refresh_display()

    def _refresh_display(self) -> None:
        if not self._init:
            return
        self.readiness_card.update_issues(check_pre_flight(self.ctx))
        self._refresh_lost_void_card()
        self._refresh_battle_card()
        self.hotkey_label.setText(
            f"{gt('快捷键')}  {gt('开始/暂停')} {self.ctx.key_start_running.upper()}"
            f"  ·  {gt('停止')} {self.ctx.key_stop_running.upper()}"
            f"  ·  {gt('可在「设置 → 脚本环境」中修改')}"
        )

    def _refresh_lost_void_card(self) -> None:
        grid = self.lost_void_card.info_grid
        if not self.ctx.ready_for_application:
            for key in ['挑战副本', '挑战配置', '刷取目标', '通关次数']:
                grid.set_value(key, gt('加载中…'))
            self.lost_void_start_btn.setEnabled(False)
            return

        try:
            config: LostVoidConfig = self.ctx.run_context.get_config(
                app_id=lost_void_const.APP_ID,
                instance_idx=self.ctx.current_instance_idx,
                group_id=application_const.DEFAULT_GROUP_ID,
            )
            record: LostVoidRunRecord = self.ctx.run_context.get_run_record(
                app_id=lost_void_const.APP_ID,
                instance_idx=self.ctx.current_instance_idx,
            )
        except Exception:
            log.error('读取迷失之地配置失败', exc_info=True)
            return

        grid.set_value('挑战副本', config.effective_mission_name)
        grid.set_value('挑战配置', config.challenge_config)
        grid.set_value('刷取目标', config.extra_task)
        grid.set_value(
            '通关次数',
            f"{gt('本周')} {record.weekly_run_times}（{gt('本轮')} {record.plan_done_times}/{config.plan_run_times}）",
        )

        self.lost_void_start_btn.setEnabled(True)
        if self.ctx.run_context.is_context_stop:
            self.lost_void_start_btn.setText(gt('开始运行'))
            self.lost_void_start_btn.setIcon(FluentIcon.PLAY)
        else:
            self.lost_void_start_btn.setText(gt('查看运行'))
            self.lost_void_start_btn.setIcon(FluentIcon.RIGHT_ARROW)

    def _refresh_battle_card(self) -> None:
        config = self.ctx.battle_assistant_config
        grid = self.battle_card.info_grid
        grid.set_value('战斗配置', config.auto_battle_config)
        grid.set_value('闪避方式', config.dodge_assistant_config)
        grid.set_value('后台模式', gt('开启') if config.background_mode else gt('关闭'))

    def _on_lost_void_start_clicked(self) -> None:
        lost_void_interface = self.main_window.lost_void_interface
        if not self.ctx.run_context.is_context_stop:
            # 已在运行 只跳过去看日志
            self.main_window.switchTo(lost_void_interface)
            return

        issues = check_pre_flight(self.ctx)
        if issues:
            dialog = PreFlightCheckDialog([msg for msg, _, _ in issues], self.window())
            if dialog.exec():
                _, target_name, sub_name = issues[0]
                self.goto_interface(target_name, sub_name)
                return

        self.main_window.switchTo(lost_void_interface)
        lost_void_interface.start_running()

    def _on_lost_void_setting_clicked(self) -> None:
        self.main_window.switchTo(self.main_window.lost_void_interface)

    def _on_battle_open_clicked(self) -> None:
        self.main_window.switchTo(self.main_window.battle_assistant_interface)

    def _on_github_clicked(self) -> None:
        QDesktopServices.openUrl(QUrl(self.ctx.project_config.github_homepage))

    def goto_interface(self, target_name: str, sub_name: str | None) -> None:
        """
        跳到指定导航页 有子页面时再切到对应 tab
        """
        target = self._find_widget(self.main_window.stackedWidget, target_name)
        if target is None:
            return
        self.main_window.switchTo(target)
        if sub_name is not None and hasattr(target, 'stacked_widget'):
            sub = self._find_widget(target.stacked_widget, sub_name)
            if sub is not None:
                target.stacked_widget.setCurrentWidget(sub)

    @staticmethod
    def _find_widget(stacked: QStackedWidget, name: str) -> QWidget | None:
        for i in range(stacked.count()):
            w = stacked.widget(i)
            if w.objectName() == name:
                return w
        return None
