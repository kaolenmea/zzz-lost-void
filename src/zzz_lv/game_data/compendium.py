import os

from one_dragon.utils import os_utils, yaml_utils
from one_dragon.utils.log_utils import log


class CompendiumTab:

    def __init__(self, tab_name: str, category_list: list | None = None):
        self.tab_name: str = tab_name
        self.category_list: list[CompendiumCategory] = []
        if category_list is not None:
            for category_list_item in category_list:
                category_item = CompendiumCategory(**category_list_item)
                category_item.set_tab(self)
                self.category_list.append(category_item)


class CompendiumCategory:

    def __init__(self, category_name: str, mission_type_list: list | None = None):
        self.tab: CompendiumTab | None = None
        self.category_name: str = category_name
        self.mission_type_list: list[CompendiumMissionType] = []
        if mission_type_list is not None:
            for mission_type_item in mission_type_list:
                mission_type = CompendiumMissionType(**mission_type_item)
                mission_type.set_category(self)
                self.mission_type_list.append(mission_type)

    def set_tab(self, tab: CompendiumTab):
        self.tab = tab


class CompendiumMissionType:

    def __init__(self, mission_type_name: str, mission_type_name_display: str | None = None,
                 mission_list: list | None = None, alias_list: list[str] | None = None):
        self.category: CompendiumCategory | None = None
        self.mission_type_name: str = mission_type_name
        self.mission_type_name_display: str = mission_type_name
        if mission_type_name_display is not None:
            self.mission_type_name_display = mission_type_name_display
        self.alias_list: list[str] = alias_list if alias_list is not None else []
        self.mission_list: list[CompendiumMission] = []
        if mission_list is not None:
            for mission_item in mission_list:
                mission = CompendiumMission(**mission_item)
                mission.set_mission_type(self)
                self.mission_list.append(mission)

    def set_category(self, category: CompendiumCategory):
        self.category = category

    @property
    def is_agent_plan(self) -> bool:
        return self.mission_type_name == '代理人方案培养'


class CompendiumMission:

    def __init__(self, mission_name: str, mission_name_display: str | None = None):
        self.mission_type: CompendiumMissionType | None = None
        self.mission_name: str = mission_name
        self.mission_name_display: str = mission_name if mission_name_display is None else mission_name_display

    def set_mission_type(self, mission_type: CompendiumMissionType):
        self.mission_type = mission_type


class CompendiumData:

    def __init__(self, tab_list: list | None = None):
        self.tab_list: list[CompendiumTab] = []
        if tab_list is not None:
            for tab_item in tab_list:
                self.tab_list.append(CompendiumTab(**tab_item))


class CompendiumService:

    def __init__(self):
        self.data: CompendiumData = CompendiumData()

    def reload(self) -> None:
        """
        重新加载数据
        :return:
        """
        self._load_all_compendium()

    def _load_all_compendium(self) -> None:
        """
        加载副本
        :return:
        """
        file_path = os.path.join(
            os_utils.get_path_under_work_dir('assets', 'game_data'),
            'compendium_data.yml'
        )

        if not os.path.exists(file_path):
            return

        try:
            with open(file_path, encoding='utf-8') as file:
                tab_list: list[dict] = yaml_utils.safe_load(file)
                self.data = CompendiumData(tab_list)
        except Exception:
            log.error(f'文件读取失败 {file_path}', exc_info=True)

    def get_tab_data(self, tab_name: str) -> CompendiumTab | None:
        for tab_item in self.data.tab_list:
            if tab_item.tab_name == tab_name:
                return tab_item
        return None

    def get_category_list_data(self, tab_name: str) -> list[CompendiumCategory]:
        tab = self.get_tab_data(tab_name)

        if tab is None:
            return []

        return tab.category_list

    def get_category_data(self, tab_name: str, category_name: str) -> CompendiumCategory | None:
        category_list = self.get_category_list_data(tab_name)

        for category_item in category_list:
            if category_item.category_name == category_name:
                return category_item

        return None

    def get_mission_type_list_data(self, tab_name: str, category_name: str) -> list[CompendiumMissionType]:
        category = self.get_category_data(tab_name, category_name)
        if category is not None:
            return category.mission_type_list
        else:
            return []

    def get_mission_type_data(self, tab_name: str, category_name: str, mission_type_name: str) -> CompendiumMissionType | None:
        mission_type_list = self.get_mission_type_list_data(tab_name, category_name)

        for mission_type in mission_type_list:
            if mission_type.mission_type_name == mission_type_name:
                return mission_type

        return None

    def get_mission_list_data(self, tab_name: str, category_name: str, mission_type_name: str) -> list[CompendiumMission]:
        mission_type = self.get_mission_type_data(tab_name, category_name, mission_type_name)
        if mission_type is not None:
            return mission_type.mission_list
        else:
            return []

    def get_mission_data(self, tab_name: str, category_name: str, mission_type_name: str, mission_name: str) -> CompendiumMission | None:
        mission_list = self.get_mission_list_data(tab_name, category_name, mission_type_name)
        for mission in mission_list:
            if mission.mission_name == mission_name:
                return mission

        return None

    def get_same_category_mission_type_list(self, mission_type_name: str) -> list[CompendiumMissionType] | None:
        """
        获取与副本相同分类的全部列表
        """
        for tab in self.data.tab_list:
            for category in tab.category_list:
                for mission_type in category.mission_type_list:
                    if mission_type.mission_type_name == mission_type_name:
                        return category.mission_type_list

        return None

    def get_lost_void_mission_name_list(self) -> list[str]:
        """
        迷失之地的关卡名称列表
        :return:
        """
        mission_name_list: list[str] = []
        mission_list = self.get_mission_list_data('作战', '零号空洞', '迷失之地')
        for mission in mission_list:
            mission_name_list.append(mission.mission_name_display)
        return mission_name_list
