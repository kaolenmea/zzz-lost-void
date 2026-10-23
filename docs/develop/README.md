# 开发指南

> `docs/develop/` 的入口与索引。开发环境与流程见 §1–§2；各类专题文档按下索引查阅。

## 文档索引

- **开发环境与工具**：[快速开始](setup/quickstart.md) · [相关仓库](setup/repositories.md) · [AI 编码助手接入](setup/ai_coding.md) · [打包与发布](setup/release.md)
- **编码规范**：[agent_guidelines.md](spec/agent_guidelines.md)
- **开发流程**：[端到端开发流程](development_workflow.md)
- **架构设计**：[一条龙整体架构](one_dragon/one_dragon_architecture.md) · [资源下载源与候选回退](one_dragon/modules/resource_download.md) · [项目工作目录](one_dragon/modules/work_directory.md) · [模块文档](one_dragon/modules/)
- **开发指引**：[应用插件开发](guides/application_plugin_guide.md) · [应用设置界面](guides/application_setting_guide.md)
- **GUI**：[界面结构与设置分级](zzz/gui_layout.md)
- **游戏业务**：[自动战斗](zzz/auto_battle.md) · [进游戏](zzz/enter_game.md) · [功能模块](zzz/application/) · [迷失之地](zzz/application/lost_void/) · [后端服务层](zzz/backend/) · [截图存档](zzz/screenshot_archive.md)
- **AI Harness 工程**：[总览与路线图](harness/README.md)
- **设计文档**：[屏幕区域识别设计](screen_scope_design.md) · [屏幕区域推进](screen_scope_rollout.md)
- **测试与画面**：[测试方法论](testing/) · [截图存档](zzz/screenshot_archive.md)

## 1.开发

### 1.1.开发环境

见 [setup/quickstart.md](setup/quickstart.md)（从零把项目跑起来）。

### 1.2.代码规范

参考 [agent_guidelines.md](spec/agent_guidelines.md)

#### 1.2.1.多线程

当前使用 onnxruntime-dml 在多线程下同时访问多个session是会出现各种意想不到的异常的，因此需要异步使用onnx session时，需统一使用 `gpu_executor.submit` 来提交，保证只有一个session被访问。

另外，onnx session 的线程池默认会自旋等待，空闲时也占用 CPU。本项目都是间歇调用，统一在创建 session 时关闭自旋（见 `onnxocr/inference_engine.py`、`one_dragon/yolo/onnx_model_loader.py`）。

### 1.3.测试

本仓库的自动化测试在 `tests/`：`uv run --env-file .env pytest -m "not requires_models"` 跑纯逻辑测试，不需要游戏和模型。上游的测试放在独立仓库 [zzz-od-test](https://github.com/OneDragon-Anything/zzz-od-test)，其中的识别测试和截图存档**尚未迁移**，涉及游戏画面的改动仍要在 Windows 上手动运行验证。

> 测试方法论(测试基建 / FixtureController 流程测试 / 画面截图存档)见 [testing/](testing/)。

## 2.Vibe Coding

- AI 编码工具（Claude Code / GitHub Copilot / Qwen / Gemini 等）的接入方式、MCP 与扩展配置见 [setup/ai_coding.md](setup/ai_coding.md)。
- AI Coding Harness 工程的设计决策、skill 清单与 MCP 路线图见 [harness/](harness/README.md)。
