import re
import time

from one_dragon.base.controller.drag_timing import DragTiming
from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.matcher.match_result import MatchResult, MatchResultList
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from zzz_lv.context.zzz_context import ZContext
from zzz_lv.operation.predefined_team_recognizer import recognize_predefined_team
from zzz_lv.operation.zzz_operation import ZOperation
from zzz_lv.screen_area.screen_normal_world import ScreenNormalWorldEnum


class ChoosePredefinedTeam(ZOperation):

    STATUS_CONTINUE_CHOOSE: str = '继续选择'
    STATUS_CHOOSE_FINISHED: str = '选择完成'
    STATUS_TEAM_LIST_READY: str = '已在预备编队列表'
    STATUS_CHOOSE_FINISHED_WITHOUT_CONFIRM: str = '选择完成且不确认'

    SELECT_BUTTON_FEEDBACK_HALF_WIDTH: int = 160
    SELECT_BUTTON_FEEDBACK_HALF_HEIGHT: int = 120
    TEAM_SCROLL_STEP: int = 4
    TEAM_SLOT_COUNT: int = 6
    TEAM_DRAG_START: Point = Point(960, 715)
    TEAM_DRAG_END: Point = Point(960, 150)
    # 预备编队翻页单独指定等待时间，避免影响其他场景的拖拽。
    TEAM_DRAG_TIMING: DragTiming = DragTiming(
        press_wait=0.6, move_duration=0.3, release_wait=1.0,
    )

    def __init__(
        self,
        ctx: ZContext,
        target_team_idx_list: list[int] | None = None,
        start_at_team_list: bool = False,
        finish_without_confirm: bool = False,
    ):
        """
        在预备编队界面选择队伍
        """
        ZOperation.__init__(
            self,
            ctx,
            op_name=f"{gt('选择预备编队')} {target_team_idx_list}",
            need_check_game_win=not start_at_team_list,
        )

        self.target_team_idx_list: list[int] = (
            [] if target_team_idx_list is None else target_team_idx_list
        )
        self.current_target_idx: int = 0
        self.current_scroll_page: int = 0
        self.pending_select_button_center: Point | None = None
        self.pending_cancel_button_center: Point | None = None
        self.start_at_team_list: bool = start_at_team_list
        self.finish_without_confirm: bool = finish_without_confirm

    @operation_node(name='画面识别', node_max_retry_times=10, is_start_node=True)
    def check_screen(self) -> OperationRoundResult:
        if self.start_at_team_list:
            return self.round_success(ChoosePredefinedTeam.STATUS_TEAM_LIST_READY)

        result = self.round_by_find_area(self.last_screenshot, '实战模拟室', '预备编队')
        if result.is_success:
            return self.round_success(result.status)
        return self.round_retry(result.status, wait=1)

    @node_from(from_name='画面识别', status='预备编队')
    @operation_node(name='点击预备编队')
    def click_team(self) -> OperationRoundResult:
        return self.round_by_find_and_click_area(
            self.last_screenshot,
            '实战模拟室',
            '预备编队',
            success_wait=1,
            retry_wait=1,
        )

    @node_from(from_name='点击预备编队')
    @node_from(from_name='画面识别', status=STATUS_TEAM_LIST_READY)
    @node_from(from_name='选择编队', status=STATUS_CONTINUE_CHOOSE)
    @operation_node(name='选择编队')
    def choose_team(self) -> OperationRoundResult:
        """
        分轮完成预备编队的选择。

        先翻到目标编队所在页面。游戏可能已有预选编队，
        此时需取消预选并等待原按钮恢复为 SELECT，避免直接选择失败。
        取消或选择后若持续无法确认状态，按节点重试上限失败退出，避免无限等待。
        每次点击后也要等待画面确认选中，再继续处理下一支编队。
        """
        if self.current_target_idx >= len(self.target_team_idx_list):
            if self.finish_without_confirm:
                return self.round_success(
                    ChoosePredefinedTeam.STATUS_CHOOSE_FINISHED_WITHOUT_CONFIRM
                )

            result = self.round_by_find_area(
                self.last_screenshot,
                '实战模拟室',
                '预备出战',
            )
            if result.is_success:
                return self.round_success(ChoosePredefinedTeam.STATUS_CHOOSE_FINISHED)
            return self.round_retry(result.status, wait=1)

        target_team_idx = self.target_team_idx_list[self.current_target_idx]
        if target_team_idx < 0:
            return self.round_fail(f'选择的预备编队下标错误 {target_team_idx}')

        current_page_start_team_idx = (
            self.current_scroll_page * self.TEAM_SCROLL_STEP
        )
        current_page_end_team_idx = (
            current_page_start_team_idx + self.TEAM_SLOT_COUNT - 1
        )
        if target_team_idx > current_page_end_team_idx:
            self._scroll_team_list(-1)
            self.current_scroll_page += 1
            return self.round_wait(ChoosePredefinedTeam.STATUS_CONTINUE_CHOOSE, wait=1)
        if target_team_idx < current_page_start_team_idx:
            self._scroll_team_list(1)
            self.current_scroll_page -= 1
            return self.round_wait(ChoosePredefinedTeam.STATUS_CONTINUE_CHOOSE, wait=1)

        target_team = self.ctx.team_config.get_team_by_idx(target_team_idx)
        if target_team is None:
            return self.round_fail(f'选择的预备编队下标错误 {target_team_idx}')
        team_slot_rect = self._get_team_slot_rect_by_idx(
            target_team_idx - current_page_start_team_idx
        )

        if self.pending_cancel_button_center is not None:
            ocr_result_map = self.ctx.ocr.run_ocr(self.last_screenshot)
            if not self._is_select_button_visible(ocr_result_map):
                return self.round_retry(
                    '取消预选后未恢复SELECT',
                    wait=0.5,
                )
            log.debug('预备编队取消预选已确认:队伍:%s', target_team.name)
            self.pending_cancel_button_center = None
            return self.round_wait(
                ChoosePredefinedTeam.STATUS_CONTINUE_CHOOSE,
                wait=0.2,
            )

        if self.pending_select_button_center is not None:
            ocr_result_map = self.ctx.ocr.run_ocr(self.last_screenshot)
            if not self._is_team_selected(ocr_result_map):
                return self.round_retry(
                    '选择预备编队后未确认选中状态',
                    wait=0.5,
                )
            log.info(
                '预备编队已选:队伍:%s 序号:%d',
                target_team.name,
                target_team_idx + 1,
            )
            self.pending_select_button_center = None
            self.current_target_idx += 1
            return self.round_wait(
                ChoosePredefinedTeam.STATUS_CONTINUE_CHOOSE,
                wait=0.2,
            )

        ocr_result_map = self.ctx.ocr.run_ocr(self.last_screenshot)
        recognition = recognize_predefined_team(
            self.ctx,
            self.last_screenshot,
            ocr_result_map,
            team_slot_rect,
        )
        team_name = recognition.team_name
        if team_name is not None:
            target_team.name = team_name

        # 识别到代理人才写角色；识别不到只同步队名，避免清空已有角色。
        agent_list = [
            match_result.data
            for match_result in recognition.agent_match_result_list
        ]
        if len(agent_list) > 0:
            team_member_count = self._get_team_member_count(
                ocr_result_map,
                team_slot_rect,
            )
            self.ctx.team_config.update_team_by_idx(
                target_team_idx,
                team_name,
                agent_list[:team_member_count] if team_member_count is not None else agent_list,
            )
        elif team_name is not None:
            self.ctx.team_config.update_team_name_by_idx(target_team_idx, team_name)

        select_button_mr = self._find_select_button(ocr_result_map, team_slot_rect)
        if select_button_mr is None:
            selected_button_mr = self._find_selected_button(
                ocr_result_map,
                team_slot_rect,
            )
            if selected_button_mr is None:
                return self.round_fail(f'当前编队未找到SELECT {target_team.name}')
            log.info('预备编队取消预选:队伍:%s', target_team.name)
            self.ctx.controller.click(selected_button_mr.center)
            self.pending_cancel_button_center = selected_button_mr.center
            return self.round_wait(
                ChoosePredefinedTeam.STATUS_CONTINUE_CHOOSE,
                wait=0.5,
            )

        log.info(
            '预备编队选择:队伍:%s 序号:%d',
            target_team.name,
            target_team_idx + 1,
        )
        self.ctx.controller.click(select_button_mr.center)
        self.pending_select_button_center = select_button_mr.center
        return self.round_wait(ChoosePredefinedTeam.STATUS_CONTINUE_CHOOSE, wait=0.5)

    @node_from(from_name='选择编队', status=STATUS_CHOOSE_FINISHED)
    @operation_node(name='选择编队确认')
    def click_confirm(self) -> OperationRoundResult:
        result = self.round_by_find_and_click_area(
            self.last_screenshot,
            '实战模拟室',
            '预备出战',
        )
        if result.is_success:
            log.info('预备编队选择完成:已点击预备出战')
            time.sleep(0.5)
            self.ctx.controller.mouse_move(ScreenNormalWorldEnum.UID.value.center)
            return self.round_success(result.status, wait=0.5)
        return self.round_retry(result.status, wait=1)

    def _get_team_slot_rect_by_idx(self, card_idx: int) -> Rect:
        """返回当前页第 ``card_idx`` 张编队卡片区域。"""
        area = self.ctx.screen_loader.get_area('编队选择', f'编队槽位{card_idx}')
        if area is None:
            raise RuntimeError(f'未配置编队槽位{card_idx}')
        return area.rect

    def _get_select_mark_rect(self, team_slot_rect: Rect) -> Rect:
        """返回当前编队卡片所在列的选择标记区域。"""
        left_area = self.ctx.screen_loader.get_area('编队选择', '选择标记左')
        right_area = self.ctx.screen_loader.get_area('编队选择', '选择标记右')
        if left_area is None or right_area is None:
            raise RuntimeError('未配置编队选择标记区域')
        return min(
            [left_area, right_area],
            key=lambda area: abs(area.center.x - team_slot_rect.center.x),
        ).rect

    @staticmethod
    def _is_match_result_in_rect(match_result: MatchResult, rect: Rect) -> bool:
        return (
            match_result.left_top.x >= rect.x1
            and match_result.right_bottom.x <= rect.x2
            and match_result.left_top.y >= rect.y1
            and match_result.right_bottom.y <= rect.y2
        )

    def _find_select_button(
        self,
        ocr_result_map: dict[str, MatchResultList],
        team_slot_rect: Rect,
    ) -> MatchResult | None:
        select_mark_rect = self._get_select_mark_rect(team_slot_rect)
        candidate_list: list[MatchResult] = []
        for text, mr_list in ocr_result_map.items():
            if not text.replace(' ', '').upper().endswith('SELECT'):
                continue
            candidate_list.extend(
                mr
                for mr in mr_list
                if self._is_match_result_in_rect(mr, select_mark_rect)
            )

        if len(candidate_list) == 0:
            return None
        return min(
            candidate_list,
            key=lambda mr: abs(mr.center.y - team_slot_rect.center.y),
        )

    def _find_selected_button(
        self,
        ocr_result_map: dict[str, MatchResultList],
        team_slot_rect: Rect,
    ) -> MatchResult | None:
        """查找当前卡片的已选状态，用于在缺少 SELECT 时先取消预选。"""
        select_mark_rect = self._get_select_mark_rect(team_slot_rect)
        candidate_list: list[MatchResult] = []
        for text, mr_list in ocr_result_map.items():
            if not self._is_selected_text(text.replace(' ', '').upper()):
                continue
            candidate_list.extend(
                mr
                for mr in mr_list
                if self._is_match_result_in_rect(mr, select_mark_rect)
            )

        if len(candidate_list) == 0:
            return None
        return min(
            candidate_list,
            key=lambda mr: abs(mr.center.y - team_slot_rect.center.y),
        )

    def _is_select_button_visible(
        self,
        ocr_result_map: dict[str, MatchResultList],
    ) -> bool:
        """确认取消后原按钮区域恢复 SELECT，避免误认其他卡片的 SELECT。"""
        if self.pending_cancel_button_center is None:
            return False

        center = self.pending_cancel_button_center
        for text, mr_list in ocr_result_map.items():
            if not text.replace(' ', '').upper().endswith('SELECT'):
                continue
            for mr in mr_list:
                if (
                    abs(mr.center.x - center.x)
                    <= ChoosePredefinedTeam.SELECT_BUTTON_FEEDBACK_HALF_WIDTH
                    and abs(mr.center.y - center.y)
                    <= ChoosePredefinedTeam.SELECT_BUTTON_FEEDBACK_HALF_HEIGHT
                ):
                    return True
        return False

    @staticmethod
    def _is_selected_text(normalized_text: str) -> bool:
        """判断 OCR 文本是否为选中态标记。"""
        return normalized_text == 'TEAM' or normalized_text.endswith('SELECTED')

    def _is_team_selected(
        self,
        ocr_result_map: dict[str, MatchResultList],
    ) -> bool:
        if self.pending_select_button_center is None:
            return False

        center = self.pending_select_button_center
        for text, mr_list in ocr_result_map.items():
            normalized_text = text.replace(' ', '').upper()
            for mr in mr_list:
                if (
                    abs(mr.center.x - center.x)
                    > ChoosePredefinedTeam.SELECT_BUTTON_FEEDBACK_HALF_WIDTH
                    or abs(mr.center.y - center.y)
                    > ChoosePredefinedTeam.SELECT_BUTTON_FEEDBACK_HALF_HEIGHT
                ):
                    continue
                if normalized_text.endswith('SELECT'):
                    return False
                if self._is_selected_text(normalized_text):
                    return True

        return False

    def _get_team_member_count(
        self,
        ocr_result_map: dict[str, MatchResultList],
        team_slot_rect: Rect,
    ) -> int | None:
        """获取当前卡片 X/Y 中表示代理人数的分母 Y。"""
        for text, mr_list in ocr_result_map.items():
            normalized = text.replace(' ', '')
            # OCR 可能把斜线误识为 1，例如 313 代表 3/3。
            m = re.fullmatch(r'(\d+)/(\d+)', normalized)
            if m is None:
                m = re.fullmatch(r'(\d)1(\d)', normalized)
            if m is None:
                continue
            for mr in mr_list:
                if self._is_match_result_in_rect(mr, team_slot_rect):
                    return int(m.group(2))
        return None

    def _scroll_team_list(self, direction: int) -> None:
        """
        按固定坐标拖动列表。

        固定坐标避免鼠标停留位置影响翻页；向下扫描和向上回退使用相反方向，
        每次拖动对应 current_scroll_page 的一页变化。
        """
        if direction < 0:
            self.ctx.controller.drag_to(
                start=ChoosePredefinedTeam.TEAM_DRAG_START,
                end=ChoosePredefinedTeam.TEAM_DRAG_END,
                timing=ChoosePredefinedTeam.TEAM_DRAG_TIMING,
            )
        else:
            self.ctx.controller.drag_to(
                start=ChoosePredefinedTeam.TEAM_DRAG_END,
                end=ChoosePredefinedTeam.TEAM_DRAG_START,
                timing=ChoosePredefinedTeam.TEAM_DRAG_TIMING,
            )
