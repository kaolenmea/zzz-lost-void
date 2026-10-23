# 参与贡献

欢迎提 issue 和 PR。

## 开发环境

见 [docs/develop/README.md](docs/develop/README.md)。简要步骤：

```powershell
uv sync --group dev
copy .env.sample .env
uv run --env-file .env pytest -m "not requires_models"
```

## 提交前

- 只对自己改过的文件运行 `uv run --env-file .env ruff check 文件路径`，不要对整个 `src/` 运行。
- 新逻辑尽量写成不依赖游戏和模型的纯函数，并在 `tests/` 里加测试；需要 OCR 模型的测试加 `@pytest.mark.requires_models`。
- 改了代码行为，同步更新 `docs/develop/` 里对应的文档。
- 涉及游戏画面的改动，请在 PR 里说明在哪个画面、什么分辨率下验证过。

## 提交说明

英文，使用 [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)：`type(scope): subject`。
`type` 可选 `feat / fix / docs / refactor / test / chore / perf / build / ci / style`，`scope` 写模块名；正文写为什么改、改了什么。

## 许可证

提交即表示你同意以 [GPL-3.0](LICENSE) 授权你的贡献。
