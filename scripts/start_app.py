#!/usr/bin/env python3
"""应用程序启动脚本。

此脚本提供了一种便捷的方式来启动FastAPI应用程序，并根据环境使用不同的配置。
"""

import argparse
import os
import sys
import uvicorn

# 将项目根目录添加到路径
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

# 项目内部导入必须在sys.path调整后
from app.core.config import settings
from middleware.logger import Logger

# 配置日志
Logger.setup_logging()
logger = Logger.get_logger("app.startup")


def parse_arguments():
    """解析命令行参数。

    返回:
        解析后的参数
    """
    parser = argparse.ArgumentParser(description="启动FastAPI应用程序")

    parser.add_argument(
        "--env",
        choices=["dev", "prod"],
        default="dev",
        help="运行应用程序的环境 (默认: dev)",
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="绑定应用程序的主机地址 (默认: 0.0.0.0)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="绑定应用程序的端口 (默认: 8000)",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        default=False,
        help="启用热重载 (仅限开发环境)",
    )

    parser.add_argument(
        "--workers", type=int, default=1, help="工作进程数量 (仅限生产环境)"
    )

    return parser.parse_args()


def load_environment_config(env: str) -> None:
    """加载特定环境的配置。

    参数:
        env: 环境名称 (dev 或 prod)
    """
    env_file = os.path.join("conf", f"{env}.env")

    if not os.path.exists(env_file):
        logger.warning(f"未找到环境文件: {env_file}")
        return

    logger.info(f"从以下位置加载环境配置: {env_file}")

    # 从文件加载环境变量
    with open(env_file, "r") as f:
        for line in f:
            # 跳过注释和空行
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # 解析键值对
            try:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # 如果存在引号则移除
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]

                # 设置环境变量
                os.environ[key] = value
                logger.debug(f"设置环境变量: {key}={value}")

            except ValueError:
                logger.warning(f"环境文件中的无效行: {line}")


def configure_logging(env: str) -> None:
    """根据环境配置日志。

    参数:
        env: 环境名称 (dev 或 prod)
    """
    # 对于生产环境，如果存在YAML配置文件则使用它
    if env == "prod":
        log_config_path = os.path.join("conf", "logging.yaml")
        if os.path.exists(log_config_path):
            Logger.setup_logging(log_config_path)
            logger.info("日志已使用生产YAML配置")
            return

    # 对于开发环境或YAML不存在的情况，使用默认配置
    Logger.setup_logging()
    logger.info(f"已为{env}环境配置日志")


def main():
    """启动应用程序的主函数。"""
    try:
        # 解析命令行参数
        args = parse_arguments()

        # 加载特定环境的配置
        load_environment_config(args.env)

        # 配置日志
        configure_logging(args.env)

        # 根据环境验证参数
        if args.env == "prod" and args.reload:
            logger.warning("生产环境不建议使用热重载")

        if args.env == "dev" and args.workers > 1:
            logger.warning("开发环境中多个工作进程可能会影响热重载")

        # 记录启动信息
        logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"环境: {args.env}")
        logger.info(f"调试模式: {settings.DEBUG}")

        # 配置Uvicorn设置
        uvicorn_config = {
            "app": "app.main:app",
            "host": args.host,
            "port": args.port,
            "reload": args.reload,
            "log_level": "info",
        }

        # 为生产环境添加工作进程
        if args.env == "prod" and args.workers > 1:
            uvicorn_config["workers"] = args.workers

        # 启动应用程序
        logger.info(f"服务器启动于 http://{args.host}:{args.port}")
        logger.info(f"API文档可在 http://{args.host}:{args.port}/docs 访问")
        logger.info(f"ReDoc可在 http://{args.host}:{args.port}/redoc 访问")

        uvicorn.run(**uvicorn_config)

    except KeyboardInterrupt:
        logger.info("用户停止了服务器")
        sys.exit(0)

    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
