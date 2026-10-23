"""测试公共 fixture。纯逻辑测试不需要模型和游戏；带 requires_models 标记的测试需要本地放置模型。"""
import pytest

from zzz_lv.application.hollow_zero.lost_void.lost_void_config import LostVoidConfig
from zzz_lv.application.hollow_zero.lost_void.lost_void_run_record import (
    LostVoidRunRecord,
)


class MemoryStore:
    """把 YamlConfig 的 get/update 换成内存字典，不读写磁盘"""

    def __init__(self) -> None:
        self.data: dict = {}

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def update(self, key: str, value) -> None:
        self.data[key] = value


@pytest.fixture
def lv_config(monkeypatch: pytest.MonkeyPatch) -> LostVoidConfig:
    store = MemoryStore()
    monkeypatch.setattr(LostVoidConfig, 'get', lambda self, key, default=None: store.get(key, default))
    monkeypatch.setattr(LostVoidConfig, 'update', lambda self, key, value: store.update(key, value))
    config = LostVoidConfig.__new__(LostVoidConfig)
    config.store = store
    return config


@pytest.fixture
def lv_run_record(monkeypatch: pytest.MonkeyPatch, lv_config: LostVoidConfig) -> LostVoidRunRecord:
    store = MemoryStore()
    monkeypatch.setattr(LostVoidRunRecord, 'get', lambda self, key, default=None: store.get(key, default))
    monkeypatch.setattr(LostVoidRunRecord, 'update', lambda self, key, value: store.update(key, value))
    record = LostVoidRunRecord.__new__(LostVoidRunRecord)
    record.config = lv_config
    return record
