from zzz_lv.application.hollow_zero.lost_void.lost_void_config import (
    LostVoidConfig,
    LostVoidTaskEnum,
)
from zzz_lv.application.hollow_zero.lost_void.lost_void_run_record import (
    LostVoidRunRecord,
)


def test_plan_finished_after_reaching_plan_run_times(
    lv_config: LostVoidConfig, lv_run_record: LostVoidRunRecord
) -> None:
    lv_config.plan_run_times = 2
    assert not lv_run_record.plan_finished

    lv_run_record.add_complete_times()
    assert lv_run_record.plan_done_times == 1
    assert not lv_run_record.plan_finished

    lv_run_record.add_complete_times()
    assert lv_run_record.plan_finished
    assert lv_run_record.weekly_run_times == 2


def test_default_plan_is_one_run(lv_run_record: LostVoidRunRecord) -> None:
    assert not lv_run_record.plan_finished
    lv_run_record.add_complete_times()
    assert lv_run_record.plan_finished


def test_reset_for_weekly_clears_plan_progress(lv_run_record: LostVoidRunRecord) -> None:
    lv_run_record.add_complete_times()
    lv_run_record.reset_for_weekly()
    assert lv_run_record.plan_done_times == 0
    assert lv_run_record.weekly_run_times == 0


def test_polychrome_goal_stops_only_by_plan(
    lv_config: LostVoidConfig, lv_run_record: LostVoidRunRecord
) -> None:
    """战线肃清目标没有每周完成判定，只靠计划次数停止"""
    lv_config.extra_task = LostVoidTaskEnum.POLYCHROME.value.value
    lv_run_record.add_complete_times()
    assert not lv_run_record.is_finished
    assert lv_run_record.plan_finished
