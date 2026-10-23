import json
from pathlib import Path

import pytest

from one_dragon.utils import os_utils


@pytest.fixture
def work_dir(tmp_path: Path):
    os_utils.set_work_dir(tmp_path)
    yield tmp_path
    os_utils.set_work_dir(None)


def test_no_release_file_is_not_release_build(work_dir: Path) -> None:
    assert os_utils.get_release_version() is None


def test_release_version_is_read(work_dir: Path) -> None:
    (work_dir / 'release.json').write_text(json.dumps({'version': '1.0.0', 'commit': 'abc'}), encoding='utf-8')
    assert os_utils.get_release_version() == '1.0.0'


@pytest.mark.parametrize('content', ['not json', '[]', '{}', '{"version": ""}'])
def test_broken_release_file_is_not_release_build(work_dir: Path, content: str) -> None:
    (work_dir / 'release.json').write_text(content, encoding='utf-8')
    assert os_utils.get_release_version() is None
