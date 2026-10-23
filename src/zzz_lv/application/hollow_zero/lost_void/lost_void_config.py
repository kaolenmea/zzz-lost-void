from enum import Enum

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.operation.application.application_config import ApplicationConfig


class LostVoidTaskEnum(Enum):

    BOUNTY_COMMISSION = ConfigItem('完成悬赏委托', desc='完成每周8000积分奖励')
    EVAL_POINT = ConfigItem('刷满业绩点', desc='刷满每周业绩点')
    POLYCHROME = ConfigItem('战线肃清', desc='自动在战线肃清·难度五辅助收集所有首通和以太活性奖励；奖励仍需逐项核对，不能自动确认全部完成')


class LostVoidAetherActivityModeEnum(Enum):

    NONE = ConfigItem('不选', desc='不选活性增幅 敌人强度不变 推荐')
    TARGET = ConfigItem('指定点数', desc='选到指定的活性点数为止')
    FULL = ConfigItem('自动选满', desc='尽量选满 9 点活性增幅 敌人会明显变强')


# 旧版本保存过的刷取目标名 读取时迁移成新名字
LEGACY_EXTRA_TASK_NAME: dict[str, str] = {
    '获取所有菲林奖励': LostVoidTaskEnum.POLYCHROME.value.value,
}

PLAN_RUN_TIMES_MIN: int = 1
PLAN_RUN_TIMES_MAX: int = 99
AETHER_ACTIVITY_MAX: int = 9  # 以太活性点数上限


# 刷取目标 -> 使用的内置挑战配置
TASK_CHALLENGE_CONFIG: dict[str, str] = {
    LostVoidTaskEnum.BOUNTY_COMMISSION.value.value: '通关效率',
    LostVoidTaskEnum.EVAL_POINT.value.value: '通关效率',
    LostVoidTaskEnum.POLYCHROME.value.value: '菲林收集',
}


class LostVoidConfig(ApplicationConfig):

    def __init__(self, instance_idx: int, group_id: str):
        ApplicationConfig.__init__(
            self,
            app_id='lost_void',
            instance_idx=instance_idx,
            group_id=group_id,
        )

    @property
    def extra_task(self) -> str:
        value = self.get('extra_task', LostVoidTaskEnum.BOUNTY_COMMISSION.value.value)
        return LEGACY_EXTRA_TASK_NAME.get(value, value)

    @extra_task.setter
    def extra_task(self, new_value: str):
        self.update('extra_task', new_value)

    @property
    def is_bounty_commission_mode(self) -> bool:
        return self.extra_task == LostVoidTaskEnum.BOUNTY_COMMISSION.value.value

    @property
    def is_polychrome_mode(self) -> bool:
        return self.extra_task == LostVoidTaskEnum.POLYCHROME.value.value

    @property
    def mission_name(self) -> str:
        return self.get('mission_name', '战线肃清')

    @mission_name.setter
    def mission_name(self, new_value: str):
        self.update('mission_name', new_value)

    @property
    def effective_mission_name(self) -> str:
        """菲林目标固定用战线肃清收集，保留用户保存的周常副本。"""
        return '战线肃清' if self.is_polychrome_mode else self.mission_name

    @effective_mission_name.setter
    def effective_mission_name(self, new_value: str) -> None:
        """保存运行页选择的周常副本。"""
        self.mission_name = new_value

    @property
    def challenge_config(self) -> str:
        """
        挑战配置随刷取目标自动切换 不由用户选择
        """
        return TASK_CHALLENGE_CONFIG.get(self.extra_task, '通关效率')

    @property
    def predefined_team_no(self) -> int:
        """出战时选择的预备编队编号 对应游戏里的「编队 N」 0 表示沿用游戏当前编队"""
        return self.get('predefined_team_no', 0)

    @predefined_team_no.setter
    def predefined_team_no(self, new_value: int) -> None:
        self.update('predefined_team_no', new_value)

    @property
    def plan_run_times(self) -> int:
        """计划刷取次数 刷满后停止 范围 1~99"""
        value = self.get('plan_run_times', PLAN_RUN_TIMES_MIN)
        return max(PLAN_RUN_TIMES_MIN, min(PLAN_RUN_TIMES_MAX, int(value)))

    @plan_run_times.setter
    def plan_run_times(self, new_value: int) -> None:
        self.update('plan_run_times', max(PLAN_RUN_TIMES_MIN, min(PLAN_RUN_TIMES_MAX, int(new_value))))

    @property
    def aether_activity_mode(self) -> str:
        """以太活性的活性增幅选择方式 只在战线肃清生效"""
        return self.get('aether_activity_mode', LostVoidAetherActivityModeEnum.NONE.value.value)

    @aether_activity_mode.setter
    def aether_activity_mode(self, new_value: str) -> None:
        self.update('aether_activity_mode', new_value)

    @property
    def aether_activity_target(self) -> int:
        """指定点数模式下要选到的活性点数 范围 1~9"""
        value = self.get('aether_activity_target', 1)
        return max(1, min(AETHER_ACTIVITY_MAX, int(value)))

    @aether_activity_target.setter
    def aether_activity_target(self, new_value: int) -> None:
        self.update('aether_activity_target', max(1, min(AETHER_ACTIVITY_MAX, int(new_value))))

    @property
    def aether_activity_goal(self) -> int:
        """本次要选到的活性点数 0 表示不选"""
        mode = self.aether_activity_mode
        if mode == LostVoidAetherActivityModeEnum.FULL.value.value:
            return AETHER_ACTIVITY_MAX
        if mode == LostVoidAetherActivityModeEnum.TARGET.value.value:
            return self.aether_activity_target
        return 0

    @property
    def depth_avoid_enabled(self) -> bool:
        """寻路时用深度模型提前绕开障碍物 没放置深度模型时不生效"""
        return self.get('depth_avoid_enabled', True)

    @depth_avoid_enabled.setter
    def depth_avoid_enabled(self, new_value: bool) -> None:
        self.update('depth_avoid_enabled', new_value)
