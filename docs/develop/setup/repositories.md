# 相关仓库

> 本仓库拆分自上游 ZenlessZoneZero-OneDragon,只保留迷失之地与战斗助手。模型、数据集仍来自上游组织维护的仓库。

## 总览

| 项 | 类型 | 位置 | 用途 | 何时去动 |
|---|---|---|---|---|
| 上游主仓 | git | [`OneDragon-Anything/ZenlessZoneZero-OneDragon`](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon) | 本仓库的代码来源 | 需要对照或移植上游改动时 |
| 上游测试仓 | git | [`OneDragon-Anything/zzz-od-test`](https://github.com/OneDragon-Anything/zzz-od-test) | 上游测试代码 + 画面截图存档 | 迁移测试时参考 |
| yolo 训练仓 | git | [`OneDragon-Anything/OneDragon-YOLO`](https://github.com/OneDragon-Anything/OneDragon-YOLO) | YOLO 模型训练 + release 发布 | 训练/发模型 |
| 数据集 | 非git(ModelScope) | 见下 | YOLO 训练数据 | 训练时拉取 |

## 测试

本仓库的自动化测试在 `tests/`(纯逻辑测试已就位);上游测试仓里的识别测试和截图存档**尚未迁移**,迁移时放进本仓 `tests/`。

## yolo 训练仓 `OneDragon-YOLO`

- 训练游戏内 YOLO 目标检测模型(迷失之地交互入口、闪光分类等),代码在 `src/one_dragon_yolo/zzz/<玩法>/`。
- **发布**:模型打包成 `<模型名>.zip`,以 release tag `zzz_model` 发布到 `OneDragon-Anything/OneDragon-YOLO`;本仓库按 `config/repository.yml` 下载消费。
- 各玩法模型文档(如 [迷失之地检测模型](../zzz/application/lost_void/det_model.md))记录其来源与消费链路。

## 数据集

- 训练数据**非 git 仓**,托管在 [ModelScope](https://modelscope.cn)(如 [`DoctorReid/ZZZ-LostVoidDet-Dataset`](https://modelscope.cn/models/DoctorReid/ZZZ-LostVoidDet-Dataset)),按 `<玩法>-Dataset` 命名。
- 本仓库相关:ZZZ-FlashClassify / ZZZ-LostVoidDet。
