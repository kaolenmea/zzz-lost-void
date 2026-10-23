from enum import Enum

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig


class LostVoidRegionType(Enum):
    """
    注意需要和识别模型的结果名称一致
    """

    ENTRY = ConfigItem('入口')
    COMBAT_RESONIUM = ConfigItem('战斗-鸣徽')
    COMBAT_GEAR = ConfigItem('战斗-武备')
    COMBAT_COIN = ConfigItem('战斗-硬币')
    CHANLLENGE_FLAWLESS = ConfigItem('挑战-无伤')
    CHANLLENGE_TIME_TRAIL = ConfigItem('挑战-限时')
    CHANLLENGE_ENEMY_TRAIL = ConfigItem('挑战-收割')
    ENCOUNTER = ConfigItem('偶遇事件')
    PRICE_DIFFERENCE = ConfigItem('代价之间')
    REST = ConfigItem('休憩调息')
    BANGBOO_STORE = ConfigItem('邦布商店')
    FRIENDLY_TALK = ConfigItem('挚交会谈')
    ELITE = ConfigItem('战斗-道中危机')
    BOSS = ConfigItem('战斗-终结之役')

    @classmethod
    def from_value(cls, value: str):
        for name in LostVoidRegionType.__members__:
            enum = cls[name]
            if enum.value.value == value:
                return enum
        return LostVoidRegionType.ENTRY


class LostVoidPeriodBuffNo(Enum):
    NO_1 = ConfigItem('第一个')
    NO_2 = ConfigItem('第二个')
    NO_3 = ConfigItem('第三个')


class LostVoidChallengeConfig(YamlConfig):

    def __init__(self, module_name: str, is_mock: bool = False):
        YamlConfig.__init__(
            self,
            module_name,
            sub_dir=['lost_void_challenge'],
            is_mock=is_mock, sample=True, copy_from_sample=False, read_sample_only=True,
        )

        # 实战中整合协战代理人武备后的第一优先级
        self._artifact_priority_in_battle: list[str] | None = None

    @property
    def auto_battle(self) -> str:
        return self.get('auto_battle', '全配队通用')

    @auto_battle.setter
    def auto_battle(self, new_value: str):
        self.update('auto_battle', new_value)

    @property
    def artifact_priority_new(self) -> bool:
        """
        优先选择NEW!藏品
        :return:
        """
        return self.get('artifact_priority_new', False)

    @artifact_priority_new.setter
    def artifact_priority_new(self, new_value: bool):
        self.update('artifact_priority_new', new_value)

    @property
    def artifact_priority(self) -> list[str]:
        return self.get('artifact_priority', [])

    @artifact_priority.setter
    def artifact_priority(self, new_value: list[str]):
        self.update('artifact_priority', new_value)

    # 战斗组：协战代理人武备属性, 程序运行时自动添加, 独立于用户配置的优先级
    @property
    def artifact_priority_in_battle(self) -> list[str]:
        if self._artifact_priority_in_battle is None:
            self._artifact_priority_in_battle = []
        return self._artifact_priority_in_battle

    def clear_artifact_priority_in_battle(self):
        self._artifact_priority_in_battle = None

    @property
    def artifact_priority_2(self) -> list[str]:
        return self.get('artifact_priority_2', [])

    @artifact_priority_2.setter
    def artifact_priority_2(self, new_value: list[str]):
        self.update('artifact_priority_2', new_value)

    @property
    def region_type_priority(self) -> list[str]:
        return self.get('region_type_priority', [])

    @region_type_priority.setter
    def region_type_priority(self, new_value: list[str]):
        self.update('region_type_priority', new_value)

    @property
    def period_buff_no(self) -> str:
        return self.get('period_buff_no', LostVoidPeriodBuffNo.NO_2.value.value)

    @period_buff_no.setter
    def period_buff_no(self, new_value: str):
        self.update('period_buff_no', new_value)

    @property
    def store_gold(self) -> bool:
        """
        @return: 是否使用金币购买商店
        """
        return self.get('store_gold', True)

    @store_gold.setter
    def store_gold(self, new_value: bool):
        self.update('store_gold', new_value)

    @property
    def store_blood(self) -> bool:
        """
        @return: 是否使用血量购买商店
        """
        return self.get('store_blood', False)

    @store_blood.setter
    def store_blood(self, new_value: bool):
        self.update('store_blood', new_value)

    @property
    def store_blood_min(self) -> int:
        """
        @return: 大于等于多少血量时 才会选择刷新和购买
        """
        return self.get('store_blood_min', 50)

    @store_blood_min.setter
    def store_blood_min(self, new_value: int):
        self.update('store_blood_min', new_value)

    @property
    def investigation_strategy(self) -> str:
        return self.get('investigation_strategy', '鸣徽狂热战略')

    @investigation_strategy.setter
    def investigation_strategy(self, new_value: str):
        self.update('investigation_strategy', new_value)

    @property
    def chase_new_mode(self) -> bool:
        """
        :return: 是否优先未满级
        """
        return self.get('chase_new_mode', False)

    @chase_new_mode.setter
    def chase_new_mode(self, new_value: bool):
        self.update('chase_new_mode', new_value)

    @property
    def same_faction_first(self) -> bool:
        """
        :return: 是否最优先选择开局通用武备同派系的鸣徽和武备
        """
        return self.get('same_faction_first', False)

    @same_faction_first.setter
    def same_faction_first(self, new_value: bool):
        self.update('same_faction_first', new_value)
