import json
import re
import shutil
import subprocess
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from one_dragon.utils.log_utils import log

# release tag 只认 v1.2.3 这种格式 这样仓库里别的 Release（如放模型的 models）不会被当成程序版本
_VERSION_PATTERN = re.compile(r'^v?(\d+(?:\.\d+)*)$')
# 发布包的文件名 与 packaging/build.ps1 生成的名字一致
_ASSET_PATTERN = re.compile(r'^ZZZLostVoid-v.+\.zip$')
_REPO_PATTERN = re.compile(r'github\.com/([^/\s]+/[^/\s]+?)(?:\.git)?/?$')

# 解压后的包里必须有这些文件 缺了说明包不完整 不能用来覆盖
_REQUIRED_PACKAGE_ENTRIES: tuple[str, ...] = (
    'release.json',
    'ZZZLostVoid.exe',
    'python',
    'src',
)

_CREATE_NO_WINDOW = 0x08000000
_CREATE_NEW_PROCESS_GROUP = 0x00000200


@dataclass(frozen=True, slots=True)
class AppRelease:
    """GitHub 上的一个程序版本。"""

    version: str
    notes: str
    asset_name: str
    download_url: str
    size: int


def parse_version(text: str | None) -> tuple[int, ...] | None:
    """把 v1.2.3 / 1.2.3 解析成数字元组，格式不对返回 None。"""
    if not text:
        return None
    match = _VERSION_PATTERN.match(text.strip())
    if match is None:
        return None
    return tuple(int(part) for part in match.group(1).split('.'))


def is_newer_version(latest: str, current: str) -> bool:
    """latest 是否比 current 新，任意一个解析失败都返回 False。"""
    latest_parts = parse_version(latest)
    current_parts = parse_version(current)
    if latest_parts is None or current_parts is None:
        return False
    length = max(len(latest_parts), len(current_parts))
    latest_parts += (0,) * (length - len(latest_parts))
    current_parts += (0,) * (length - len(current_parts))
    return latest_parts > current_parts


def get_repo_slug(github_homepage: str | None) -> str | None:
    """从 https://github.com/owner/repo 取出 owner/repo。"""
    if not github_homepage:
        return None
    match = _REPO_PATTERN.search(github_homepage.strip())
    return match.group(1) if match else None


def pick_latest_release(releases: list[dict]) -> AppRelease | None:
    """从 GitHub Release 列表里选出版本号最大、带发布包的正式版本。"""
    best: tuple[tuple[int, ...], AppRelease] | None = None
    for item in releases:
        if not isinstance(item, dict) or item.get('draft') or item.get('prerelease'):
            continue
        tag = str(item.get('tag_name') or '')
        parts = parse_version(tag)
        if parts is None:
            continue
        for asset in item.get('assets') or []:
            name = str(asset.get('name') or '')
            url = str(asset.get('browser_download_url') or '')
            if not _ASSET_PATTERN.match(name) or not url:
                continue
            release = AppRelease(
                version=tag.lstrip('vV'),
                notes=str(item.get('body') or ''),
                asset_name=name,
                download_url=url,
                size=int(asset.get('size') or 0),
            )
            if best is None or parts > best[0]:
                best = (parts, release)
            break
    return best[1] if best is not None else None


def fetch_latest_release(repo_slug: str, timeout: float = 10) -> AppRelease | None:
    """请求 GitHub 取最新的程序版本；网络失败时抛出异常，由调用方决定怎么处理。"""
    url = f'https://api.github.com/repos/{repo_slug}/releases?per_page=20'
    request = urllib.request.Request(
        url,
        headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'zzz-lost-void'},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        releases = json.loads(response.read().decode('utf-8'))
    if not isinstance(releases, list):
        return None
    return pick_latest_release(releases)


def find_package_root(extract_dir: Path) -> Path | None:
    """在解压目录里找到发布包根目录（含 release.json 的那一层）。"""
    if (extract_dir / 'release.json').is_file():
        return extract_dir
    for child in extract_dir.iterdir():
        if child.is_dir() and (child / 'release.json').is_file():
            return child
    return None


def validate_package_root(package_root: Path) -> list[str]:
    """返回包里缺少的必要文件，空列表表示完整。"""
    return [name for name in _REQUIRED_PACKAGE_ENTRIES if not (package_root / name).exists()]


