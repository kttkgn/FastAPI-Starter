"""应用程序测试的Pytest配置。

此文件包含运行pytest测试的fixture和配置。
"""

# 导入必要的库
import os
from typing import Any, Dict, Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 设置测试环境变量
os.environ["ENVIRONMENT"] = "test"

# 关键步骤：导入顺序很重要！
# 1. 首先导入所有模型，确保它们注册到Base
print("[conftest] 第一步：导入所有模型...")
from app.adapters.db.models.order import Order, OrderItem
from app.adapters.db.models.product import Product
from app.adapters.db.models.user import User

print("[conftest] ✓ 模型导入完成")

# 2. 然后导入Base
print("[conftest] 第二步：导入Base...")
from app.adapters.db.session import Base

print(f"[conftest] ✓ Base导入完成 (id: {id(Base)})")
print(f"[conftest] ✓ 已注册的表: {list(Base.metadata.tables.keys())}")

# 3. 验证所有模型使用同一个Base实例
print("[conftest] 验证模型Base一致性:")
print(f"[conftest]   User.__base__ id: {id(User.__base__)}")
print(f"[conftest]   Product.__base__ id: {id(Product.__base__)}")
print(
    f"[conftest]   一致性验证: "
    f"{id(User.__base__) == id(Base) == id(Product.__base__)}"
)

# 4. 创建测试数据库配置
TEST_DATABASE_URL = "sqlite:////tmp/test_app.db"
print(f"[conftest] 测试数据库URL: {TEST_DATABASE_URL}")

# 5. 创建测试专用引擎和会话工厂
print("[conftest] 创建测试数据库引擎...")
test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)
print(f"[conftest] ✓ 测试引擎创建完成 (id: {id(test_engine)})")

# 6. 在模块级别创建所有表 - 确保在任何测试运行前表已存在
print("[conftest] 创建数据库表...")
Base.metadata.create_all(bind=test_engine)
print("[conftest] ✓ 表创建完成")

# 7. 验证表是否真的创建成功
print("[conftest] 验证表创建...")
try:
    with test_engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        existing_tables = [row[0] for row in result]
        print(f"[conftest] SQLite中实际存在的表: {existing_tables}")
        assert (
            "users" in existing_tables
        ), "[conftest] ERROR: users表未创建成功！"
except Exception as e:
    print(f"[conftest] 验证表存在时出错: {e}")
    raise

# 8. 强制应用程序使用测试数据库引擎
print("[conftest] 配置应用程序使用测试数据库...")
from app.adapters.db import session

session.engine = test_engine
session.SessionLocal = TestingSessionLocal
print("[conftest] ✓ 应用程序数据库引擎已替换")


