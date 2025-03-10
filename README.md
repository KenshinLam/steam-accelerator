# Steam Game Accelerator

一个用于优化Steam游戏（如DOTA2、CS2）网络连接的加速器。

## 功能特点

- 支持多个游戏服务器区域（国服、香港、东南亚等）
- 实时延迟监控
- 自动选择最优节点
- 可视化界面，操作简单

## 系统要求

- Windows 10/11
- Python 3.8+
- 管理员权限（用于修改系统路由）

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/your-username/steam-accelerator.git
cd steam-accelerator
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 以管理员身份运行：
```bash
python gui.py
```

2. 在界面上选择游戏和区域
3. 点击"测试延迟"
4. 点击"开始加速"

## 配置说明

在 `config.json` 中可以配置：
- 游戏服务器IP
- 加速节点信息
- 区域设置

## 注意事项

- 需要管理员权限
- 使用前请确保已安装所有依赖
- 如遇问题，请查看 `accelerator.log`

## 开发相关

项目结构：
```
steam_accelerator/
├── gui.py              # 图形界面
├── src/
│   ├── main.py        # 主程序
│   └── route_optimizer.py  # 路由优化
├── config.json         # 配置文件
└── requirements.txt    # 依赖列表
```

## License

[MIT License](LICENSE)
