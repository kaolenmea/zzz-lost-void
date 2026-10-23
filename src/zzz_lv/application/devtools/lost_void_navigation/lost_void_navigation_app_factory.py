from __future__ import annotations

from typing import TYPE_CHECKING

from one_dragon.base.operation.application.application_factory import ApplicationFactory
from one_dragon.base.operation.application_base import Application
from zzz_lv.application.devtools.lost_void_navigation import lost_void_navigation_const
from zzz_lv.application.devtools.lost_void_navigation.lost_void_navigation_app import (
    LostVoidNavigationApp,
)

if TYPE_CHECKING:
    from zzz_lv.context.zzz_context import ZContext


class LostVoidNavigationAppFactory(ApplicationFactory):

    def __init__(self, ctx: ZContext):
        ApplicationFactory.__init__(self, lost_void_navigation_const)
        self.ctx: ZContext = ctx

    def create_application(self, instance_idx: int, group_id: str) -> Application:
        return LostVoidNavigationApp(self.ctx)
