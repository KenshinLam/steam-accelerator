import sys
import os
import ctypes
import logging
from datetime import datetime

def setup_logging():
    """设置日志记录"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, f"accelerator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def is_admin():
    """检查是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logging.error(f"检查管理员权限时出错: {str(e)}")
        return False

if __name__ == '__main__':
    try:
        setup_logging()
        print("程序启动...")
        if not is_admin():
            print("尝试获取管理员权限...")
            # 如果不是管理员，则使用管理员权限重新运行
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            except Exception as e:
                logging.error(f"请求管理员权限失败: {str(e)}")
                print("\n错误：无法获取管理员权限。请右键点击程序，选择\"以管理员身份运行\"。")
                input("\n按回车键退出...")
        else:
            logging.info("已获得管理员权限")
            # 添加src目录到Python路径
            src_path = os.path.join(os.path.dirname(__file__), 'src')
            sys.path.append(src_path)
            logging.debug(f"Python路径: {sys.path}")
            logging.debug(f"当前目录: {os.getcwd()}")
            
            try:
                # 导入并运行主程序
                logging.info("正在导入主程序...")
                from main import main
                logging.info("正在启动主界面...")
                main()
            except ImportError as e:
                logging.error(f"导入主程序失败: {str(e)}")
                print("\n错误：无法加载主程序。请确保程序文件完整。")
                print(f"详细错误: {str(e)}")
            except Exception as e:
                logging.error(f"启动主程序时出错: {str(e)}")
                print("\n错误：程序启动失败。")
                print(f"详细错误: {str(e)}")
                
    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}")
        print(f"\n发生未知错误: {str(e)}")
    finally:
        input("\n按回车键退出...")