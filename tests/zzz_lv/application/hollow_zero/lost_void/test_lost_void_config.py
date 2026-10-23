import pytest

from zzz_lv.application.hollow_zero.lost_void.lost_void_config import (
    LostVoidAetherActivityModeEnum,
    LostVoidConfig,
    LostVoidTaskEnum,
)


@pytest.mark.parametrize('legacy_name', ['获取所有菲林奖励', '战线肃清'])
def test_legacy_extra_task_name_is_migrated(lv_config: LostVoidConfig, legacy_name: str) -> None:
    lv_config.store.data['extra_task'] = legacy_name
    assert lv_config.extra_task == '获取大部分菲林奖励'
    assert lv_config.is_polychrome_mode
    assert lv_config.challenge_config == '菲林收集'


def test_unknown_extra_task_falls_back_to_default_challenge(lv_config: LostVoidConfig) -> None:
    lv_config.store.data['extra_task'] = '不存在的目标'
    assert not lv_config.is_polychrome_mode
    assert lv_config.challenge_config == '通关效率'


def test_polychrome_difficulty_default_and_fallback(lv_config: LostVoidConfig) -> None:
    assert lv_config.polychrome_difficulty == '难度五'
    lv_config.polychrome_difficulty = '难度六'
    assert lv_config.polychrome_difficulty == '难度六'
    lv_config.store.data['polychrome_difficulty'] = '难度七'
    assert lv_config.polychrome_difficulty == '难度五'


def test_default_extra_task_is_bounty_commission(lv_config: LostVoidConfig) -> None:
    assert lv_config.extra_task == LostVoidTaskEnum.BOUNTY_COMMISSION.value.value


@pytest.mark.parametrize(('value', 'expected'), [(0, 1), (1, 1), (10, 10), (99, 99), (100, 99), (-5, 1)])
def test_plan_run_times_is_clamped(lv_config: LostVoidConfig, value: int, expected: int) -> None:
    lv_config.plan_run_times = value
    assert lv_config.plan_run_times == expected


def test_plan_run_times_default_is_one(lv_config: LostVoidConfig) -> None:
    assert lv_config.plan_run_times == 1


def test_plan_run_times_clamps_out_of_range_saved_value(lv_config: LostVoidConfig) -> None:
    lv_config.store.data['plan_run_times'] = 500
    assert lv_config.plan_run_times == 99


def test_aether_activity_default_is_none(lv_config: LostVoidConfig) -> None:
    assert lv_config.aether_activity_goal == 0


def test_aether_activity_goal_by_mode(lv_config: LostVoidConfig) -> None:
    lv_config.aether_activity_target = 4
    lv_config.aether_activity_mode = LostVoidAetherActivityModeEnum.TARGET.value.value
    assert lv_config.aether_activity_goal == 4

    lv_config.aether_activity_mode = LostVoidAetherActivityModeEnum.FULL.value.value
    assert lv_config.aether_activity_goal == 9

    lv_config.aether_activity_mode = LostVoidAetherActivityModeEnum.NONE.value.value
    assert lv_config.aether_activity_goal == 0


@pytest.mark.parametrize(('value', 'expected'), [(0, 1), (9, 9), (12, 9)])
def test_aether_activity_target_is_clamped(lv_config: LostVoidConfig, value: int, expected: int) -> None:
    lv_config.aether_activity_target = value
    assert lv_config.aether_activity_target == expected


@pytest.mark.parametrize('name', ['ai_decision_enabled', 'ai_api_key', 'team_agent_list'])
def test_ai_config_removed(lv_config: LostVoidConfig, name: str) -> None:
    assert not hasattr(lv_config, name)
