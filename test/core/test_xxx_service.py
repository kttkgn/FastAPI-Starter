"""领域服务的测试。

该模块包含核心业务逻辑服务的单元测试。
"""

from unittest.mock import Mock, patch

import pytest

from app.adapters.db.repositories.order_repository import OrderRepository
from app.adapters.db.repositories.user_repositories import UserRepository
from app.api.v1.schemas.user_schemas import (
    OrderCreate,
    OrderUpdate,
    UserCreate,
    UserUpdate,
)
from app.core.exceptions import (
    InsufficientStockError,
    OrderNotFoundError,
    ProductNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
    ValidationError,
)
from app.core.services.order_service import OrderService
from app.core.services.user_service import UserService


@pytest.mark.unit
class TestUserService:
    """UserService类的单元测试。"""

    def setup_method(self):
        """在每个测试方法前设置测试夹具。"""
        # 创建模拟仓库
        self.mock_user_repo = Mock(spec=UserRepository)

        # 创建带有模拟依赖的服务实例
        self.user_service = UserService(user_repository=self.mock_user_repo)

    def test_create_user_success(self):
        """测试成功创建用户。"""
        # 创建用户数据
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            full_name="Test User",
        )

        # 配置模拟对象返回None（用户名检查）
        self.mock_user_repo.get_by_username.return_value = None

        # 配置模拟对象返回None（邮箱检查）
        self.mock_user_repo.get_by_email.return_value = None

        # 配置模拟对象在创建时返回用户对象
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = user_create.username
        mock_user.email = user_create.email
        mock_user.full_name = user_create.full_name
        mock_user.is_active = True
        mock_user.is_superuser = False

        self.mock_user_repo.create.return_value = mock_user

        # 调用服务方法
        result = self.user_service.create_user(user_create)

        # 验证仓库方法是否使用正确参数被调用
        self.mock_user_repo.get_by_username.assert_called_once_with(
            user_create.username
        )
        self.mock_user_repo.get_by_email.assert_called_once_with(
            user_create.email
        )
        self.mock_user_repo.create.assert_called_once()

        # 验证结果
        assert result.id == 1
        assert result.username == user_create.username
        assert result.email == user_create.email
        assert result.full_name == user_create.full_name

    def test_create_user_username_exists(self):
        """测试创建已存在用户名的用户。"""
        # 创建用户数据
        user_create = UserCreate(
            username="existinguser",
            email="new@example.com",
            password="testpassword123",
            full_name="New User",
        )

        # 配置模拟对象返回用户对象（用户名检查）
        self.mock_user_repo.get_by_username.return_value = Mock()

        # 调用服务方法并验证异常
        with pytest.raises(UserAlreadyExistsError) as excinfo:
            self.user_service.create_user(user_create)

        # 验证异常消息
        assert "Username already exists" in str(excinfo.value)

        # 验证仓库方法是否被调用
        self.mock_user_repo.get_by_username.assert_called_once_with(
            user_create.username
        )
        self.mock_user_repo.get_by_email.assert_not_called()
        self.mock_user_repo.create.assert_not_called()

    def test_create_user_email_exists(self):
        """测试创建使用已存在邮箱的用户。"""
        # 创建用户数据
        user_create = UserCreate(
            username="newuser",
            email="existing@example.com",
            password="testpassword123",
            full_name="New User",
        )

        # 配置模拟对象返回None（用户名检查）
        self.mock_user_repo.get_by_username.return_value = None

        # 配置模拟对象返回用户对象（邮箱检查）
        self.mock_user_repo.get_by_email.return_value = Mock()

        # 调用服务方法并验证异常
        with pytest.raises(UserAlreadyExistsError) as excinfo:
            self.user_service.create_user(user_create)

        # 验证异常消息
        assert "Email already exists" in str(excinfo.value)

        # 验证仓库方法是否被调用
        self.mock_user_repo.get_by_username.assert_called_once_with(
            user_create.username
        )
        self.mock_user_repo.get_by_email.assert_called_once_with(
            user_create.email
        )
        self.mock_user_repo.create.assert_not_called()

    def test_get_user_by_id_success(self):
        """测试成功通过ID获取用户。"""
        # 配置模拟对象返回用户对象
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"

        self.mock_user_repo.get_by_id.return_value = mock_user

        # 调用服务方法
        result = self.user_service.get_user_by_id(1)

        # 验证仓库方法是否被调用
        self.mock_user_repo.get_by_id.assert_called_once_with(1)

        # 验证结果
        assert result.id == 1
        assert result.username == "testuser"

    def test_get_user_by_id_not_found(self):
        """测试通过ID获取不存在的用户。"""
        # 配置模拟对象返回None
        self.mock_user_repo.get_by_id.return_value = None

        # 调用服务方法并验证异常
        with pytest.raises(UserNotFoundError) as excinfo:
            self.user_service.get_user_by_id(999)

        # 验证异常消息
        assert "User not found" in str(excinfo.value)

        # 验证仓库方法是否被调用
        self.mock_user_repo.get_by_id.assert_called_once_with(999)

    def test_update_user_success(self):
        """测试成功更新用户。"""
        # 创建更新数据
        user_update = UserUpdate(
            full_name="Updated Name", email="updated@example.com"
        )

        # 配置模拟对象返回用户对象
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "old@example.com"
        mock_user.full_name = "Old Name"

        self.mock_user_repo.get_by_id.return_value = mock_user

        # 配置模拟对象返回更新后的用户
        updated_user = Mock()
        updated_user.id = 1
        updated_user.username = "testuser"
        updated_user.email = user_update.email
        updated_user.full_name = user_update.full_name

        self.mock_user_repo.update.return_value = updated_user

        # 调用服务方法
        result = self.user_service.update_user(1, user_update)

        # 验证仓库方法是否被调用
        self.mock_user_repo.get_by_id.assert_called_once_with(1)
        self.mock_user_repo.update.assert_called_once()

        # 验证结果
        assert result.id == 1
        assert result.email == user_update.email
        assert result.full_name == user_update.full_name

    def test_update_user_not_found(self):
        """测试更新不存在的用户。"""
        # 创建更新数据
        user_update = UserUpdate(full_name="Should Fail")

        # 配置模拟对象返回None
        self.mock_user_repo.get_by_id.return_value = None

        # 调用服务方法并验证异常
        with pytest.raises(UserNotFoundError) as excinfo:
            self.user_service.update_user(999, user_update)

        # 验证异常消息
        assert "User not found" in str(excinfo.value)

        # 验证仓库方法是否被调用
        self.mock_user_repo.get_by_id.assert_called_once_with(999)
        self.mock_user_repo.update.assert_not_called()

    def test_delete_user_success(self):
        """测试成功删除用户。"""
        # 配置模拟对象返回用户对象
        mock_user = Mock()
        mock_user.id = 1

        self.mock_user_repo.get_by_id.return_value = mock_user

        # 调用服务方法
        self.user_service.delete_user(1)

        # 验证仓库方法是否被调用
        self.mock_user_repo.get_by_id.assert_called_once_with(1)
        self.mock_user_repo.delete.assert_called_once_with(1)

    def test_delete_user_not_found(self):
        """测试删除不存在的用户。"""
        # 配置模拟对象返回None
        self.mock_user_repo.get_by_id.return_value = None

        # 调用服务方法并验证异常
        with pytest.raises(UserNotFoundError) as excinfo:
            self.user_service.delete_user(999)

        # 验证异常消息
        assert "User not found" in str(excinfo.value)

        # 验证仓库方法是否被调用
        self.mock_user_repo.get_by_id.assert_called_once_with(999)
        self.mock_user_repo.delete.assert_not_called()

    def test_list_users(self):
        """测试列出所有用户。"""
        # 创建模拟用户
        mock_users = [Mock(id=i, username=f"user{i}") for i in range(1, 4)]

        # 配置模拟对象返回用户列表
        self.mock_user_repo.list.return_value = mock_users

        # 调用服务方法
        result = self.user_service.list_users()

        # 验证仓库方法是否被调用
        self.mock_user_repo.list.assert_called_once()

        # 验证结果
        assert len(result) == 3
        assert result[0].id == 1
        assert result[1].id == 2
        assert result[2].id == 3


