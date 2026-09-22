"""
统一配置加载模块（.env 支持）
============================
职责：在任何模块读取环境变量之前，加载 rag_server/.env 文件，
     并提供 env(key, default) 辅助函数统一读取配置。

设计考量：
- 项目当前不是 git 仓库，也不强制依赖 python-dotenv，因此对 dotenv 采用「优雅降级」：
    安装了 python-dotenv → 从 rag_server/.env 加载；未安装 → 只用系统环境变量。
- 模块被 import 时立即执行一次 load()，保证无论哪个模块先被导入，配置都已就绪。

用法：
    from common.config import env
    db_password = env("MYSQL_PASSWORD", "xxxxxxx")
"""
import os
from pathlib import Path

# 项目根目录：common/ 的上一级 = rag_server/
# ★ 用 __file__ 推导绝对路径，不依赖 os.getcwd()：
#   保证无论从哪个目录执行 `python main.py`，或未来在 Docker 容器中启动，
#   都能精准定位项目根目录下的 .env 文件。
_BASE_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BASE_DIR / ".env"


def load_dotenv_file():
    """加载 rag_server/.env（幂等；未安装 python-dotenv 时静默跳过）"""
    try:
        from dotenv import load_dotenv
        load_dotenv(_ENV_FILE)
    except ImportError:
        # 未安装 python-dotenv：仅依赖系统环境变量，功能不受影响
        pass


def env(key, default=None):
    """读取环境变量，若未设置则返回默认值。"""
    return os.getenv(key, default)


def required_env(key):
    """读取必填环境变量，缺失或为空时抛出异常（Fail Fast 原则）。

    用于 DASHSCOPE_API_KEY / MYSQL_PASSWORD / NEO4J_PASSWORD / SMTP_PASSWORD
    等核心敏感配置：生产环境若忘记配置 .env，应在启动时立刻失败，
    而不是用默认弱密码静默连库。
    """
    val = os.getenv(key)
    if val is None or val == "":
        raise ValueError(f"Missing required environment variable: {key}")
    return val


def langfuse_config():
    """读取 Langfuse 全链路追踪配置。

    Langfuse 是可观测性增强工具，缺失配置时不应影响核心业务，
    因此缺任一变量返回 None（而非抛异常），由调用方降级为无追踪模式。
    """
    pub = env("LANGFUSE_PUBLIC_KEY")
    sec = env("LANGFUSE_SECRET_KEY")
    base = env("LANGFUSE_BASE_URL")
    if not pub or not sec or not base:
        return None
    return {"public_key": pub, "secret_key": sec, "base_url": base}


# 模块导入时立即加载一次，保证 import 顺序安全
load_dotenv_file()
