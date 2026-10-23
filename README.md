# zzz-lost-void

[English](README.en.md) | 简体中文

绝区零「迷失之地」全自动工具，附带战斗助手（自动战斗 / 闪避助手）。

拆分自 [ZenlessZoneZero-OneDragon](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon)（绝区零一条龙），只保留迷失之地和战斗助手，并重点优化了迷失之地的导航、选择和稳定性。

- **迷失之地**：自动进入并完成迷失之地（战线肃清 / 特遣调查 / 矩阵行动等），包括选预备编队、层间移动、选择鸣徽/武备、战斗。
- **战斗助手**：自动战斗、闪避助手，以及自动战斗配置模板和调试工具。

## 相比一条龙，迷失之地做了哪些优化

### 导航与移动

| 优化 | 做法 | 效果 |
|---|---|---|
| 单目深度避障 | 加入 Depth Anything V2 Small，把画面分成 16 列估计障碍距离；按「障碍深度 + 转向代价」选瞄准列，并优先往更空的一侧绕行 | 减少撞墙和来回摆动；首层首个房间实测少绕约 16 秒。仅在 GPU（CUDA / DirectML）上启用，无 GPU 自动关闭，不回退 CPU |
| 卡死检测与脱困 | 用场景静止帧差（1.5 s）加目标图标位置判断卡住；A/D 平移脱困，连续 2 次无效换边；单层累计 12 次放弃并重试 | 不再原地卡到超时 |
| Tab 地图路线规划 | 读取 Tab 地图，按区域类型优先级给路线打分，锁定已规划的入口，已访问类型的门不再重复进入 | 层内路线更稳定，减少绕路 |
| YOLO HUD 遮罩 | 检测前把头像、通知图标涂黑 | 减少把 HUD 误识别为目标 |

### 选择与资源

| 优化 | 做法 | 效果 |
|---|---|---|
| 鸣徽选择 | 优先级：同阵营 → NEW → 配置优先级 → 题库兜底 → 盲点；找不到同阵营时自动刷新 | 构筑更容易成型 |
| 邦布商店 | 刷新价 50/100/200/300，先刷约 3 次，之后把金币留给最后的休息区；始终保留购买鸣徽所需金币 | 避免金币刷光 |
| 战斗结束判定 | 每 0.8 s 用 OCR 读取距离提示判断战斗是否结束 | 战斗结束后立刻继续，不空等 |
| 运行记忆 | 本轮已用 NPC、已选项持久化到 `lost_void_run_memory.yml`；入口层交互前校验标签 | 重试时不重复交互 |

### 配置与可用性

- 计划刷取次数（1~99），到次数自动停止。
- 目标难度可选（难度一 ~ 六）；战线肃清可选「活性增幅」。
- GUI 精简为主页 / 迷失之地 / 战斗助手 / 资源管理 / 设置五个页面，并支持中文 / English 界面切换（设置 → 界面语言）。
- 提供导航采样工具，把每次运行的数据写入 `.debug/lost_void_navigation/`，便于调参。

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

本项目拆分自 [OneDragon-Anything/ZenlessZoneZero-OneDragon](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon)（上游提交 `9012d3e7`），保留了上游的通用框架（`one_dragon` / `one_dragon_qt` / `onnxocr`），只保留迷失之地和战斗助手，并把业务包 `zzz_od` 改名为 `zzz_lv`。其余差异：去掉了安装器、启动器、自动更新和遥测，免安装包改用自带 Python 的方式发布；自动化测试放在本仓 `tests/`。

按上游许可证要求，本项目同样以 [GPL-3.0](LICENSE) 发布，版权归上游原作者及本项目贡献者所有。`src/onnxocr/` 来自 [OnnxOCR](https://github.com/jingsongliujing/OnnxOCR)，使用 Apache-2.0 许可证，许可证原文见 [src/onnxocr/LICENSE](src/onnxocr/LICENSE)。
