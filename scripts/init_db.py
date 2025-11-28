#!/usr/bin/env python3
"""数据库初始化脚本。

此脚本通过以下方式初始化数据库：
1. 根据ORM模型创建所有表
2. 创建初始管理员用户（如果不存在）
3. 创建任何其他必要的初始数据
"""

import logging
import os
import sys
from sqlalchemy.orm import Session

# 将项目根目录添加到路径
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

# 项目内部导入必须在sys.path调整后
from app.adapters.db.models.user import User as UserModel
from app.adapters.db.session import Base, SessionLocal, engine
from app.core.security import get_password_hash

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def init_db():
    """通过创建表来初始化数据库。"""
    logger.info("开始数据库初始化...")

    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("所有表创建成功")

    except Exception as e:
        logger.error(f"创建表时出错: {e}")
        raise


def create_initial_data(db: Session):
    """在数据库中创建初始数据。

    参数:
        db: 数据库会话
    """
    logger.info("创建初始数据...")

    # 如果不存在则创建管理员用户
    admin_user = (
        db.query(UserModel).filter(UserModel.username == "admin").first()
    )

    if not admin_user:
        admin_user = UserModel(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            full_name="管理员",
            is_active=True,
            is_superuser=True,
        )
        db.add(admin_user)
        db.commit()
        logger.info("管理员用户创建成功")
    else:
        logger.info("管理员用户已存在")

    # 在此添加任何其他初始数据
    # 例如：创建默认角色、权限、产品等
    #
    # 示例：创建示例产品
    # if settings.ENVIRONMENT == "development":
    #     from app.adapters.db.models.product import Product as ProductModel
    #     sample_products = [
    #         {
    #             "name": "产品 1", 
    #             "description": "第一个产品", 
    #             "price": 99.99, 
    #             "stock": 100
    #         },
    #         {
    #             "name": "产品 2", 
    #             "description": "第二个产品", 
    #             "price": 199.99, 
    #             "stock": 50
    #         },
    #     ]
    #
    #     for product_data in sample_products:
    #         if not db.query(ProductModel).filter(
    #             ProductModel.name == product_data["name"]
    #         ).first():
    #             product = ProductModel(**product_data)
    #             db.add(product)
    #
    #     db.commit()
    #     logger.info("示例产品已创建")


def main():
    """运行初始化过程的主函数。"""
    try:
        # 初始化数据库表
        init_db()

        # 创建数据库会话
        db = SessionLocal()

        try:
            # 创建初始数据
            create_initial_data(db)
            logger.info("数据库初始化成功完成！")

        except Exception as e:
            logger.error(f"创建初始数据时出错: {e}")
            db.rollback()
            raise

        finally:
            db.close()

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
