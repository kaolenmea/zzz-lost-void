# zzz-lost-void

绝区零自动化工具，只包含两部分：

- **迷失之地**：自动进入并完成迷失之地（战线肃清 / 特遣调查 / 矩阵行动等），包括选预备编队、层间移动、选择鸣徽/武备、战斗。
- **战斗助手**：自动战斗、闪避助手，以及自动战斗配置模板和调试工具。

## 来源与许可证

本项目拆分自 [OneDragon-Anything/ZenlessZoneZero-OneDragon](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon)（上游提交 `9012d3e7`），保留了上游的通用框架（`one_dragon` / `one_dragon_qt` / `onnxocr`），删除了其他功能，并把业务包 `zzz_od` 改名为 `zzz_lv`。

按上游许可证要求，本项目同样以 [GPL-3.0](LICENSE) 发布，版权归上游原作者及本项目贡献者所有。

## 运行

只支持 Windows，游戏分辨率按 1920×1080 设计。

```powershell
# 1. 安装 uv: https://github.com/astral-sh/uv
winget install --id=astral-sh.uv -e

# 2. 安装依赖（uv 会自动准备 Python 3.11）
uv sync --group dev
# 需要手柄后台模式时再加上 gamepad 组
uv sync --group dev --group gamepad

# 3. 启动 GUI
copy .env.sample .env
uv run --env-file .env src/zzz_lv/gui/app.py
```

首次启动会提示下载 OCR、闪光识别、迷失之地识别模型（来自上游的模型发布仓库）。

## 与上游的差异

- 删除了体力计划、锄大地、式舆防卫战、枯萎之都、咖啡店、委托助手等其他功能。
- 删除了安装器、启动器、代码自动更新和打包脚本，只支持源码运行。
- 删除了遥测上报。
- 导航新增「迷失之地」页面，集中放运行、配置、挑战配置、预备编队。
- 上游测试（`zzz-od-test`）尚未迁移。

开发说明见 [docs/develop/README.md](docs/develop/README.md) 和 [AGENTS.md](AGENTS.md)。