def extract_update_package(
    zip_path: Path,
    extract_dir: Path,
    progress_callback: Callable[[float], None] | None = None,
    cancel_signal: dict[str, str | None] | None = None,
) -> Path | None:
    """解压发布包并检查完整性。

    Returns:
        包根目录；被取消时返回 None。

    Raises:
        ValueError: 压缩包里有越界路径，或缺少必要文件。
    """
    extract_dir.mkdir(parents=True, exist_ok=True)
    base = extract_dir.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        members = zf.infolist()
        for index, member in enumerate(members):
            if cancel_signal is not None and cancel_signal.get('signal') == 'cancel':
                return None
            target = (base / member.filename).resolve()
            if target != base and base not in target.parents:
                raise ValueError(f'压缩包含有非法路径: {member.filename}')
            zf.extract(member, base)
            if progress_callback is not None and index % 200 == 0:
                progress_callback((index + 1) / len(members))
    if progress_callback is not None:
        progress_callback(1)

    package_root = find_package_root(base)
    if package_root is None:
        raise ValueError('更新包里找不到 release.json')
    missing = validate_package_root(package_root)
    if missing:
        raise ValueError(f'更新包不完整，缺少: {", ".join(missing)}')
    return package_root


def _ps_quote(text: str) -> str:
    """转成 PowerShell 单引号字符串。"""
    return "'" + text.replace("'", "''") + "'"


def build_update_script(pid: int, root: Path, package_root: Path, log_path: Path) -> str:
    """生成更新脚本：等程序退出 → 用新包覆盖 → 重新启动。

    覆盖规则:
    - python、src: 镜像同步，删掉新版本里已不存在的旧文件（src 里残留的旧应用文件会被程序当成应用加载）。
    - assets、plugins: 只覆盖和新增，不删文件（用户的自定义背景图在 assets/ui 下）。
    - config: 只补充新增的文件，已有的配置文件不动。
    - 根目录文件: 直接覆盖，release.json 最后写，没写成功下次启动还会提示更新。
    """
    return f"""$ErrorActionPreference = 'Continue'
$procId = {pid}
$root = {_ps_quote(str(root))}
$pkg = {_ps_quote(str(package_root))}
$log = {_ps_quote(str(log_path))}
$failed = $false

function Write-Log($msg) {{
    Add-Content -LiteralPath $log -Value ("[{{0}}] {{1}}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg) -Encoding UTF8
}}

function Sync-Dir($name, $flags) {{
    $src = Join-Path $pkg $name
    if (-not (Test-Path -LiteralPath $src)) {{ return }}
    $dst = Join-Path $root $name
    robocopy $src $dst @flags /R:5 /W:2 /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) {{
        Write-Log "同步 $name 失败，robocopy 退出码 $LASTEXITCODE"
        $script:failed = $true
    }} else {{
        Write-Log "已同步 $name"
    }}
}}

Write-Log '等待程序退出'
Wait-Process -Id $procId -Timeout 120 -ErrorAction SilentlyContinue
if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {{
    Write-Log '程序没有在 120 秒内退出，放弃更新'
    $failed = $true
}}
Start-Sleep -Seconds 2

if (-not $failed) {{
    Sync-Dir 'python' @('/MIR')
    Sync-Dir 'src' @('/MIR')
    Sync-Dir 'assets' @('/E')
    Sync-Dir 'plugins' @('/E')
    Sync-Dir 'config' @('/E', '/XC', '/XN', '/XO')
    foreach ($file in Get-ChildItem -LiteralPath $pkg -File | Where-Object {{ $_.Name -ne 'release.json' }}) {{
        try {{
            Copy-Item -LiteralPath $file.FullName -Destination $root -Force -ErrorAction Stop
        }} catch {{
            Write-Log "复制 $($file.Name) 失败: $_"
            $failed = $true
        }}
    }}
}}
if (-not $failed) {{
    try {{
        Copy-Item -LiteralPath (Join-Path $pkg 'release.json') -Destination $root -Force -ErrorAction Stop
        Write-Log '更新完成'
    }} catch {{
        Write-Log "写入 release.json 失败: $_"
        $failed = $true
    }}
}}

if ($failed) {{
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("更新失败，详情见: $log`n可以到 GitHub Release 页面手动下载完整包。", 'ZZZ Lost Void', 'OK', 'Error') | Out-Null
}} else {{
    Remove-Item -LiteralPath $pkg -Recurse -Force -ErrorAction SilentlyContinue
}}

Start-Process -FilePath (Join-Path $root 'ZZZLostVoid.exe') -WorkingDirectory $root
"""


def launch_update_script(script_path: Path) -> None:
    """后台启动更新脚本；调用后当前程序应立刻退出。"""
    subprocess.Popen(
        [
            'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
            '-WindowStyle', 'Hidden', '-File', str(script_path),
        ],
        creationflags=_CREATE_NO_WINDOW | _CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )


def clean_update_dir(update_dir: Path) -> None:
    """清掉上一次留下的更新文件。"""
    if update_dir.exists():
        shutil.rmtree(update_dir, ignore_errors=True)
    update_dir.mkdir(parents=True, exist_ok=True)
    log.info(f'更新目录已清理: {update_dir}')