# 9. 重写session模块的get_db函数，确保返回测试会话
def test_get_db() -> Generator:
    """测试用的get_db函数。"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


session.get_db = test_get_db
print("[conftest] ✓ get_db函数已替换")

# 10. 重写init_db函数，确保使用测试引擎
old_init_db = session.init_db


def test_init_db():
    """测试用的init_db函数。"""
    print("[conftest] test_init_db called")
    # 重新导入模型，确保注册
    from app.adapters.db.models.order import Order, OrderItem
    from app.adapters.db.models.product import Product
    from app.adapters.db.models.user import User

    # 使用测试引擎创建表
    Base.metadata.create_all(bind=test_engine)

    # 再次验证表存在
    with test_engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = [row[0] for row in result]
        print(f"[conftest] init_db后表: {tables}")


session.init_db = test_init_db
print("[conftest] ✓ init_db函数已替换")

# 11. 导入应用程序
print("[conftest] 导入应用程序...")
from fastapi.testclient import TestClient

from app.main import app

print("[conftest] ✓ 应用程序导入完成")


@pytest.fixture(scope="function")
def db() -> Generator:
    """测试用的数据库会话fixture。"""
    print("[conftest:db] 创建测试数据库会话...")

    # 在每个测试前，先清理表中的数据但不删除表
    # 这样可以避免频繁创建/删除表导致的问题
    print("[conftest:db] 清理表数据...")
    with test_engine.connect() as conn:
        # 按照依赖关系顺序清理表
        conn.execute(text("DELETE FROM order_items"))
        conn.execute(text("DELETE FROM orders"))
        conn.execute(text("DELETE FROM products"))
        conn.execute(text("DELETE FROM users"))
        conn.commit()
    print("[conftest:db] ✓ 表数据清理完成")

    # 再次验证表存在（这很重要！）
    with test_engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = [row[0] for row in result]
        print(f"[conftest:db] 测试前可用表: {tables}")
        assert "users" in tables, "[conftest:db] 错误：users表不存在！"

    # 创建测试会话
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        print("[conftest:db] ✓ 会话关闭")


@pytest.fixture(scope="function")
def client(db) -> Generator:
    """测试客户端fixture。"""
    print("[conftest:client] 创建测试客户端...")

    # 创建测试客户端
    client = TestClient(app)

    # 验证应用程序使用的是测试数据库
    from app.adapters.db import session

    print(f"[conftest:client] 应用程序engine id: {id(session.engine)}")
    print(f"[conftest:client] 测试engine id: {id(test_engine)}")
    print(f"[conftest:client] 引擎一致性: {session.engine is test_engine}")

    # 确保在请求前表存在
    with test_engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = [row[0] for row in result]
        print(f"[conftest:client] 客户端请求前可用表: {tables}")

    yield client
    print("[conftest:client] ✓ 客户端测试完成")


@pytest.fixture(scope="function")
def client(db) -> Generator:
    """FastAPI应用程序的测试客户端fixture。"""
    print(f"[conftest] 创建测试客户端，使用数据库: {db.bind.url}")

    # 导入get_db用于覆盖
    # 完全替换session模块中的get_db函数
    # 这样应用程序中的任何地方导入get_db都会使用我们的测试版本
    import app.adapters.db.session as session_module
    from app.adapters.db.session import get_db

    original_get_db = session_module.get_db

    def test_get_db():
        try:
            print("[conftest] 应用程序请求数据库会话")
            yield db
        finally:
            pass

    # 替换session模块中的get_db函数
    session_module.get_db = test_get_db

    # 同时也覆盖FastAPI的依赖
    app.dependency_overrides[get_db] = test_get_db

    # 创建测试客户端
    with TestClient(app) as test_client:
        yield test_client

    # 清理 - 恢复原始的get_db
    session_module.get_db = original_get_db
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function")
def test_user(db) -> Generator:
    """为认证创建测试用户。

    参数:
        db: 数据库会话fixture

    生成:
        测试用户
    """
    from app.adapters.db.models.user import User as UserModel
    from app.core.security import get_password_hash

    # 创建测试用户
    test_user = UserModel(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )

    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    yield test_user


@pytest.fixture(scope="function")
def test_superuser(db) -> Generator:
    """为认证创建测试超级用户。

    参数:
        db: 数据库会话fixture

    生成:
        测试超级用户
    """
    from app.adapters.db.models.user import User as UserModel
    from app.core.security import get_password_hash

    # 创建测试超级用户
    test_superuser = UserModel(
        username="testadmin",
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword123"),
        full_name="Test Admin",
        is_active=True,
        is_superuser=True,
    )

    db.add(test_superuser)
    db.commit()
    db.refresh(test_superuser)

    yield test_superuser


@pytest.fixture(scope="function")
def user_token(client, test_user) -> str:
    """获取测试用户的认证令牌。

    参数:
        client: 测试客户端
        test_user: 测试用户

    返回:
        JWT令牌
    """
    # 登录获取令牌
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpassword123"},
    )

    # 返回访问令牌
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def admin_token(client, test_superuser) -> str:
    """获取测试超级用户的认证令牌。

    参数:
        client: 测试客户端
        test_superuser: 测试超级用户

    返回:
        JWT令牌
    """
    # 登录获取令牌
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testadmin", "password": "adminpassword123"},
    )

    # 返回访问令牌
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def test_product(db) -> Generator:
    """创建测试产品。

    参数:
        db: 数据库会话fixture

    生成:
        测试产品
    """
    from app.adapters.db.models.product import Product as ProductModel

    # 创建测试产品
    test_product = ProductModel(
        name="Test Product",
        description="Test product description",
        price=99.99,
        stock=100,
    )

    db.add(test_product)
    db.commit()
    db.refresh(test_product)

    yield test_product


@pytest.fixture(scope="function")
def mock_settings(mocker) -> Generator:
    """模拟测试用的设置。

    参数:
        mocker: Pytest-mock fixture

    生成:
        模拟的设置
    """
    # 模拟settings对象
    mock_settings = mocker.patch("app.core.config.settings")
    mock_settings.ENVIRONMENT = "test"
    mock_settings.DATABASE_URL = "sqlite:///:memory:"
    mock_settings.REDIS_URL = "redis://localhost:6379/1"
    mock_settings.SECRET_KEY = "test-secret-key"
    mock_settings.JWT_SECRET = "test-jwt-secret"
    mock_settings.APP_NAME = "Test App"
    mock_settings.APP_VERSION = "0.1.0"
    mock_settings.DEBUG = True

    yield mock_settings


@pytest.fixture(scope="function")
def sample_payloads() -> Dict[str, Any]:
    """测试API端点的样本请求体。

    返回:
        样本请求体字典
    """
    return {
        "user_create": {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword123",
            "full_name": "New User",
        },
        "product_create": {
            "name": "New Product",
            "description": "New product description",
            "price": 199.99,
            "stock": 50,
        },
        "order_create": {"items": [{"product_id": 1, "quantity": 2}]},
        "login": {"username": "testuser", "password": "testpassword123"},
    }


# 配置pytest选项
def pytest_configure(config):
    """向pytest配置添加标记。

    参数:
        config: Pytest配置对象
    """
    config.addinivalue_line("markers", "api: 标记为API测试")
    config.addinivalue_line("markers", "unit: 标记为单元测试")
    config.addinivalue_line("markers", "integration: 标记为集成测试")
    config.addinivalue_line(
        "markers", "slow: 标记为慢速测试(使用-m 'not slow'跳过)"
    )
    config.addinivalue_line("markers", "db: 标记需要数据库的测试")


# 测试结果收集钩子
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """向pytest输出添加摘要信息。

    参数:
        terminalreporter: 终端报告器对象
        exitstatus: 退出状态码
        config: Pytest配置对象
    """
    terminalreporter.ensure_newline()
    terminalreporter.section("测试摘要")
    terminalreporter.line(f"总测试数: {terminalreporter._numcollected}")
    terminalreporter.line(
        f"通过: {len(terminalreporter.stats.get('passed', []))}"
    )
    terminalreporter.line(
        f"失败: {len(terminalreporter.stats.get('failed', []))}"
    )
    terminalreporter.line(
        f"跳过: {len(terminalreporter.stats.get('skipped', []))}"
    )
    terminalreporter.line(
        f"错误: {len(terminalreporter.stats.get('error', []))}"
    )
