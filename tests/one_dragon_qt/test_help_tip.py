import os

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget  # noqa: E402

from one_dragon_qt.view.setting import setting_help_tips  # noqa: E402
from one_dragon_qt.widgets.help_tip import (  # noqa: E402
    HelpTipIcon,
    apply_help_tips,
    get_card_title,
    set_help_tip,
    wrap_tip_text,
)
from one_dragon_qt.widgets.setting_card.switch_setting_card import (  # noqa: E402
    SwitchSettingCard,
)
from zzz_lv.gui import help_tips  # noqa: E402


@pytest.fixture(scope='module')
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def _make_root(titles: list[str]) -> tuple[QWidget, list[SwitchSettingCard]]:
    root = QWidget()
    layout = QVBoxLayout(root)
    cards = [SwitchSettingCard(icon='', title=t) for t in titles]
    for card in cards:
        layout.addWidget(card)
    return root, cards


def test_wrap_keeps_numbers_whole() -> None:
    text = '这一轮刷什么。完成悬赏委托：刷到每周 8000 积分的奖励就停，新手推荐。'
    lines = wrap_tip_text(text, 22).split('\n')
    assert all(len(line) <= 22 for line in lines)
    assert any(line.startswith('8000') for line in lines)
    assert ''.join(lines) == text


def test_wrap_keeps_original_newlines() -> None:
    assert wrap_tip_text('第一行\n第二行', 22) == '第一行\n第二行'


def test_wrap_long_ascii_still_splits() -> None:
    assert wrap_tip_text('a' * 30, 22).count('\n') == 1


def test_apply_help_tips(qapp: QApplication) -> None:
    root, cards = _make_root(['有说明', '没说明'])
    missing, unused = apply_help_tips(root, {'有说明': '解释', '多余的键': '无用'})
    assert missing == ['没说明']
    assert unused == ['多余的键']
    assert isinstance(cards[0].help_tip_icon, HelpTipIcon)
    assert not hasattr(cards[1], 'help_tip_icon')
    assert cards[0].help_tip_icon.toolTip() == '解释'
    # 标题仍然在原来的布局里
    assert get_card_title(cards[0]) == '有说明'


def test_set_help_tip_twice_updates_text(qapp: QApplication) -> None:
    _, cards = _make_root(['卡片'])
    card = cards[0]
    set_help_tip(card, '第一次')
    icon = card.help_tip_icon
    set_help_tip(card, '第二次')
    assert card.help_tip_icon is icon
    assert icon.toolTip() == '第二次'
    assert len(card.findChildren(HelpTipIcon)) == 1


def test_required_title_markup_is_ignored(qapp: QApplication) -> None:
    _, cards = _make_root(["Token <span style='color: #ff6b6b;'>*</span>"])
    assert get_card_title(cards[0]) == 'Token'


@pytest.mark.parametrize('tips', [
    help_tips.GAME_SETTING_TIPS,
    help_tips.OVERLAY_SETTING_TIPS,
    help_tips.LOST_VOID_TIPS,
    help_tips.BATTLE_ASSISTANT_TIPS,
    setting_help_tips.ENV_SETTING_TIPS,
    setting_help_tips.PUSH_SETTING_TIPS,
    setting_help_tips.CUSTOM_SETTING_TIPS,
])
def test_tips_not_empty(tips: dict[str, str]) -> None:
    assert tips
    for title, text in tips.items():
        assert title.strip() and text.strip()
