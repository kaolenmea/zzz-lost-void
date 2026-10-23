"""免安装包的启动器：用包内自带的 Python 启动程序。

打包成 exe 时要求管理员权限（游戏以管理员运行，普通权限的键鼠输入会被系统拦截），
子进程会继承这个权限，程序本身不会再弹一次提权窗口。
只用标准库，打出来的 exe 很小。
"""
import ctypes
import os
import subprocess
import sys
from pathlib import Path

WINDOW_TITLE: str = 'ZZZ Lost Void'


def show_error(message: str) -> None:
    """弹出错误提示（exe 没有控制台窗口，只能用弹窗告诉用户）"""
    ctypes.windll.user32.MessageBoxW(0, message, WINDOW_TITLE, 0x10)


def main() -> int:
    root = Path(sys.executable).resolve().parent
    pythonw = root / 'python' / 'pythonw.exe'
    entry = root / 'src' / 'zzz_lv' / 'gui' / 'app.py'

    if not pythonw.is_file() or not entry.is_file():
        show_error(
            '找不到程序文件，请确认已经把压缩包完整解压，'
            '并且没有单独移动 ZZZLostVoid.exe。\n\n'
            f'缺少: {pythonw if not pythonw.is_file() else entry}'
        )
        return 1

    env = os.environ.copy()
    env['PYTHONPATH'] = str(root / 'src')
    subprocess.Popen([str(pythonw), str(entry)], cwd=str(root), env=env)
    return 0


if __name__ == '__main__':
    sys.exit(main())
