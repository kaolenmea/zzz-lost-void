# 打包与发布免安装包

免安装包是一个文件夹加一个启动器 `ZZZLostVoid.exe`，里面自带 Python 和全部依赖，用户解压后双击就能用，不需要装任何东西。

## 为什么不是把程序整个打成单个 exe

程序启动时会扫描 `src/zzz_lv/application/` 下的 `.py` 文件来注册应用和设置页（`ApplicationFactoryManager`、`AppSettingManager`），运行时要读 `src/` 下的源码文件。整个冻结成单个 exe 要逐个处理这些动态加载，也更容易被杀毒软件当成病毒。所以做法是：带一份 Python，源码原样放着，`ZZZLostVoid.exe` 只是一个很小的启动器，负责用管理员权限调起包里的 `pythonw.exe`。

## 包里有什么

```
ZZZLostVoid\
  ZZZLostVoid.exe    启动器（PyInstaller 打包，要求管理员权限）
  python\            uv 管理的独立 Python 3.11 + 依赖（已删掉用不到的 Qt 浏览器内核、3D、翻译）
  src\ assets\ plugins\
  config\            只含 git 已跟踪的文件，不含任何个人配置
  release.json       版本号、提交号、构建时间
  LICENSE  README.md
```

`release.json` 存在，程序就认为自己是发布包：默认关闭「显示高级设置」、窗口标题栏显示版本号、首次运行弹出快速设置。源码运行没有这个文件，默认显示全部设置。

## 本机打包

前置：Windows，已装 `uv` 和 `git`，`assets/models/` 里放好了全部模型（模型不在 git 里，打包脚本从本机目录复制）。

```powershell
./packaging/build.ps1                 # 版本号读 pyproject.toml 的 version
./packaging/build.ps1 -Version 1.0.1  # 指定版本号
./packaging/build.ps1 -SkipZip        # 只生成 dist/ZZZLostVoid/，不压缩
```

产物是 `dist/ZZZLostVoid-v<版本>.zip`（约 570 MB，解压后约 1.3 GB）。脚本最后会用包里的 Python 导入一次主程序做自检。构建大约 6~8 分钟，其中压缩占两分钟。

## 用 GitHub 发布

1. 一次性准备：把 `assets/models/` 整个目录压成 `models.zip`，在本仓库建一个标签叫 `models` 的 Release，把它传上去。工作流从这里取模型。
2. 更新 `pyproject.toml` 的 `version`，在 `CHANGELOG.md` 写这一版的改动，提交。
3. 打标签并推送：`git tag v1.0.0 && git push origin v1.0.0`。`.github/workflows/release.yml` 会打包并创建同名 Release，附上 zip。

## 打包前要自己确认

- `git ls-files config` 里没有个人配置（`config/[0-9]*/`、`env.yml` 等已被 `.gitignore` 忽略，不会被复制）。
- 本机 `assets/ui/` 下的个人背景图（`version_poster.webp`、`static_background.webp`、`dynamic_background.webm`）脚本会删掉，不会打进包。
- 没有在本机验证的部分：启动器 exe 的管理员提权弹窗（需要人点「是」）、在没有装过 Python 和 VC++ 运行库的干净机器上运行。发版前请在干净的 Windows 上完整跑一局。

## 已知问题

- 启动器 exe 没有代码签名，Windows Defender 或其他杀毒软件可能提示风险。源码公开，可以自行用上面的脚本打包。
- 包很大，主要是 PySide6（约 300 MB）和模型（约 200 MB）。
