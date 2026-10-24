from dataclasses import dataclass


@dataclass(frozen=True)
class TutorialStep:
    """教程里的一个步骤：标题 + 说明（说明里 \\n 表示换行）"""

    title: str
    body: str


@dataclass(frozen=True)
class TutorialPage:
    """教程的一页：对应弹窗里的一个标签"""

    key: str
    title: str
    intro: str
    steps: list[TutorialStep]


# 主页横幅上显示的三步概览
QUICK_STEPS: list[str] = [
    '设置游戏路径',
    '选刷取目标和次数',
    '点「开始运行」',
]


def build_tutorial_pages(start_key: str, stop_key: str) -> list[TutorialPage]:
    """
    生成教程内容
    :param start_key: 开始/暂停按键，如 F9
    :param stop_key: 停止按键，如 F10
    """
    return [
        _build_prepare_page(),
        _build_settings_page(start_key, stop_key),
        _build_lost_void_page(start_key, stop_key),
        _build_battle_page(start_key, stop_key),
        _build_faq_page(),
    ]


def _build_prepare_page() -> TutorialPage:
    return TutorialPage(
        key='prepare',
        title='开始前准备',
        intro='第一次用，先把下面 4 件事做好，一次就行，以后不用再弄。',
        steps=[
            TutorialStep(
                '用管理员身份打开程序',
                '双击 ZZZLostVoid.exe 后，系统会弹出「是否允许此应用对设备进行更改」，请点「是」。\n'
                '游戏是管理员权限运行的，程序没有管理员权限就点不了游戏。',
            ),
            TutorialStep(
                '把游戏画面设成 1920×1080',
                '窗口模式或全屏都可以，但分辨率必须是 1920×1080，其他分辨率会认不出画面。\n'
                '游戏的 HDR 要关闭：程序自动启动游戏时会自己关掉；'
                '只有你手动打开游戏时，才需要先在「设置 → 游戏设置」里点「禁用 HDR」。',
            ),
            TutorialStep(
                '告诉程序游戏装在哪',
                '点左侧最下面的「设置」→「游戏设置」→ 最上面「游戏」分组的「游戏路径」→ 点「选择」，\n'
                '找到游戏安装目录里的 ZenlessZoneZero.exe 并选中。\n'
                '设置好之后，游戏没开的时候程序会自己启动游戏并进入。\n'
                '其他设置要不要改，见旁边的「设置页」标签。',
            ),
            TutorialStep(
                '在游戏里解锁迷失之地',
                '程序只负责刷，不会帮你做剧情。你的账号要先在游戏里解锁「迷失之地」，\n'
                '并且已经能手动进去玩。',
            ),
            TutorialStep(
                '看主页的「运行准备」',
                '回到「主页」，顶部的「运行准备」显示绿色的「准备就绪」就可以开始了。\n'
                '如果显示黄色的「有 N 项需要处理」，点后面的「前往」按钮，按提示补上就行。',
            ),
        ],
    )


def _build_settings_page(start_key: str, stop_key: str) -> TutorialPage:
    return TutorialPage(
        key='settings',
        title='设置页',
        intro='设置页里大部分选项用默认值就行。每个选项名字旁边都有一个 ! 图标，鼠标放上去就能看到说明。',
        steps=[
            TutorialStep(
                '必须设：游戏路径',
                '在「设置 → 游戏设置」最上面的「游戏」分组里，选好 ZenlessZoneZero.exe。\n'
                '没设的话，主页的「运行准备」会提醒你，点「前往」就能跳过来。',
            ),
            TutorialStep(
                '看情况改：游戏区服',
                '默认是国服。用 B 服、美服、欧服、亚服、港澳台服的，要改成自己所在的服，\n'
                '否则自动启动和登录会走错。',
            ),
            TutorialStep(
                '看情况改：自动登录',
                '「设置 → 游戏设置」里的「自动登录（可选）」。游戏一直保持登录状态就不用填；\n'
                '想让程序在登录界面自动登录，才填账号密码（明文保存在你电脑本地）。',
            ),
            TutorialStep(
                '看情况改：按键设置',
                '「设置 → 游戏设置」最下面的「按键设置」。默认值就是游戏的默认键位，\n'
                '只有你在游戏里改过键位，才需要把这里改成一样的，否则程序会按错键。',
            ),
            TutorialStep(
                '看情况改：开始 / 停止快捷键',
                f'在「设置 → 脚本环境」的「脚本按键」里。默认 {start_key} 开始或暂停、{stop_key} 停止，\n'
                '和别的软件快捷键冲突时才需要改。',
            ),
            TutorialStep(
                '看情况改：显示高级设置',
                '在「设置 → 脚本环境」里，默认关闭，此时只显示常用设置，也不显示「资源管理」页。\n'
                '不熟悉就保持关闭，不会影响正常使用。',
            ),
            TutorialStep(
                '可以不管的',
                '悬浮层（测试功能）、推送通知、自定义里的语言和主题、后台模式（测试版）、\n'
                'DX12 启动、启动参数。这些都有可用的默认值，需要时看每项旁边的 ! 说明再决定。',
            ),
        ],
    )


