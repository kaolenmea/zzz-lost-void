# zzz-lost-void

绝区零自动化工具，只包含两部分：

- **迷失之地**：自动进入并完成迷失之地（战线肃清 / 特遣调查 / 矩阵行动等），包括选预备编队、层间移动、选择鸣徽/武备、战斗。
- **战斗助手**：自动战斗、闪避助手，以及自动战斗配置模板和调试工具。

## 怎么用

### 普通用户：下载免安装包

1. 到 [Releases](https://github.com/kaolenmea/zzz-lost-void/releases) 下载最新的 `ZZZLostVoid-vX.Y.Z.zip`，完整解压到固定目录（路径尽量不要含中文和空格）。
2. 把游戏设置成 1920×1080 窗口或全屏，双击 `ZZZLostVoid.exe`（会弹出管理员权限申请，需要同意）。
3. 在「迷失之地」页选好刷取目标和计划刷取次数，点开始。

免安装包不需要装 Python，模型文件已经包含在里面。设置说明和常见问题见 [使用手册](docs/user/README.md)，打包方法见 [打包与发布](docs/develop/setup/release.md)。

### 开发者：从源码运行

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

# 4. 跑测试（不需要游戏和模型）
uv run --env-file .env pytest -m "not requires_models"
```

启动时如果不是管理员权限，会弹出 UAC 申请提权，确认后在新窗口中运行。游戏以管理员权限运行，普通权限程序的鼠标键盘操作会被系统拦截，所以必须提权。

首次从源码启动会提示下载 OCR、闪光识别、迷失之地识别模型（模型来自上游 [OneDragon-Env](https://github.com/OneDragon-Anything/OneDragon-Env) 的发布页）。

开发说明见 [docs/develop/README.md](docs/develop/README.md) 和 [AGENTS.md](AGENTS.md)。

## 免责声明

- 本项目仅供学习交流使用，使用本工具产生的一切风险由使用者自行承担。
- 本项目没有授权任何个人、商家、自媒体账号售卖本软件。如果你是花钱得到的，请注意被骗。
- 若遇到商家使用本软件代练并收费，由此产生的问题和后果与本项目无关。
- 开发者不提供任何「售后」服务。

## 来源与许可证

本项目拆分自 [OneDragon-Anything/ZenlessZoneZero-OneDragon](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon)（上游提交 `9012d3e7`），保留了上游的通用框架（`one_dragon` / `one_dragon_qt` / `onnxocr`），删除了其他功能，并把业务包 `zzz_od` 改名为 `zzz_lv`。

按上游许可证要求，本项目同样以 [GPL-3.0](LICENSE) 发布，版权归上游原作者及本项目贡献者所有。`src/onnxocr/` 来自 [OnnxOCR](https://github.com/jingsongliujing/OnnxOCR)，使用 Apache-2.0 许可证，许可证原文见 [src/onnxocr/LICENSE](src/onnxocr/LICENSE)。

## 与上游的差异

- 删除了体力计划、锄大地、式舆防卫战、枯萎之都、咖啡店、委托助手等其他功能。
- 删除了安装器、启动器和代码自动更新；免安装包改用自带 Python 的方式发布。
- 删除了遥测上报。
- 删除了迷失之地的 AI 决策功能，周期增益固定选第二个。
- 新增「计划刷取次数」（1~99 次，到次数自动停止）和战线肃清的「活性增幅」选择。
- 精简 GUI 导航：只保留主页、迷失之地、战斗助手、资源管理、设置（开发工具只在开发者模式下显示）；去掉一条龙、应用运行、账户管理页面。
- 迷失之地运行页集中放常用配置和「结束后」动作；未打开游戏时会按「设置 → 游戏设置」里的游戏路径自动启动并进入游戏。
- 自动化测试放在本仓 `tests/`，上游独立的测试仓 `zzz-od-test` 尚未迁移。
