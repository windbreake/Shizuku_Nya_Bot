import os, subprocess, platform

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
START_BAT = os.path.join(BASE_DIR, 'start.bat')

def run_choice(choice: str):
    """
    通过管道将 choice 输入到 start.bat 以跳转到对应标签
    """
    # 在 Windows 下使用管道输入选项，然后自动关闭窗口
    cmd = f'cmd /c echo {choice} ^| "{START_BAT}"'
    subprocess.Popen(cmd, shell=True)
