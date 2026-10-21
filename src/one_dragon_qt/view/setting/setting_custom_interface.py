from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget
from qfluentwidgets import (
    ColorDialog,
    Dialog,
    FluentIcon,
    PushButton,
    SettingCardGroup,
    Theme,
    setTheme,
)

from one_dragon.base.config.custom_config import (
    ThemeEnum,
    UILanguageEnum,
)
from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.utils import app_utils
from one_dragon.utils.i18_utils import gt
from one_dragon_qt.services.theme_manager import ThemeManager
from one_dragon_qt.widgets.column import Column
from one_dragon_qt.widgets.setting_card.combo_box_setting_card import (
    ComboBoxSettingCard,
)
from one_dragon_qt.widgets.setting_card.help_card import HelpCard
from one_dragon_qt.widgets.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface

# 未开启自定义主题色时使用的主题色
_DEFAULT_THEME_COLOR: tuple[int, int, int] = (0, 120, 215)


class SettingCustomInterface(VerticalScrollInterface):

    def __init__(self, ctx: OneDragonContext, parent=None):
        self.ctx: OneDragonContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='setting_custom_interface',
            content_widget=None, parent=parent,
            nav_text_cn='自定义设置'
        )

    def get_content_widget(self) -> QWidget:
        content_widget = Column(self)

        self.help_opt = HelpCard(
            title='设置说明',
            content='语言调整后需要重启生效',
        )
        content_widget.add_widget(self.help_opt)
        content_widget.add_widget(self._init_basic_group())
        content_widget.add_stretch(1)

        return content_widget

    def _init_basic_group(self) -> SettingCardGroup:
        basic_group = SettingCardGroup(gt('外观'))

        self.ui_language_opt = ComboBoxSettingCard(
            icon=FluentIcon.LANGUAGE, title='界面语言',
            options_enum=UILanguageEnum
        )
        self.ui_language_opt.value_changed.connect(self._on_ui_language_changed)
        basic_group.addSettingCard(self.ui_language_opt)

        self.theme_opt = ComboBoxSettingCard(
            icon=FluentIcon.CONSTRACT, title='界面主题',
            options_enum=ThemeEnum
        )
        self.theme_opt.value_changed.connect(self._on_theme_changed)
        basic_group.addSettingCard(self.theme_opt)

        # 自定义主题色 关闭时使用默认主题色
        self.theme_color_mode_opt = SwitchSettingCard(
            icon=FluentIcon.PALETTE,
            title='自定义主题色',
            content='关闭时使用默认蓝色',
        )
        self.custom_theme_color_btn = PushButton(icon=FluentIcon.PALETTE, text=gt('选择颜色'))
        self.custom_theme_color_btn.clicked.connect(self._on_custom_theme_color_clicked)
        self.theme_color_mode_opt.hBoxLayout.addWidget(self.custom_theme_color_btn, 0, Qt.AlignmentFlag.AlignRight)
        self.theme_color_mode_opt.hBoxLayout.addSpacing(16)
        self.theme_color_mode_opt.value_changed.connect(self._on_theme_color_mode_changed)
        basic_group.addSettingCard(self.theme_color_mode_opt)

        return basic_group

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)
        self.ui_language_opt.init_with_adapter(self.ctx.custom_config.get_prop_adapter('ui_language'))
        self.theme_opt.init_with_adapter(self.ctx.custom_config.get_prop_adapter('theme'))
        self.theme_color_mode_opt.init_with_adapter(self.ctx.custom_config.get_prop_adapter('custom_theme_color'))
        self.custom_theme_color_btn.setEnabled(self.ctx.custom_config.custom_theme_color)

    def _on_ui_language_changed(self, index: int, value: str) -> None:
        language = self.ctx.custom_config.ui_language
        dialog = Dialog(gt("提示", "ui", language), gt("语言切换成功，需要重启应用程序以生效", "ui", language), self)
        dialog.setTitleBarVisible(False)
        dialog.yesButton.setText(gt("立即重启", "ui", language))
        dialog.cancelButton.setText(gt("稍后重启", "ui", language))

        if dialog.exec():
            app_utils.start_one_dragon(True)

    def _on_theme_changed(self, index: int, value: str) -> None:
        setTheme(Theme[self.ctx.custom_config.theme.upper()],lazy=True)

    def _on_theme_color_mode_changed(self, value: bool) -> None:
        self.custom_theme_color_btn.setEnabled(value)
        if value:
            ThemeManager.set_theme_color(self.ctx.custom_config.theme_color)
        else:
            ThemeManager.set_theme_color(_DEFAULT_THEME_COLOR)

    def _on_custom_theme_color_clicked(self) -> None:
        _c = self.ctx.custom_config.theme_color
        _d = ColorDialog(QColor(_c[0], _c[1], _c[2]), gt('请选择主题色'), self)
        _d.colorChanged.connect(self._update_custom_theme_color)
        _d.yesButton.setText(gt('确定'))
        _d.cancelButton.setText(gt('取消'))
        _d.exec()

    def _update_custom_theme_color(self, color: QColor) -> None:
        _ct = (color.red(), color.green(), color.blue())
        self.ctx.custom_config.theme_color = _ct
        ThemeManager.set_theme_color(_ct)
