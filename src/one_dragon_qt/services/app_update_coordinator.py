import os
import shutil
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget
from qfluentwidgets import (
    BodyLabel,
    MessageBoxBase,
    ProgressBar,
    SubtitleLabel,
    TextEdit,
)

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon.utils import app_update_utils, http_utils, os_utils
from one_dragon.utils.app_update_utils import AppRelease
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log

# 下载 + 解压 + 覆盖期间同时存在 zip 和解压后的文件，至少要留出的磁盘空间
_MIN_FREE_BYTES: int = 3 * 1024 ** 3


class _CheckRunner(QThread):
    """后台查询 GitHub 上的最新版本，失败只记日志，不打扰用户。"""

    found = Signal(object)

    def __init__(self, repo_slug: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._repo_slug: str = repo_slug

    def run(self) -> None:
        release: AppRelease | None = None
        try:
            release = app_update_utils.fetch_latest_release(self._repo_slug)
        except Exception:
            log.info('检查程序更新失败', exc_info=True)
        self.found.emit(release)


class _UpdateWorker(QThread):
    """下载并解压更新包。"""

    progress = Signal(float, str)
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        release: AppRelease,
        update_dir: Path,
        proxy: str | None,
        gh_proxy_url: str | None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._release: AppRelease = release
        self._update_dir: Path = update_dir
        self._proxy: str | None = proxy
        self._gh_proxy_url: str | None = gh_proxy_url
        self.cancel_signal: dict[str, str | None] = {'signal': None}

    def cancel(self) -> None:
        self.cancel_signal['signal'] = 'cancel'

    def run(self) -> None:
        try:
            self._update_dir.mkdir(parents=True, exist_ok=True)
            free = shutil.disk_usage(self._update_dir).free
            if free < _MIN_FREE_BYTES:
                self.failed.emit(f'{gt("磁盘空间不足，至少需要")} {_MIN_FREE_BYTES // 1024 ** 3} GB')
                return

            zip_path = self._update_dir / 'package.zip'
            url = self._release.download_url
            if self._gh_proxy_url:
                url = f'{self._gh_proxy_url.rstrip("/")}/{url}'
            ok = http_utils.download_file(
                url,
                str(zip_path),
                proxy=self._proxy,
                progress_signal=self.cancel_signal,
                progress_callback=lambda p, msg: self.progress.emit(p * 0.9, msg),
            )
            if not ok:
                if self.cancel_signal['signal'] != 'cancel':
                    self.failed.emit(gt('下载失败，请检查网络或在资源管理里设置代理'))
                return

            self.progress.emit(0.9, gt('正在解压'))
            package_root = app_update_utils.extract_update_package(
                zip_path,
                self._update_dir / 'new',
                progress_callback=lambda p: self.progress.emit(0.9 + p * 0.1, gt('正在解压')),
                cancel_signal=self.cancel_signal,
            )
            zip_path.unlink(missing_ok=True)
            if package_root is None:
                return
            self.succeeded.emit(package_root)
        except Exception as e:
            log.error('下载更新包失败', exc_info=True)
            self.failed.emit(str(e))


class AppUpdateDialog(MessageBoxBase):
    """展示新版本信息，用户确认后开始更新。"""

    def __init__(self, release: AppRelease, current_version: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.yesButton.setText(gt('立即更新'))
        self.cancelButton.setText(gt('稍后'))

        self.viewLayout.addWidget(SubtitleLabel(gt('发现新版本')))
        self.viewLayout.addSpacing(8)
        self.viewLayout.addWidget(BodyLabel(f'v{current_version} → v{release.version}'))
        size_mb = release.size / 1024 / 1024
        self.viewLayout.addWidget(BodyLabel(f'{gt("下载大小")} {size_mb:.0f} MB'))
        if release.notes.strip():
            notes = TextEdit()
            notes.setReadOnly(True)
            notes.setPlainText(release.notes.strip())
            notes.setFixedHeight(180)
            self.viewLayout.addSpacing(8)
            self.viewLayout.addWidget(notes)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addWidget(BodyLabel(gt('更新会关闭程序，完成后自动重新启动；配置不会丢失。')))
        self.widget.setMinimumWidth(520)


class _ProgressDialog(MessageBoxBase):
    """下载进度弹窗，只提供取消。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.yesButton.hide()
        self.cancelButton.setText(gt('取消'))
        self.viewLayout.addWidget(SubtitleLabel(gt('正在更新')))
        self.viewLayout.addSpacing(8)
        self.message_label = BodyLabel(gt('正在连接'))
        self.viewLayout.addWidget(self.message_label)
        self.bar = ProgressBar()
        self.bar.setRange(0, 1000)
        self.viewLayout.addWidget(self.bar)
        self.widget.setMinimumWidth(480)

    def set_progress(self, value: float, message: str) -> None:
        self.bar.setValue(int(max(0.0, min(1.0, value)) * 1000))
        self.message_label.setText(message)


class AppUpdateCoordinator(QObject):
    """程序自身的更新：启动时查 GitHub Release，有新版本就让用户一键更新。

    只有免安装发布包（根目录有 release.json）才会检查，源码运行不更新。
    """

    def __init__(self, ctx: OneDragonEnvContext, parent_window: QWidget) -> None:
        super().__init__(parent_window)
        self.ctx: OneDragonEnvContext = ctx
        self._window: QWidget = parent_window
        self._checker: _CheckRunner | None = None
        self._worker: _UpdateWorker | None = None
        self._progress_dialog: _ProgressDialog | None = None

    def check(self) -> None:
        """后台检查是否有新版本，每次启动调用一次。"""
        if self._checker is not None or self._worker is not None:
            return
        current = os_utils.get_release_version()
        repo_slug = app_update_utils.get_repo_slug(self.ctx.project_config.github_homepage)
        if current is None or repo_slug is None:
            return
        self._checker = _CheckRunner(repo_slug, self)
        self._checker.found.connect(self._on_checked)
        self._checker.start()

    def _on_checked(self, release: AppRelease | None) -> None:
        self._checker = None
        current = os_utils.get_release_version()
        if release is None or current is None:
            return
        if not app_update_utils.is_newer_version(release.version, current):
            log.info(f'程序已是最新版本: v{current}')
            return
        log.info(f'发现新版本: v{current} → v{release.version}')
        dialog = AppUpdateDialog(release, current, self._window)
        if dialog.exec():
            self._start_update(release)

    def _start_update(self, release: AppRelease) -> None:
        env_config = self.ctx.env_config
        update_dir = Path(os_utils.get_work_dir()) / 'update'
        app_update_utils.clean_update_dir(update_dir)

        self._worker = _UpdateWorker(
            release,
            update_dir,
            proxy=env_config.personal_proxy if env_config.is_personal_proxy else None,
            gh_proxy_url=env_config.gh_proxy_url if env_config.is_gh_proxy else None,
            parent=self,
        )
        self._progress_dialog = _ProgressDialog(self._window)
        self._worker.progress.connect(self._progress_dialog.set_progress)
        self._worker.succeeded.connect(self._on_download_succeeded)
        self._worker.failed.connect(self._on_download_failed)
        self._progress_dialog.cancelButton.clicked.connect(self._worker.cancel)
        self._worker.start()
        self._progress_dialog.exec()

        # 弹窗被关掉（取消）时等线程收尾
        worker = self._worker
        self._worker = None
        self._progress_dialog = None
        if worker is not None and worker.isRunning():
            worker.cancel()
            worker.wait(10000)

    def _on_download_failed(self, message: str) -> None:
        if self._progress_dialog is not None:
            self._progress_dialog.reject()
        QMessageBox.warning(self._window, gt('更新失败'), message)

    def _on_download_succeeded(self, package_root: Path) -> None:
        if self._progress_dialog is not None:
            self._progress_dialog.accept()
        update_dir = Path(os_utils.get_work_dir()) / 'update'
        script_path = update_dir / 'apply_update.ps1'
        script = app_update_utils.build_update_script(
            pid=os.getpid(),
            root=Path(os_utils.get_work_dir()),
            package_root=package_root,
            log_path=update_dir / 'update.log',
        )
        # 带 BOM，Windows PowerShell 才能正确读中文
        script_path.write_text(script, encoding='utf-8-sig')
        try:
            app_update_utils.launch_update_script(script_path)
        except OSError as e:
            log.error('启动更新脚本失败', exc_info=True)
            QMessageBox.warning(self._window, gt('更新失败'), str(e))
            return
        log.info('更新包已就绪，退出程序以应用更新')
        QApplication.quit()
