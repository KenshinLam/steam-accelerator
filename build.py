import os
import sys
import shutil
from subprocess import run

def build_exe():
    """打包程序为exe"""
    print("开始打包程序...")
    
    # 确保dist目录存在并清空
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    os.makedirs('dist')
    
    # 使用pyinstaller打包
    cmd = [
        'pyinstaller',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--uac-admin',  # 请求管理员权限
        '--icon=app.ico',  # 如果有图标的话
        '--add-data=config.json;.',  # 添加配置文件
        '--name=Steam游戏加速器',
        'gui.py'
    ]
    
    result = run(cmd)
    if result.returncode != 0:
        print("打包失败！")
        return False
        
    # 复制必要的文件到dist目录
    shutil.copy('config.json', 'dist')
    
    print("打包完成！程序位于 dist 目录")
    return True

if __name__ == '__main__':
    build_exe()