@pytest.mark.unit
class TestOrderService:
    """OrderService类的单元测试。"""

    def setup_method(self):
        """在每个测试方法前设置测试夹具。"""
        # 创建模拟仓库
        self.mock_order_repo = Mock(spec=OrderRepository)
        self.mock_user_repo = Mock(spec=UserRepository)
        self.mock_product_repo = Mock(
            spec=UserRepository
        )  # 使用UserRepository作为模拟规格

        # 创建带有模拟依赖的服务实例
        self.order_service = OrderService(
            order_repository=self.mock_order_repo,
            user_repository=self.mock_user_repo,
            product_repository=self.mock_product_repo,
        )

    def test_create_order_success(self):
        """测试成功创建订单。"""
        # 创建订单数据
        order_create = OrderCreate(items=[{"product_id": 1, "quantity": 2}])

        # 配置模拟对象返回用户对象
        mock_user = Mock(id=1)
        self.mock_user_repo.get_by_id.return_value = mock_user

        # 配置模拟对象返回产品对象
        mock_product = Mock(id=1, name="Test Product", price=99.99, stock=10)
        self.mock_product_repo.get_by_id.return_value = mock_product

        # 配置模拟对象在创建时返回订单对象
        mock_order = Mock()
        mock_order.id = 1
        mock_order.user_id = 1
        mock_order.status = "pending"
        mock_order.total_amount = 199.98

        self.mock_order_repo.create.return_value = mock_order

        # 调用服务方法
        result = self.order_service.create_order(1, order_create)

        # 验证仓库方法被调用
        self.mock_user_repo.get_by_id.assert_called_once_with(1)
        self.mock_product_repo.get_by_id.assert_called_once_with(1)
        self.mock_order_repo.create.assert_called_once()

        # 验证结果
        assert result.id == 1
        assert result.user_id == 1
        assert result.status == "pending"

    def test_create_order_user_not_found(self):
        """Test creating an order for a non-existent user."""
        # Create order data
        order_create = OrderCreate(items=[{"product_id": 1, "quantity": 1}])

        # 配置模拟对象返回None
        self.mock_user_repo.get_by_id.return_value = None

        # 调用服务方法并验证异常
        with pytest.raises(UserNotFoundError) as excinfo:
            self.order_service.create_order(999, order_create)

        # 验证异常消息
        assert "User not found" in str(excinfo.value)

        # 验证仓库方法被调用
        self.mock_user_repo.get_by_id.assert_called_once_with(999)

    def test_create_order_product_not_found(self):
        """Test creating an order with a non-existent product."""
        # Create order data
        order_create = OrderCreate(items=[{"product_id": 999, "quantity": 1}])

        # Configure mock to return a user object
        self.mock_user_repo.get_by_id.return_value = Mock(id=1)

        # Configure mock to return None
        self.mock_product_repo.get_by_id.return_value = None

        # 调用服务方法并验证异常
        with pytest.raises(ProductNotFoundError) as excinfo:
            self.order_service.create_order(1, order_create)

        # 验证异常消息
        assert "Product not found" in str(excinfo.value)

        # Verify repository methods were called
        self.mock_user_repo.get_by_id.assert_called_once_with(1)
        self.mock_product_repo.get_by_id.assert_called_once_with(999)

    def test_create_order_insufficient_stock(self):
        """Test creating an order with insufficient stock."""
        # Create order data
        order_create = OrderCreate(items=[{"product_id": 1, "quantity": 20}])

        # Configure mock to return a user object
        self.mock_user_repo.get_by_id.return_value = Mock(id=1)

        # 配置模拟对象返回库存有限的产品
        mock_product = Mock(
            id=1,
            name="Test Product",
            price=99.99,
            stock=10,  # Only 10 in stock, but trying to order 20
        )
        self.mock_product_repo.get_by_id.return_value = mock_product

        # Call the service method and verify exception
        with pytest.raises(InsufficientStockError) as excinfo:
            self.order_service.create_order(1, order_create)

        # Verify exception message
        assert "Insufficient stock" in str(excinfo.value)

        # Verify repository methods were called
        self.mock_user_repo.get_by_id.assert_called_once_with(1)
        self.mock_product_repo.get_by_id.assert_called_once_with(1)

    def test_get_order_by_id_success(self):
        """Test getting an order by ID successfully."""
        # 配置模拟对象返回订单对象
        mock_order = Mock()
        mock_order.id = 1
        mock_order.user_id = 1
        mock_order.status = "pending"

        self.mock_order_repo.get_by_id.return_value = mock_order

        # Call the service method
        result = self.order_service.get_order_by_id(1)

        # Verify repository method was called
        self.mock_order_repo.get_by_id.assert_called_once_with(1)

        # Verify the result
        assert result.id == 1
        assert result.user_id == 1
        assert result.status == "pending"

    def test_get_order_by_id_not_found(self):
        """Test getting a non-existent order by ID."""
        # Configure mock to return None
        self.mock_order_repo.get_by_id.return_value = None

        # Call the service method and verify exception
        with pytest.raises(OrderNotFoundError) as excinfo:
            self.order_service.get_order_by_id(999)

        # Verify exception message
        assert "Order not found" in str(excinfo.value)

        # Verify repository method was called
        self.mock_order_repo.get_by_id.assert_called_once_with(999)

    def test_update_order_status_success(self):
        """Test updating an order status successfully."""
        # 创建更新数据
        order_update = OrderUpdate(status="completed")

        # Configure mock to return an order object
        mock_order = Mock(id=1, status="pending")
        self.mock_order_repo.get_by_id.return_value = mock_order

        # 配置模拟对象返回更新后的订单
        updated_order = Mock(id=1, status="completed")
        self.mock_order_repo.update.return_value = updated_order

        # Call the service method
        result = self.order_service.update_order(1, order_update)

        # Verify repository methods were called
        self.mock_order_repo.get_by_id.assert_called_once_with(1)
        self.mock_order_repo.update.assert_called_once()

        # Verify the result
        assert result.id == 1
        assert result.status == "completed"

    def test_update_order_not_found(self):
        """Test updating a non-existent order."""
        # Create update data
        order_update = OrderUpdate(status="completed")

        # Configure mock to return None
        self.mock_order_repo.get_by_id.return_value = None

        # Call the service method and verify exception
        with pytest.raises(OrderNotFoundError) as excinfo:
            self.order_service.update_order(999, order_update)

        # Verify exception message
        assert "Order not found" in str(excinfo.value)

        # Verify repository method was called
        self.mock_order_repo.get_by_id.assert_called_once_with(999)
        self.mock_order_repo.update.assert_not_called()

    def test_delete_order_success(self):
        """Test deleting an order successfully."""
        # Configure mock to return an order object
        mock_order = Mock(id=1)
        self.mock_order_repo.get_by_id.return_value = mock_order

        # Call the service method
        self.order_service.delete_order(1)

        # Verify repository methods were called
        self.mock_order_repo.get_by_id.assert_called_once_with(1)
        self.mock_order_repo.delete.assert_called_once_with(1)

    def test_delete_order_not_found(self):
        """Test deleting a non-existent order."""
        # Configure mock to return None
        self.mock_order_repo.get_by_id.return_value = None

        # Call the service method and verify exception
        with pytest.raises(OrderNotFoundError) as excinfo:
            self.order_service.delete_order(999)

        # Verify exception message
        assert "Order not found" in str(excinfo.value)

        # Verify repository method was called
        self.mock_order_repo.get_by_id.assert_called_once_with(999)
        self.mock_order_repo.delete.assert_not_called()

    def test_list_orders(self):
        """Test listing all orders."""
        # 创建模拟订单列表
        mock_orders = [Mock(id=i, user_id=1) for i in range(1, 4)]

        # 配置模拟对象返回订单列表
        self.mock_order_repo.list.return_value = mock_orders

        # Call the service method
        result = self.order_service.list_orders()

        # Verify repository method was called
        self.mock_order_repo.list.assert_called_once()

        # Verify the result
        assert len(result) == 3
        assert result[0].id == 1
        assert result[1].id == 2
        assert result[2].id == 3


