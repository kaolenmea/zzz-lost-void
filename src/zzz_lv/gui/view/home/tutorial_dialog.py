from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    MessageBoxBase,
    ScrollArea,
    SegmentedWidget,
    SimpleCardWidget,
    StrongBodyLabel,
    SubtitleLabel,
)

from one_dragon.utils.i18_utils import gt
from zzz_lv.gui.view.home.tutorial_content import (
    TutorialPage,
    TutorialStep,
    build_tutorial_pages,
)

if TYPE_CHECKING:
    from zzz_lv.context.zzz_context import ZContext

# 教程内容区高度 内容超出时在区域内滚动
_CONTENT_HEIGHT = 400


class StepCard(SimpleCardWidget):
    """
    一个教程步骤 标题 + 说明
    """

    def __init__(self, step: TutorialStep, parent: QWidget | None = None) -> None:
        SimpleCardWidget.__init__(self, parent=parent)
        self.setBorderRadius(8)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        layout.addWidget(StrongBodyLabel(gt(step.title)))
        body = BodyLabel(gt(step.body))
        body.setWordWrap(True)
        layout.addWidget(body)


class TutorialDialog(MessageBoxBase):
    """
    新手教程 按「开始前准备 / 迷失之地 / 战斗助手 / 常见问题」分标签展示
    """

    def __init__(self, ctx: ZContext, parent: QWidget | None = None) -> None:
        MessageBoxBase.__init__(self, parent)
        self.cancelButton.hide()
        self.yesButton.setText(gt('我知道了'))
        self.widget.setMinimumWidth(720)

        self.viewLayout.addWidget(SubtitleLabel(gt('新手教程')))

        self.segment = SegmentedWidget()
        self.stacked = QStackedWidget()
        pages = build_tutorial_pages(
            start_key=ctx.key_start_running.upper(),
            stop_key=ctx.key_stop_running.upper(),
        )
        for page in pages:
            self._add_page(page)
        self.segment.setCurrentItem(pages[0].key)

        self.viewLayout.addWidget(self.segment, 0, Qt.AlignmentFlag.AlignLeft)
        self.viewLayout.addWidget(self.stacked)

    def _add_page(self, page: TutorialPage) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.setSpacing(10)

        intro = BodyLabel(gt(page.intro))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        for step in page.steps:
            layout.addWidget(StepCard(step))
        layout.addStretch(1)

        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(_CONTENT_HEIGHT)
        scroll.setWidget(content)
        scroll.enableTransparentBackground()

        self.stacked.addWidget(scroll)
        self.segment.addItem(
            routeKey=page.key,
            text=gt(page.title),
            onClick=lambda _=False, w=scroll: self.stacked.setCurrentWidget(w),
        )
