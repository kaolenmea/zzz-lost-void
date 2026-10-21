from one_dragon.base.config.yaml_config import YamlConfig


class ProjectConfig(YamlConfig):

    def __init__(self, prefer_bundled_config: bool = False) -> None:
        YamlConfig.__init__(
            self,
            module_name='project',
            prefer_bundled_config=prefer_bundled_config,
        )

        self.project_name = self.get('project_name')
        self.python_version = self.get('python_version')
        self.github_homepage = self.get('github_homepage')
        self.env_archive_name = f'{self.project_name}-Environment.zip'
        self.game_executable_name = self.get('game_executable_name', '')

        self.screen_standard_width = int(self.get('screen_standard_width'))
        self.screen_standard_height = int(self.get('screen_standard_height'))
