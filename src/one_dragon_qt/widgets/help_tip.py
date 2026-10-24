import re

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QWidget
from qfluentwidgets import ToolTipFilter, ToolTipPosition, themeColor
from qfluentwidgets.components.settings.setting_card import SettingCard

from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log

# 悬停说明每行的字数 qfluentwidgets 的气泡不会自动换行
TIP_LINE_WIDTH: int = 22

_HTML_TAG_PATTERN = re.compile(r'<[^>]+>')


def _is_ascii_word_char(char: str) -> bool:
    return char.isascii() and char.isalnum()


def wrap_tip_text(text: str, width: int = TIP_LINE_WIDTH) -> str:
    """
    把说明文字按字数折行 原文里的换行保留 不会把连续的数字或英文单词从中间断开
    :param text: 说明文字
    :param width: 每行最多的字数
    """
    lines: list[str] = []
    for paragraph in text.split('\n'):
        while len(paragraph) > width:
            cut = width
            if _is_ascii_word_char(paragraph[cut - 1]) and _is_ascii_word_char(paragraph[cut]):
                # 往前找这一串数字或英文的开头 整串放到下一行
                start = cut
                while start > 0 and _is_ascii_word_char(paragraph[start - 1]):
                    start -= 1
                if start > 0:
                    cut = start
            lines.append(paragraph[:cut])
            paragraph = paragraph[cut:]
        lines.append(paragraph)
    return '\n'.join(lines)


class HelpTipIcon(QWidget):
    """
    标题旁边的感叹号 鼠标悬停显示说明
    """

    SIZE: int = 16

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        QWidget.__init__(self, parent=parent)
        self.setFixedSize(HelpTipIcon.SIZE, HelpTipIcon.SIZE)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)
        self.setToolTip(wrap_tip_text(text))
        self.installEventFilter(ToolTipFilter(self, showDelay=100, position=ToolTipPosition.TOP))

    def set_text(self, text: str) -> None:
        self.setToolTip(wrap_tip_text(text))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 点在感叹号上不要传给卡片 否则可展开的卡片会被展开或收起
        event.accept()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = themeColor()
        painter.setPen(QPen(color, 1.4))
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        painter.drawEllipse(rect)

        font = QFont(self.font())
        font.setBold(True)
        font.setPixelSize(11)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, '!')


def set_help_tip(card: SettingCard, text: str) -> None:
    """
    给设置卡片的标题后面加感叹号 已经加过则只更新说明文字
    :param card: 设置卡片 需要有 titleLabel 和 vBoxLayout
    :param text: 悬停显示的说明
    """
    icon: HelpTipIcon | None = getattr(card, 'help_tip_icon', None)
    if icon is not None:
        icon.set_text(text)
        return

    title_label = card.titleLabel
    index = card.vBoxLayout.indexOf(title_label)
    if index < 0:
        return

    card.vBoxLayout.removeWidget(title_label)
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(6)
    icon = HelpTipIcon(text, parent=card)
    row.addWidget(title_label, 0, Qt.AlignmentFlag.AlignVCenter)
    row.addWidget(icon, 0, Qt.AlignmentFlag.AlignVCenter)
    row.addStretch(1)
    card.vBoxLayout.insertLayout(index, row)
    card.help_tip_icon = icon


def get_card_title(card: SettingCard) -> str:
    """
    取卡片标题的纯文字 推送页的必填项标题带 HTML 星号 需要去掉
    """
    return _HTML_TAG_PATTERN.sub('', card.titleLabel.text()).replace('*', '').strip()


def apply_help_tips(root: QWidget, tips: dict[str, str]) -> tuple[list[str], list[str]]:
    """
    给 root 下所有设置卡片按标题加上感叹号说明
    :param root: 页面内容控件
    :param tips: 卡片标题 -> 说明 标题写中文原文 这里会按当前语言翻译后再匹配
    :return: (没有说明的卡片标题, 没有匹配到卡片的说明标题) 用于发现改了标题后说明失效
    """
    translated: dict[str, tuple[str, str]] = {gt(title): (title, gt(text)) for title, text in tips.items()}
    used: set[str] = set()
    missing: list[str] = []

    for card in root.findChildren(SettingCard):
        title = get_card_title(card)
        found = translated.get(title)
        if found is None:
            if title:
                missing.append(title)
            continue
        set_help_tip(card, found[1])
        used.add(found[0])

    unused = [title for title in tips if title not in used]
    if missing:
        log.debug(f'以下设置项没有说明: {missing}')
    if unused:
        log.debug(f'以下说明没有匹配到设置项: {unused}')
    return missing, unused