def _build_lost_void_page(start_key: str, stop_key: str) -> TutorialPage:
    return TutorialPage(
        key='lost_void',
        title='迷失之地',
        intro='程序会自己进入迷失之地，完成选队、走图、选鸣徽和战斗，你只需要设置好然后点开始。',
        steps=[
            TutorialStep(
                '第 1 步：选刷取目标',
                '点左侧「迷失之地」，在「刷取目标」里选一个：\n'
                '• 完成悬赏委托（推荐新手）：刷到每周 8000 积分的奖励就停。\n'
                '• 刷满业绩点：刷到每周零号业绩点满就停。\n'
                '• 获取大部分菲林奖励：自动在战线肃清收集首通和以太活性奖励，\n'
                '   程序不能确认奖励是否全部拿完，需要你自己进游戏核对。',
            ),
            TutorialStep(
                '第 2 步：设置计划刷取次数',
                '通关达到这个次数后程序自动停止。第一次先填 1 或 2 次，看着它跑通了再加大。',
            ),
            TutorialStep(
                '第 3 步：选预备编队（可选）',
                '先在游戏里把要用的队伍存成「编队 N」，这里选对应的 N，出战前程序会自动换上这支队伍。\n'
                '不确定就保持「不选择」，程序会使用游戏里当前的队伍。',
            ),
            TutorialStep(
                f'第 4 步：点开始（或按 {start_key}）',
                '可以点主页迷失之地卡片上的「开始运行」，也可以在「迷失之地」页点右侧的「开始」。\n'
                '游戏没开也没关系，程序会按「游戏路径」自己启动并进入游戏。',
            ),
            TutorialStep(
                '运行中要注意',
                '• 游戏窗口不要最小化，也不要被别的窗口盖住。\n'
                '• 程序会模拟键盘鼠标操作游戏，运行时尽量不要同时操作这台电脑。\n'
                f'• 想暂停或继续，按 {start_key}；想停止，按 {stop_key}。\n'
                '• 右侧的日志会显示当前在做什么，看到滚动就说明在正常运行。',
            ),
            TutorialStep(
                '跑完之后',
                '到了计划次数程序会自动停下。如果想让它跑完后自动关游戏或关机，\n'
                '在「迷失之地」页的「结束后」里选；选了「关机」会在跑完约 1 分钟后关机，不想关就改回「无」。',
            ),
        ],
    )


def _build_battle_page(start_key: str, stop_key: str) -> TutorialPage:
    return TutorialPage(
        key='battle',
        title='战斗助手',
        intro='你自己在游戏里玩，程序在旁边帮你打架。和迷失之地互不影响，不用的话可以跳过。',
        steps=[
            TutorialStep(
                '先选一种模式',
                '点左侧「战斗助手」，顶部有两个标签：\n'
                '• 自动战斗：程序替你按技能、普攻和闪避，整场战斗自动打。\n'
                '• 闪避助手：只在敌人攻击时帮你自动闪避，其余操作你自己来。',
            ),
            TutorialStep(
                '选战斗配置或闪避方式',
                '自动战斗在「战斗配置」里选，不知道选哪个就用默认的「全配队通用」。\n'
                '闪避助手在「闪避方式」里选一个。',
            ),
            TutorialStep(
                f'进入战斗后点开始（或按 {start_key}）',
                '先在游戏里进到有战斗的场景，再点「开始」或按键。想停就按 '
                f'{stop_key}。',
            ),
            TutorialStep(
                '让它打得更好的小建议',
                '• 游戏帧数限制在 30 帧，画质适当调低，不要开「无限帧率」。\n'
                '• 把连携技的「左」「右」「取消」设成各自独立的按键，不要和普攻、闪避共用，\n'
                '   连携技放错基本都是因为共用了同一个按键。\n'
                '• 关掉不必要的后台程序，游戏窗口不要被盖住。\n'
                '• 遇到 BOSS 转阶段等特殊情况，可能需要你暂停后手动处理一下。',
            ),
        ],
    )


def _build_faq_page() -> TutorialPage:
    return TutorialPage(
        key='faq',
        title='常见问题',
        intro='遇到问题先对照下面几条，大部分都是这些原因。',
        steps=[
            TutorialStep(
                '点了开始，游戏里没有反应',
                '依次检查：① 程序是不是管理员权限运行的；② 游戏分辨率是不是 1920×1080；\n'
                '③ 游戏窗口有没有被最小化或被别的窗口盖住。',
            ),
            TutorialStep(
                '运行到一半停了或卡住了',
                '先按停止键，再重新点开始试一次。\n'
                '反复出现的话，把程序目录下 .log 文件夹里最新的日志文件发给开发者，并说明卡在哪个画面。',
            ),
            TutorialStep(
                '杀毒软件报毒',
                '程序是开源的，启动器没有代码签名所以会被误报。把程序所在文件夹加入杀毒软件的白名单即可。',
            ),
            TutorialStep(
                '怎么升级到新版本',
                '程序启动时会自动检查更新，有新版会提示。想手动升级的话，下载新版压缩包解压到新文件夹，\n'
                '再把旧版 config 文件夹里的内容复制过去，就能保留设置。',
            ),
            TutorialStep(
                '说明和更多帮助',
                '完整手册和问题反馈见主页右上角的 GitHub 页面。\n'
                '本软件免费开源，没有授权任何人售卖，如果是花钱买到的，请注意被骗。',
            ),
        ],
    )
