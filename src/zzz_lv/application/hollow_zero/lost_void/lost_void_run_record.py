
from one_dragon.base.operation.application_run_record import (
    AppRunRecord,
    AppRunRecordPeriod,
)
from one_dragon.utils import os_utils
from zzz_lv.application.hollow_zero.lost_void.lost_void_config import (
    LostVoidConfig,
    LostVoidTaskEnum,
)


class LostVoidRunRecord(AppRunRecord):

    def __init__(self, config: LostVoidConfig, instance_idx: int | None = None, game_refresh_hour_offset: int = 0):
        AppRunRecord.__init__(
            self,
            'lost_void',
            instance_idx=instance_idx,
            game_refresh_hour_offset=game_refresh_hour_offset,
            record_period=AppRunRecordPeriod.WEEKLY
        )

        self.config: LostVoidConfig = config

    @property
    def weekly_run_times(self) -> int:
        return self.get('weekly_run_times', 0)

    @weekly_run_times.setter
    def weekly_run_times(self, new_value: int):
        self.update('weekly_run_times', new_value)

    def add_complete_times(self) -> None:
        """
        每周增加一次完成次数
        @return:
        """
        self.weekly_run_times += 1
        self.plan_done_times += 1

    @property
    def plan_done_times(self) -> int:
        """本轮计划已完成的次数 达到计划刷取次数后停止 下次启动重新计数"""
        return self.get('plan_done_times', 0)

    @plan_done_times.setter
    def plan_done_times(self, new_value: int) -> None:
        self.update('plan_done_times', new_value)

    @property
    def plan_finished(self) -> bool:
        """本轮计划次数是否已经刷满"""
        return self.plan_done_times >= self.config.plan_run_times

    @property
    def bounty_commission_complete(self) -> bool:
        """
        是否已经刷满悬赏委托
        """
        return self.get('bounty_commission_complete', False)

    @bounty_commission_complete.setter
    def bounty_commission_complete(self, new_value: bool) -> None:
        """
        是否已经刷满悬赏委托
        """
        self.update('bounty_commission_complete', new_value)

    @property
    def eval_point_complete(self) -> bool:
        """
        是否已经刷满业绩点
        """
        return self.get('eval_point_complete', False)

    @eval_point_complete.setter
    def eval_point_complete(self, new_value: bool) -> None:
        """
        是否已经刷满业绩点
        """
        self.update('eval_point_complete', new_value)

    @property
    def polychrome_notice(self) -> str:
        """菲林收集最近一次停止后需要核对的原因，不代表完成进度。"""
        return self.get('polychrome_notice', '')

    @polychrome_notice.setter
    def polychrome_notice(self, new_value: str) -> None:
        """保存需要核对的原因。"""
        self.update('polychrome_notice', new_value)

    @property
    def is_finished(self) -> bool:
        """
        判断当前目标是否完成；菲林目标尚无完整的奖励完成判定。
        """
        if self.config.extra_task == LostVoidTaskEnum.BOUNTY_COMMISSION.value.value:
            # 需要刷悬赏委托 就看8000积分奖励完成没有
            return self.bounty_commission_complete
        elif self.config.extra_task == LostVoidTaskEnum.EVAL_POINT.value.value:
            # 需要刷业绩 就看空业绩点出来没有
            return self.eval_point_complete
        else:
            return False

    @property
    def run_status_under_now(self) -> int:
        """
        基于当前时间显示的运行状态
        :return:
        """
        if self.config.is_polychrome_mode:
            return (
                AppRunRecord.STATUS_WAIT
                if self.run_status == AppRunRecord.STATUS_SUCCESS
                else self.run_status
            )
        current_dt = self.get_current_dt()
        if os_utils.get_sunday_dt(self.dt) != os_utils.get_sunday_dt(current_dt):  # 上一次运行已经是上一周
            # 必定是重置
            return AppRunRecord.STATUS_WAIT
        elif self.is_finished:
            return AppRunRecord.STATUS_SUCCESS
        else:
            return AppRunRecord.STATUS_WAIT

    def check_and_update_status(self) -> None:
        """
        判断并更新状态
        """
        current_dt = self.get_current_dt()
        if os_utils.get_sunday_dt(self.dt) != os_utils.get_sunday_dt(current_dt):  # 上一次运行已经是上一周
            # 必定是重置
            self.reset_record()
            self.reset_for_weekly()
        elif not self.is_finished:
            self.reset_record()

    def reset_for_weekly(self) -> None:
        self.weekly_run_times = 0
        self.plan_done_times = 0
        self.bounty_commission_complete = False
        self.eval_point_complete = False
