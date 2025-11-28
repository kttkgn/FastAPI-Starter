"""辅助函数集合 - 整合从其他模块提取的公共逻辑。"""
import datetime
import re
import uuid
from datetime import timezone
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TypeVar

T = TypeVar("T")
U = TypeVar("U")


def generate_uuid() -> str:
    """生成UUID字符串。"""
    return str(uuid.uuid4())


def validate_pattern(value: str, pattern: str) -> bool:
    """使用正则表达式验证字符串模式。

    Args:
        value: 要验证的值
        pattern: 正则表达式模式

    Returns:
        验证是否通过
    """
    return bool(re.match(pattern, value))


def is_valid_email(email: str) -> bool:
    """验证邮箱格式。"""
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return validate_pattern(email, email_regex)


def is_valid_url(url: str) -> bool:
    """验证URL格式。"""
    url_regex = (
        r"^https?://(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}"
        r"\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"
    )
    return validate_pattern(url, url_regex)


def format_datetime(
    dt: Optional[datetime.datetime] = None,
    format_str: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """格式化日期时间为字符串。"""
    if dt is None:
        dt = datetime.datetime.now(timezone.utc)
    return dt.strftime(format_str)


def parse_datetime(
    datetime_str: str, format_str: str = "%Y-%m-%d %H:%M:%S"
) -> Optional[datetime.datetime]:
    """解析日期时间字符串。"""
    try:
        return datetime.datetime.strptime(datetime_str, format_str)
    except ValueError:
        return None


def safe_cast(value: Any, target_type: type, default: Any = None) -> Any:
    """安全地将值转换为目标类型。"""
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return default


def paginate(
    data: List[T],
    page: int,
    page_size: int
) -> Tuple[List[T], Dict[str, Any]]:
    """对列表进行分页并返回分页数据和元数据。

    Args:
        data: 要分页的数据列表
        page: 页码（从1开始）
        page_size: 每页项目数

    Returns:
        包含分页后数据和元数据的元组
    """
    # 验证输入
    page = max(1, page)
    page_size = max(1, page_size)

    # 计算分页
    total_items = len(data)
    total_pages = (total_items + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    # 获取分页后的数据
    paginated_items = data[start_idx:end_idx]

    # 构建分页元数据
    pagination_meta = {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }

    return paginated_items, pagination_meta


def deep_get(
    d: Dict[str, Any],
    keys: Union[str, List[str]],
    default: Any = None
) -> Any:
    """使用点表示法安全获取嵌套字典中的值。"""
    # 转换字符串键为列表
    if isinstance(keys, str):
        keys = keys.split(".")

    # 遍历字典
    current = d
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def deep_set(
    d: Dict[str, Any],
    keys: Union[str, List[str]],
    value: Any
) -> None:
    """使用点表示法设置嵌套字典中的值。"""
    # 转换字符串键为列表
    if isinstance(keys, str):
        keys = keys.split(".")

    # 遍历字典，按需创建嵌套字典
    current = d
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # 设置最终值
    current[keys[-1]] = value


def remove_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """递归移除字典中的None值。"""
    if not isinstance(d, dict):
        return d

    return {
        k: remove_none_values(v) if isinstance(v, dict) else v
        for k, v in d.items()
        if v is not None
    }


def retry(max_attempts: int = 3, exceptions: tuple = (Exception,)) -> Callable:
    """重试装饰器 - 支持同步和异步函数。"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            attempts = 0
            last_exception = None

            while attempts < max_attempts:
                attempts += 1
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempts == max_attempts:
                        raise

            # 这一行理论上不会被执行，因为上面的循环在最后一次尝试失败时会抛出异常
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            attempts = 0
            last_exception = None

            while attempts < max_attempts:
                attempts += 1
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempts == max_attempts:
                        raise

            # 这一行理论上不会被执行，因为上面的循环在最后一次尝试失败时会抛出异常
            raise last_exception

        # 根据函数类型选择合适的包装器
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def map_dict_values(func: Callable[[T], U], d: Dict[Any, T]) -> Dict[Any, U]:
    """将函数应用于字典的所有值。"""
    return {k: func(v) for k, v in d.items()}


def filter_dict_by_keys(d: Dict[Any, Any], keys_to_keep: List[Any]) -> Dict[Any, Any]:
    """根据键列表过滤字典。"""
    return {k: v for k, v in d.items() if k in keys_to_keep}


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[
    str, Any]:
    """将嵌套字典扁平化为单层字典，使用指定分隔符连接键名。"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
