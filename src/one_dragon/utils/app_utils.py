import subprocess
import sys


def start_one_dragon(restart: bool) -> None:
    """
    用当前解释器和启动参数重新启动脚本
    :param restart: 是否退出当前进程
    """
    subprocess.Popen([sys.executable, *sys.argv])
    if restart:
        sys.exit(0)
