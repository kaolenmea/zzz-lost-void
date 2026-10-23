import zipfile
from pathlib import Path

import pytest

from one_dragon.utils import app_update_utils


@pytest.mark.parametrize(('latest', 'current', 'expected'), [
    ('1.1.3', '1.1.2', True),
    ('v1.2.0', '1.1.9', True),
    ('1.10.0', '1.9.0', True),
    ('1.1.2', '1.1.2', False),
    ('1.1.1', '1.1.2', False),
    ('1.1', '1.1.0', False),
    ('models', '1.1.2', False),
    ('1.1.3', 'dev', False),
])
def test_is_newer_version(latest: str, current: str, expected: bool) -> None:
    assert app_update_utils.is_newer_version(latest, current) is expected


@pytest.mark.parametrize(('url', 'expected'), [
    ('https://github.com/kaolenmea/zzz-lost-void', 'kaolenmea/zzz-lost-void'),
    ('https://github.com/kaolenmea/zzz-lost-void/', 'kaolenmea/zzz-lost-void'),
    ('https://github.com/kaolenmea/zzz-lost-void.git', 'kaolenmea/zzz-lost-void'),
    ('https://example.com/a', None),
    (None, None),
])
def test_get_repo_slug(url: str | None, expected: str | None) -> None:
    assert app_update_utils.get_repo_slug(url) == expected


def _release(tag: str, asset: str | None = None, **extra) -> dict:
    assets = []
    if asset is not None:
        assets.append({
            'name': asset,
            'browser_download_url': f'https://example.com/{asset}',
            'size': 100,
        })
    return {'tag_name': tag, 'body': f'notes {tag}', 'assets': assets, **extra}


def test_pick_latest_release_ignores_models_draft_prerelease() -> None:
    releases = [
        _release('models', 'models.zip'),
        _release('v1.3.0', 'ZZZLostVoid-v1.3.0.zip', draft=True),
        _release('v1.2.5', 'ZZZLostVoid-v1.2.5.zip', prerelease=True),
        _release('v1.1.2', 'ZZZLostVoid-v1.1.2.zip'),
        _release('v1.1.10', 'ZZZLostVoid-v1.1.10.zip'),
        _release('v1.2.0'),
    ]
    picked = app_update_utils.pick_latest_release(releases)
    assert picked is not None
    assert picked.version == '1.1.10'
    assert picked.asset_name == 'ZZZLostVoid-v1.1.10.zip'
    assert picked.notes == 'notes v1.1.10'


def test_pick_latest_release_none_when_no_package() -> None:
    assert app_update_utils.pick_latest_release([_release('models', 'models.zip')]) is None
    assert app_update_utils.pick_latest_release([]) is None


def _make_zip(path: Path, names: list[str]) -> None:
    with zipfile.ZipFile(path, 'w') as zf:
        for name in names:
            zf.writestr(name, 'x')


_FULL_PACKAGE = [
    'ZZZLostVoid/release.json',
    'ZZZLostVoid/ZZZLostVoid.exe',
    'ZZZLostVoid/python/python.exe',
    'ZZZLostVoid/src/a.py',
]


def test_extract_update_package_finds_root(tmp_path: Path) -> None:
    zip_path = tmp_path / 'p.zip'
    _make_zip(zip_path, _FULL_PACKAGE)
    root = app_update_utils.extract_update_package(zip_path, tmp_path / 'out')
    assert root is not None
    assert root.name == 'ZZZLostVoid'
    assert (root / 'src' / 'a.py').is_file()


def test_extract_update_package_rejects_incomplete(tmp_path: Path) -> None:
    zip_path = tmp_path / 'p.zip'
    _make_zip(zip_path, ['ZZZLostVoid/release.json'])
    with pytest.raises(ValueError, match='不完整'):
        app_update_utils.extract_update_package(zip_path, tmp_path / 'out')


def test_extract_update_package_rejects_path_escape(tmp_path: Path) -> None:
    zip_path = tmp_path / 'p.zip'
    _make_zip(zip_path, ['../evil.txt'])
    with pytest.raises(ValueError, match='非法路径'):
        app_update_utils.extract_update_package(zip_path, tmp_path / 'out')
    assert not (tmp_path / 'evil.txt').exists()


def test_extract_update_package_cancel(tmp_path: Path) -> None:
    zip_path = tmp_path / 'p.zip'
    _make_zip(zip_path, _FULL_PACKAGE)
    result = app_update_utils.extract_update_package(
        zip_path, tmp_path / 'out', cancel_signal={'signal': 'cancel'}
    )
    assert result is None


def test_build_update_script_escapes_quotes_and_orders_release_json() -> None:
    script = app_update_utils.build_update_script(
        pid=4321,
        root=Path("D:/it's/app"),
        package_root=Path('D:/it\'s/app/update/new/ZZZLostVoid'),
        log_path=Path('D:/it\'s/app/update/update.log'),
    )
    assert '$procId = 4321' in script
    assert "'D:\\it''s\\app'" in script or "'D:/it''s/app'" in script
    assert "Sync-Dir 'config' @('/E', '/XC', '/XN', '/XO')" in script
    assert "Sync-Dir 'python' @('/MIR')" in script
    # release.json 必须在其它文件同步完成后才写
    assert script.index("Sync-Dir 'src'") < script.index("'release.json') -Destination")
