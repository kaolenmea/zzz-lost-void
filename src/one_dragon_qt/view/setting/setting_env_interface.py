from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import (
    FluentIcon,
    SettingCardGroup,
    VBoxLayout,
)

from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.envs.env_config import ScreenshotMethodEnum
from one_dragon.utils.i18_utils import gt
from one_dragon_qt.widgets.setting_card.combo_box_setting_card import (
    ComboBoxSettingCard,
)
from one_dragon_qt.widgets.setting_card.help_card import HelpCard
from one_dragon_qt.widgets.setting_card.key_setting_card import KeySettingCard
from one_dragon_qt.widgets.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface


class SettingEnvInterface(VerticalScrollInterface):
    """
    脚本环境设置 网络代理统一在「资源管理」页设置
    """

    def __init__(self, ctx: OneDragonContext, parent=None):
        self.ctx: OneDragonContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='setting_env_interface',
            content_widget=None, parent=parent,
            nav_text_cn='脚本环境'
        )

    def get_content_widget(self) -> QWidget:
        content_widget = QWidget()
        content_layout = VBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.help_opt = HelpCard(
            title='设置说明',
            content='不清楚用途时建议保持默认，无法截图时再调整截图方法；下载代理在「资源管理」中设置',
        )
        content_layout.addWidget(self.help_opt)
        content_layout.addWidget(self._init_basic_group())
        content_layout.addWidget(self._init_key_group())

        return content_widget

    def _init_basic_group(self) -> SettingCardGroup:
        basic_group = SettingCardGroup(gt('基础'))

        self.screenshot_method_opt = ComboBoxSettingCard(
            icon=FluentIcon.CAMERA, title='截图方法',
            options_enum=ScreenshotMethodEnum
        )
        self.screenshot_method_opt.value_changed.connect(lambda: self.ctx.init_controller())
        basic_group.addSettingCard(self.screenshot_method_opt)

        self.debug_opt = SwitchSettingCard(
            icon=FluentIcon.SEARCH, title='调试模式', content='正常无需开启'
        )
        self.debug_opt.value_changed.connect(lambda: self.ctx.init_async())
        basic_group.addSettingCard(self.debug_opt)

        self.advanced_mode_opt = SwitchSettingCard(
            icon=FluentIcon.SETTING,
            title='显示高级设置',
            content='关闭后只显示常用设置，其余用默认值；已有配置不会改变',
        )
        self.advanced_mode_opt.value_changed.connect(self._on_advanced_mode_changed)
        basic_group.addSettingCard(self.advanced_mode_opt)

        self.developer_mode_opt = SwitchSettingCard(
            icon=FluentIcon.DEVELOPER_TOOLS,
            title='开发者模式',
            content='关闭后隐藏开发工具和实验功能，已有配置不会改变',
        )
        self.developer_mode_opt.value_changed.connect(self._on_developer_mode_changed)
        basic_group.addSettingCard(self.developer_mode_opt)

        self.copy_screenshot_opt = SwitchSettingCard(
            icon=FluentIcon.CAMERA, title='复制截图到剪贴板',
            content='按下截图按键时，自动将截图复制到剪贴板'
        )
        basic_group.addSettingCard(self.copy_screenshot_opt)

        return basic_group

    def _init_key_group(self) -> SettingCardGroup:
        key_group = SettingCardGroup(gt('脚本按键'))

        self.key_start_running_input = KeySettingCard(
            icon=FluentIcon.PLAY, title='开始运行', content='开始、暂停、恢复某个应用',
        )
        key_group.addSettingCard(self.key_start_running_input)

        self.key_stop_running_input = KeySettingCard(
            icon=FluentIcon.CLOSE, title='停止运行', content='停止正在运行的应用，不能恢复'
        )
        key_group.addSettingCard(self.key_stop_running_input)

        self.key_screenshot_input = KeySettingCard(
            icon=FluentIcon.CAMERA, title='游戏截图', content='用于开发、提交bug。会自动对UID打码，保存在 .debug/images/ 文件夹中'
        )
        key_group.addSettingCard(self.key_screenshot_input)

        self.key_debug_input = KeySettingCard(
            icon=FluentIcon.MOVE, title='调试按钮', content='用于开发，部分应用开始调试'
        )
        key_group.addSettingCard(self.key_debug_input)

        return key_group

    def on_interface_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        VerticalScrollInterface.on_interface_shown(self)

        self.screenshot_method_opt.init_with_adapter(self.ctx.env_config.get_prop_adapter('screenshot_method'))
        self.debug_opt.init_with_adapter(self.ctx.env_config.get_prop_adapter('is_debug'))
        self.advanced_mode_opt.init_with_adapter(
            self.ctx.env_config.get_prop_adapter('advanced_mode')
        )
        self.developer_mode_opt.init_with_adapter(
            self.ctx.env_config.get_prop_adapter('developer_mode')
        )
        self.copy_screenshot_opt.init_with_adapter(self.ctx.env_config.get_prop_adapter('copy_screenshot'))

        self.key_start_running_input.init_with_adapter(self.ctx.env_config.get_prop_adapter('key_start_running'))
        self.key_stop_running_input.init_with_adapter(self.ctx.env_config.get_prop_adapter('key_stop_running'))
        self.key_screenshot_input.init_with_adapter(self.ctx.env_config.get_prop_adapter('key_screenshot'))
        self.key_debug_input.init_with_adapter(self.ctx.env_config.get_prop_adapter('key_debug'))
        self._apply_developer_visibility(self.ctx.env_config.developer_mode)

    def _on_advanced_mode_changed(self, value: bool) -> None:
        """通知主窗口更新高级设置可见性。"""
        window = self.window()
        if hasattr(window, 'set_advanced_mode'):
            window.set_advanced_mode(value)

    def _on_developer_mode_changed(self, value: bool) -> None:
        """通知主窗口更新开发者功能可见性。"""
        window = self.window()
        if hasattr(window, 'set_developer_mode'):
            window.set_developer_mode(value)
        self._apply_developer_visibility(value)

    def _apply_developer_visibility(self, developer_mode: bool) -> None:
        """调试模式、截图相关、调试键只在开发者模式下显示"""
        self.debug_opt.setVisible(developer_mode)
        self.key_screenshot_input.setVisible(developer_mode)
        self.key_debug_input.setVisible(developer_mode)
        self.copy_screenshot_opt.setVisible(developer_mode)
