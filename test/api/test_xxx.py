"""xxx端点的测试。

此模块包含对app/api/v1/endpoints/xxx.py中定义的用户和订单端点的测试。
"""

from typing import Any, Dict

import pytest
from fastapi import status

from app.adapters.db.models.order import Order as OrderModel
from app.adapters.db.models.order import OrderItem as OrderItemModel
from app.adapters.db.models.product import Product as ProductModel
from app.adapters.db.models.user import User as UserModel


@pytest.mark.api
class TestUserEndpoints:
    """用户相关端点的测试。"""

    def test_create_user(self, client, sample_payloads: Dict[str, Any]):
        """测试创建新用户。

        参数:
            client: 测试客户端fixture
            sample_payloads: 样本请求体fixture
        """
        # 发送POST请求创建用户
        response = client.post(
            "/api/v1/users", json=sample_payloads["user_create"]
        )

        # 断言响应状态码
        assert response.status_code == status.HTTP_201_CREATED

        # 断言响应体
        response_data = response.json()
        assert "id" in response_data
        assert (
            response_data["username"]
            == sample_payloads["user_create"]["username"]
        )
        assert (
            response_data["email"] == sample_payloads["user_create"]["email"]
        )
        assert (
            response_data["full_name"]
            == sample_payloads["user_create"]["full_name"]
        )
        assert "password" not in response_data  # 不应返回密码

    def test_get_users(self, client, db):
        """测试获取所有用户。

        参数:
            client: 测试客户端fixture
            db: 数据库会话fixture
        """
        # 创建一些测试用户
        users = [
            UserModel(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password_hash="hashed_password",
                full_name=f"User {i}",
                is_active=True,
                is_superuser=False,
            )
            for i in range(3)
        ]

        for user in users:
            db.add(user)
        db.commit()

        # 发送GET请求获取用户列表
        response = client.get("/api/v1/users")

        # 断言响应状态码
        assert response.status_code == status.HTTP_200_OK

        # 断言响应体
        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) >= 3  # 至少应返回3个用户

    def test_get_user_by_id(self, client, test_user):
        """测试通过ID获取用户。

        参数:
            client: 测试客户端fixture
            test_user: 测试用户fixture
        """
        # 发送GET请求通过ID获取用户
        response = client.get(f"/api/v1/users/{test_user.id}")

        # 断言响应状态码
        assert response.status_code == status.HTTP_200_OK

        # 断言响应体
        response_data = response.json()
        assert response_data["id"] == test_user.id
        assert response_data["username"] == test_user.username
        assert response_data["email"] == test_user.email

    def test_update_user(self, client, test_user, user_token):
        """测试更新用户信息。

        参数:
            client: 测试客户端fixture
            test_user: 测试用户fixture
            user_token: JWT令牌fixture
        """
        # 准备更新数据
        update_data = {
            "full_name": "更新的名称",
            "email": "updated@example.com",
        }

        # 发送PUT请求更新用户
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # 断言响应状态码
        assert response.status_code == status.HTTP_200_OK

        # 断言响应体
        response_data = response.json()
        assert response_data["id"] == test_user.id
        assert response_data["full_name"] == update_data["full_name"]
        assert response_data["email"] == update_data["email"]

    def test_delete_user(self, client, test_user, admin_token):
        """测试删除用户（需要管理员权限）。

        参数:
            client: 测试客户端fixture
            test_user: 测试用户fixture
            admin_token: 管理员JWT令牌fixture
        """
        # 发送DELETE请求删除用户
        response = client.delete(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # 断言响应状态码
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 验证用户已被删除
        response = client.get(f"/api/v1/users/{test_user.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestOrderEndpoints:
    """订单相关端点的测试。"""

    def test_create_order(
        self, client, db, test_user, user_token, test_product
    ):
        """测试创建新订单。

        参数:
            client: 测试客户端fixture
            db: 数据库会话fixture
            test_user: 测试用户fixture
            user_token: JWT令牌fixture
            test_product: 测试产品fixture
        """
        # 准备订单数据
        order_data = {
            "items": [{"product_id": test_product.id, "quantity": 2}]
        }

        # 发送POST请求创建订单
        response = client.post(
            "/api/v1/orders",
            json=order_data,
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # 断言响应状态码
        assert response.status_code == status.HTTP_201_CREATED

        # 断言响应体
        response_data = response.json()
        assert "id" in response_data
        assert response_data["user_id"] == test_user.id
        assert response_data["status"] == "pending"
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["product_id"] == test_product.id
        assert response_data["items"][0]["quantity"] == 2
        assert response_data["items"][0]["price"] == test_product.price

    def test_get_orders(self, client, db, test_user):
        """测试获取所有订单。

        参数:
            client: 测试客户端fixture
            db: 数据库会话fixture
            test_user: 测试用户fixture
        """
        # 创建测试产品
        products = [
            ProductModel(
                name=f"Product {i}",
                description=f"Description {i}",
                price=10.0 * (i + 1),
                stock=100,
            )
            for i in range(2)
        ]

        for product in products:
            db.add(product)
        db.commit()

        # 创建测试订单
        orders = []
        for i in range(2):
            order = OrderModel(
                user_id=test_user.id,
                status="pending" if i == 0 else "completed",
            )
            db.add(order)
            db.flush()  # 在不提交的情况下获取订单ID

            # 添加订单项
            item = OrderItemModel(
                order_id=order.id,
                product_id=products[i].id,
                quantity=i + 1,
                price=products[i].price,
            )
            db.add(item)
            orders.append(order)

        db.commit()

        # 发送GET请求获取订单列表
        response = client.get("/api/v1/orders")

        # 断言响应状态码
        assert response.status_code == status.HTTP_200_OK

        # 断言响应体
        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) >= 2  # 至少应返回2个订单

    def test_get_order_by_id(self, client, db, test_user, test_product):
        """测试通过ID获取订单。

        参数:
            client: 测试客户端fixture
            db: 数据库会话fixture
            test_user: 测试用户fixture
            test_product: 测试产品fixture
        """
        # 创建测试订单
        order = OrderModel(user_id=test_user.id, status="pending")
        db.add(order)
        db.flush()  # 在不提交的情况下获取订单ID

        # 添加订单项
        item = OrderItemModel(
            order_id=order.id,
            product_id=test_product.id,
            quantity=1,
            price=test_product.price,
        )
        db.add(item)
        db.commit()
        db.refresh(order)

        # 发送GET请求通过ID获取订单
        response = client.get(f"/api/v1/orders/{order.id}")

        # 断言响应状态码
        assert response.status_code == status.HTTP_200_OK

        # 断言响应体
        response_data = response.json()
        assert response_data["id"] == order.id
        assert response_data["user_id"] == test_user.id
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["product_id"] == test_product.id

    def test_update_order_status(
        self, client, db, test_user, test_product, admin_token
    ):
        """测试更新订单状态（需要管理员权限）。

        参数:
            client: 测试客户端fixture
            db: 数据库会话fixture
            test_user: 测试用户fixture
            test_product: 测试产品fixture
            admin_token: 管理员JWT令牌fixture
        """
        # 创建测试订单
        order = OrderModel(user_id=test_user.id, status="pending")
        db.add(order)
        db.commit()
        db.refresh(order)

        # 准备更新数据
        update_data = {"status": "completed"}

        # 发送PUT请求更新订单状态
        response = client.put(
            f"/api/v1/orders/{order.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # 断言响应状态码
        assert response.status_code == status.HTTP_200_OK

        # 断言响应体
        response_data = response.json()
        assert response_data["id"] == order.id
        assert response_data["status"] == update_data["status"]

    def test_delete_order(self, client, db, test_user, admin_token):
        """测试删除订单（需要管理员权限）。

        参数:
            client: 测试客户端fixture
            db: 数据库会话fixture
            test_user: 测试用户fixture
            admin_token: 管理员JWT令牌fixture
        """
        # 创建测试订单
        order = OrderModel(user_id=test_user.id, status="pending")
        db.add(order)
        db.commit()
        db.refresh(order)

        # 发送DELETE请求删除订单
        response = client.delete(
            f"/api/v1/orders/{order.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # 断言响应状态码
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 验证订单已被删除
        response = client.get(f"/api/v1/orders/{order.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
@pytest.mark.parametrize(
    "invalid_payload,expected_status,expected_detail",
    [
        (
            "not_a_json",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Unprocessable Entity",
        ),
        (
            {"username": "", "email": "invalid"},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "username",
        ),
        (
            {"username": "test", "email": "not-an-email"},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "email",
        ),
    ],
)
def test_user_validation_errors(
    client, invalid_payload: Any, expected_status: int, expected_detail: str
):
    """测试用户端点的验证错误。

    参数:
        client: 测试客户端fixture
        invalid_payload: 要测试的无效请求体
        expected_status: 期望的HTTP状态码
        expected_detail: 期望的错误详情
    """
    # 发送包含无效请求体的POST请求
    response = client.post("/api/v1/users", json=invalid_payload)

    # 断言响应状态码
    assert response.status_code == expected_status

    # 断言错误详情存在
    if isinstance(invalid_payload, dict):
        response_data = response.json()
        assert "detail" in response_data
        if isinstance(response_data["detail"], list):
            assert any(
                expected_detail in str(error)
                for error in response_data["detail"]
            )
        else:
            assert expected_detail in response_data["detail"]


@pytest.mark.api
def test_unauthorized_access(client, test_user):
    """测试对受保护端点的未授权访问。

    参数:
        client: 测试客户端fixture
        test_user: 测试用户fixture
    """
    # 尝试在没有令牌的情况下访问受保护端点
    response = client.put(
        f"/api/v1/users/{test_user.id}", json={"full_name": "Should Fail"}
    )

    # 断言响应状态码
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 尝试使用无效令牌
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        json={"full_name": "Should Fail"},
        headers={"Authorization": "Bearer invalid_token"},
    )

    # 断言响应状态码
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.api
def test_not_found(client):
    """测试访问不存在的资源。

    参数:
        client: 测试客户端fixture
    """
    # 尝试访问不存在的用户
    response = client.get("/api/v1/users/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # 尝试访问不存在的订单
    response = client.get("/api/v1/orders/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