@pytest.mark.unit
@pytest.mark.parametrize(
    "service_method,exception_type,error_message",
    [
        ("create_user", ValidationError, "Invalid data"),
        ("update_user", ValidationError, "Invalid data"),
        ("create_order", ValidationError, "Invalid data"),
        ("update_order", ValidationError, "Invalid data"),
    ],
)
@patch("app.core.services.user_service.UserService.create_user")
def test_service_error_handling(
    mock_create_user,
    service_method: str,
    exception_type: Exception,
    error_message: str,
):
    """Test error handling in services.

    Args:
        mock_create_user: Mocked UserService.create_user method
        service_method: Service method name
        exception_type: Expected exception type
        error_message: Expected error message
    """
    # 配置模拟对象抛出异常
    mock_create_user.side_effect = exception_type(error_message)

    # 创建模拟仓库
    mock_user_repo = Mock(spec=UserRepository)

    # 创建服务实例
    user_service = UserService(user_repository=mock_user_repo)

    # 创建用户数据
    user_create = UserCreate(
        username="test",
        email="test@example.com",
        password="test123",
        full_name="Test",
    )

    # Call the service method and verify exception
    with pytest.raises(exception_type) as excinfo:
        user_service.create_user(user_create)

    # Verify exception message
    assert error_message in str(excinfo.value)
