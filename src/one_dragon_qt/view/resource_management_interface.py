from collections.abc import Callable

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QWidget
from qfluentwidgets import (
    FluentIcon,
    PushButton,
    SettingCardGroup,
)

from one_dragon.base.config.basic_model_config import (
    get_ocr_opts,
)
from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.base.web.common_downloader import CommonDownloaderParam
from one_dragon.base.web.zip_downloader import ZipDownloader
from one_dragon.envs.env_config import ProxyTypeEnum
from one_dragon.envs.repo_config import ModelResourceDefinition
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from one_dragon_qt.services.download_queue_service import (
    DownloadQueueService,
    ResourceDownloadSpec,
)
from one_dragon_qt.widgets.column import Column
from one_dragon_qt.widgets.download_card.onnx_model_download_card import (
    OnnxModelDownloadCard,
)
from one_dragon_qt.widgets.resource_download_dialog import (
    build_resource_source_options,
)
from one_dragon_qt.widgets.setting_card.combo_box_setting_card import (
    ComboBoxSettingCard,
)
from one_dragon_qt.widgets.setting_card.expand_setting_card_group import (
    ExpandSettingCardGroup,
)
from one_dragon_qt.widgets.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon_qt.widgets.setting_card.text_setting_card import TextSettingCard
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface


class OcrReloadRunner(QThread):
    """后台重新初始化 OCR 模型 避免下载与加载阻塞界面线程。"""

    def __init__(self, ctx: OneDragonContext):
        super().__init__()
        self.ctx: OneDragonContext = ctx

    def run(self) -> None:
        try:
            self.ctx.init_ocr()
        except Exception:
            log.error('后台重新加载 OCR 模型失败', exc_info=True)



