# SpotifyExportTool 开发者指南

## 项目架构

### 目录结构

```
SpotifyExportTool/
├── src/                  # 主要源代码目录
│   ├── config/           # 配置管理
│   │   ├── settings.py   # 应用设置
│   │   └── config.py     # 配置加载
│   ├── exporters/        # 数据导出模块
│   │   ├── txt_exporter.py
│   │   ├── csv_exporter.py
│   │   └── json_exporter.py
│   ├── tools/            # 辅助工具
│   │   └── ...
│   ├── ui/               # 用户界面模块
│   │   ├── home.py       # 主页视图
│   │   ├── login.py      # 登录视图
│   │   ├── sidebar_view.py  # 侧边栏
│   │   ├── settings_view.py # 设置页面
│   │   └── ...
│   └── utils/            # 实用工具
│       ├── cache_manager.py  # 缓存管理
│       ├── language_manager.py  # 语言管理
│       ├── logger.py     # 日志系统
│       └── thread_manager.py  # 线程管理
└── main.py               # 应用程序入口
```

## 开发环境设置

### 前提条件

- Python 3.7+
- pip
- 虚拟环境（推荐）

### 环境搭建步骤

1. 克隆仓库
```bash
git clone https://github.com/Cail-Gainey/SpotifyExportTool.git
cd SpotifyExportTool
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate    # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

## 开发流程

### 代码规范

- 遵循 PEP 8 风格指南
- 使用类型注解
- 编写有意义的注释和文档字符串
- 保持代码简洁和可读性

### 模块开发指南

#### UI 模块
- 继承 `QWidget` 或 `QDialog`
- 使用信号和槽进行组件间通信
- 尽量保持业务逻辑与界面分离

#### 工具模块
- 编写通用、可复用的函数
- 使用类型提示
- 添加适当的错误处理

#### 导出模块
- 实现统一的导出接口
- 支持多种导出格式
- 处理导出过程中的异常情况

## 日志系统

项目使用 `loguru` 作为日志系统。

### 日志级别

- `DEBUG`: 详细调试信息
- `INFO`: 一般运行信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 日志使用示例

```python
from src.utils.logger import logger

def example_function():
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告")
    logger.error("这是一条错误信息")
```

## 测试

### 单元测试

- 使用 `pytest` 进行单元测试
- 覆盖关键模块和关键路径
- 测试代码放置在 `tests/` 目录

### 运行测试

```bash
pytest tests/
```

## 打包与发布

### Windows 打包

```bash
pyinstaller spotify_export.spec
```

### macOS 打包

```bash
pyinstaller spotify_export.spec
```

## 持续集成

### GitHub Actions

项目配置了 GitHub Actions 进行：
- 代码风格检查
- 单元测试
- 自动构建

## 贡献指南

1. Fork 仓库
2. 创建特性分支 `git checkout -b feature/amazing-feature`
3. 提交更改 `git commit -m '添加一些令人惊叹的特性'`
4. 推送到分支 `git push origin feature/amazing-feature`
5. 提交 Pull Request

## 常见问题

### 如何添加新的语言支持？

1. 在 `locale/` 目录添加新的 JSON 语言文件
2. 更新 `language_manager.py`
3. 在设置页面添加语言选项

### 如何调试 OAuth 认证问题？

- 检查 `config.py` 中的 Spotify API 凭据
- 确保重定向 URI 正确配置
- 查看日志文件中的详细错误信息

## 联系方式

- GitHub Issues: [提交问题](https://github.com/Cail-Gainey/SpotifyExportTool/issues)
- 邮箱: cailgainey@foxmail.com

---

祝你开发愉快！🚀 