class ResourceManagementInterface(VerticalScrollInterface):

    def __init__(
        self,
        ctx: OneDragonContext,
        download_queue: DownloadQueueService,
        parent: QWidget | None = None,
    ) -> None:
        self.ctx: OneDragonContext = ctx
        self.download_queue: DownloadQueueService = download_queue
        self._last_proxy_type: str = ctx.env_config.proxy_type

        VerticalScrollInterface.__init__(
            self,
            content_widget=None,
            object_name='resource_management_interface',
            parent=parent,
            nav_text_cn='资源管理', nav_icon=FluentIcon.SYNC
        )

    def get_content_widget(self) -> QWidget:
        content_widget = Column(spacing=20)
        content_widget.setMaximumWidth(1180)
        content_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        content_widget.v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._add_resource_content(content_widget)

        page_widget = QWidget()
        page_layout = QHBoxLayout(page_widget)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addStretch(1)
        page_layout.addWidget(content_widget, stretch=100)
        page_layout.addStretch(1)
        return page_widget

    def _add_resource_content(self, content_widget: Column) -> None:
        """添加框架通用资源和项目资源。"""
        self.download_settings_group = SettingCardGroup('下载设置')
        self.resource_source_opt = ComboBoxSettingCard(
            icon=FluentIcon.GLOBE,
            title='下载源',
            content='自动模式优先使用上次成功源，失败后继续尝试其他源',
            options_list=build_resource_source_options(self.ctx.env_config),
        )
        self.resource_source_opt.combo_box.setFixedWidth(160)
        self.download_settings_group.addSettingCard(self.resource_source_opt)

        self.proxy_group = ExpandSettingCardGroup(
            icon=FluentIcon.WIFI,
            title='代理设置',
            content='为资源下载配置网络代理',
        )
        self.proxy_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.GLOBE,
            title='代理类型',
            options_enum=ProxyTypeEnum,
        )
        self.proxy_type_opt.value_changed.connect(
            self._on_proxy_type_changed
        )
        self.proxy_group.addHeaderWidget(self.proxy_type_opt.combo_box)

        self.proxy_url_input = TextSettingCard(
            icon=FluentIcon.WIFI,
            title='代理地址',
            input_max_width=300,
        )
        self.proxy_url_input.line_edit.setFixedWidth(300)
        self.proxy_url_input.value_changed.connect(
            lambda _value: self.ctx.env_config.init_system_proxy()
        )
        self.proxy_group.addSettingCard(self.proxy_url_input)

        self.auto_fetch_proxy_opt = SwitchSettingCard(
            icon=FluentIcon.SYNC,
            title='自动获取免费代理地址',
            content='仅在使用 GitHub 代理时生效',
            on_text_cn='',
            off_text_cn='',
        )
        self.fetch_proxy_btn = PushButton(gt('立即获取'), self)
        self.fetch_proxy_btn.setFixedWidth(112)
        self.fetch_proxy_btn.clicked.connect(self._fetch_proxy_url)
        self.auto_fetch_proxy_opt.hBoxLayout.addWidget(
            self.fetch_proxy_btn,
            0,
            Qt.AlignmentFlag.AlignRight,
        )
        self.auto_fetch_proxy_opt.hBoxLayout.addSpacing(16)
        self.proxy_group.addSettingCard(self.auto_fetch_proxy_opt)
        self.download_settings_group.addSettingCard(self.proxy_group)

        self.auto_download_opt = SwitchSettingCard(
            icon=FluentIcon.DOWNLOAD,
            title='资源自动下载',
            content='发现资源缺失或有新版本时，跳过确认并自动下载',
            on_text_cn='',
            off_text_cn='',
        )
        self.download_settings_group.addSettingCard(self.auto_download_opt)
        content_widget.add_widget(self.download_settings_group)

        self.download_items_group = SettingCardGroup('更新与下载')
        self.ocr_opt = self._create_model_card(
            title='OCR识别',
            options=get_ocr_opts(),
            current_getter=lambda: self.ctx.model_config.ocr,
            config_key='ocr',
            resource_id='ocr',
        )
        self.ocr_opt.gpu_changed.connect(self._on_ocr_gpu_changed)
        self.download_items_group.addSettingCard(self.ocr_opt)

        self._add_model_resource_cards(self.download_items_group)
        content_widget.add_widget(self.download_items_group)

    def _add_model_resource_cards(
        self,
        group: SettingCardGroup,
    ) -> None:
        """按项目模型配置声明自动创建全部模型卡片。"""
        self.model_resource_cards: dict[str, OnnxModelDownloadCard] = {}
        for resource in self.ctx.model_config.get_model_resources():
            def current_getter(
                selected: ModelResourceDefinition = resource,
            ) -> str:
                return self.ctx.model_config.get_model_current(selected)

            card = self._create_model_card(
                title=resource.display_name,
                options=self.ctx.model_config.get_model_options(resource),
                current_getter=current_getter,
                config_key=resource.config_key,
                resource_id=resource.config_key,
            )
            self._bind_model_gpu_option(card, resource)
            self.model_resource_cards[resource.config_key] = card
            group.addSettingCard(card)

    def _bind_model_gpu_option(
        self,
        card: OnnxModelDownloadCard,
        resource: ModelResourceDefinition,
    ) -> None:
        """按声明绑定模型 GPU 配置；未声明时隐藏开关。"""
        if resource.gpu_config_key is None:
            card.gpu_opt.hide()
            return
        card.gpu_changed.connect(
            lambda value, key=resource.gpu_config_key: (
                self.ctx.model_config.update(key, value)
            )
        )

    def _on_proxy_type_changed(
        self,
        _index: int,
        _value: str,
    ) -> None:
        """代理类型变化后刷新输入项并应用系统代理。"""
        proxy_type = self.ctx.env_config.proxy_type
        self._update_proxy_ui()
        if (
            self._last_proxy_type == ProxyTypeEnum.NONE.value.value
            and proxy_type != ProxyTypeEnum.NONE.value.value
        ):
            self.proxy_group.setExpand(True)
        self._last_proxy_type = proxy_type
        self.ctx.env_config.init_system_proxy()

    def _update_proxy_ui(self) -> None:
        """按后端代理类型绑定对应地址配置。"""
        proxy_type = self.ctx.env_config.proxy_type
        proxy_enabled = proxy_type != ProxyTypeEnum.NONE.value.value
        if not proxy_enabled:
            self.proxy_group.setExpand(False)
        self.proxy_group.card.expandButton.setEnabled(proxy_enabled)

        if proxy_type == ProxyTypeEnum.PERSONAL.value.value:
            self.proxy_url_input.init_with_adapter(
                self.ctx.env_config.get_prop_adapter('personal_proxy')
            )
            self.proxy_url_input.titleLabel.setText(gt('个人代理地址'))
            self.proxy_url_input.line_edit.setPlaceholderText(
                'http://127.0.0.1:7890'
            )
            self.proxy_url_input.setVisible(True)
            self.auto_fetch_proxy_opt.setVisible(False)
        elif proxy_type == ProxyTypeEnum.GHPROXY.value.value:
            self.proxy_url_input.init_with_adapter(
                self.ctx.env_config.get_prop_adapter('gh_proxy_url')
            )
            self.proxy_url_input.titleLabel.setText(gt('免费代理地址'))
            self.proxy_url_input.line_edit.setPlaceholderText(
                'https://ghproxy.link/'
            )
            self.proxy_url_input.setVisible(True)
            self.auto_fetch_proxy_opt.setVisible(True)
        else:
            self.proxy_url_input.setVisible(False)
            self.auto_fetch_proxy_opt.setVisible(False)

    def _fetch_proxy_url(self) -> None:
        """立即获取免费代理地址并刷新输入框。"""
        self.ctx.gh_proxy_service.update_proxy_url()
        self.proxy_url_input.init_with_adapter(
            self.ctx.env_config.get_prop_adapter('gh_proxy_url')
        )
        self.ctx.env_config.init_system_proxy()

    def _create_model_card(
        self,
        title: str,
        options: list[ConfigItem],
        current_getter: Callable[[], str],
        config_key: str,
        resource_id: str,
    ) -> OnnxModelDownloadCard:
        """创建接入下载队列的模型卡片。"""
        card = OnnxModelDownloadCard(
            ctx=self.ctx,
            icon=FluentIcon.GLOBE,
            title=title,
        )
        card.set_options_by_list(options)
        card.set_active_value_getter(current_getter)
        card.set_value_by_save_file_name(f'{current_getter()}.zip')
        card.value_changed.connect(
            lambda _index, param, key=config_key: self._switch_existing_model(
                key,
                param,
            )
        )
        card.use_download_queue(
            self.download_queue,
            lambda c=card, key=config_key, rid=resource_id, name=title: (
                self._build_model_spec(c, key, rid, name)
            ),
        )
        return card

    def _build_model_spec(
        self,
        card: OnnxModelDownloadCard,
        config_key: str,
        resource_id: str,
        title: str,
    ) -> ResourceDownloadSpec:
        """根据模型卡片当前选项构造队列任务。"""
        param: CommonDownloaderParam = card.getValue()
        target = param.save_file_name.removesuffix('.zip')
        current = str(self.ctx.model_config.get(config_key, ''))
        return ResourceDownloadSpec(
            resource_id=resource_id,
            resource_type='model',
            title=title,
            current_version=current,
            target_version=target,
            downloader_factory=lambda selected=param: ZipDownloader(selected),
            after_download=(
                lambda success, key=config_key, value=target: (
                    self._after_model_download(success, key, value)
                )
            ),
        )


    def _switch_existing_model(
        self,
        config_key: str,
        param: CommonDownloaderParam,
    ) -> None:
        """仅在模型已经存在时立即切换配置。"""
        downloader = ZipDownloader(param)
        if downloader.is_file_existed():
            self.ctx.model_config.update(
                config_key,
                param.save_file_name.removesuffix('.zip'),
            )

    def _after_model_download(
        self,
        success: bool,
        config_key: str,
        target: str,
    ) -> None:
        """模型下载成功后切换配置。"""
        if success:
            self.ctx.model_config.update(config_key, target)
            if config_key == 'ocr':
                self.ctx.init_ocr()

    def _on_ocr_gpu_changed(self, value: bool) -> None:
        """更新 OCR GPU 配置。"""
        previous = self.ctx.model_config.ocr_use_gpu
        self.ctx.model_config.ocr_use_gpu = value
        # 重新初始化 OCR 可能触发下载和模型加载 放到后台避免卡住界面
        self._ocr_reload_runner = OcrReloadRunner(self.ctx)
        self._ocr_reload_runner.finished.connect(
            lambda: self._on_ocr_reload_finished(previous, value)
        )
        self._ocr_reload_runner.start()

    def _on_ocr_reload_finished(self, previous: bool, requested: bool) -> None:
        """OCR 后台重载结束后恢复界面状态。"""
        ocr = self.ctx.ocr
        if ocr is None or ocr._model is None:
            # 加载失败 回滚开关和配置 避免界面显示与实际引擎不一致
            if previous != requested:
                self.ctx.model_config.ocr_use_gpu = previous
                self.ocr_opt.gpu_opt.setChecked(previous)

    def on_interface_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        VerticalScrollInterface.on_interface_shown(self)
        self.resource_source_opt.init_with_adapter(
            self.ctx.env_config.get_prop_adapter('resource_source')
        )
        self.proxy_type_opt.init_with_adapter(
            self.ctx.env_config.get_prop_adapter('proxy_type')
        )
        self.auto_fetch_proxy_opt.init_with_adapter(
            self.ctx.env_config.get_prop_adapter(
                'auto_fetch_gh_proxy_url'
            )
        )
        self._update_proxy_ui()
        self.auto_download_opt.init_with_adapter(
            self.ctx.env_config.get_prop_adapter(
                'resource_download_no_confirm'
            )
        )
        self.ocr_opt.gpu_opt.setChecked(self.ctx.model_config.ocr_use_gpu)
        for resource in self.ctx.model_config.get_model_resources():
            if resource.gpu_config_key is None:
                continue
            card = self.model_resource_cards.get(resource.config_key)
            if card is not None:
                card.gpu_opt.setChecked(
                    bool(
                        self.ctx.model_config.get(
                            resource.gpu_config_key,
                            False,
                        )
                    )
                )
