import re
from typing import Callable, Iterable, Any, TypeVar
from app.config.settings import SKIP_PATH_PATTERNS


# 在模块被首次加载时编译，实现高效的缓存
_COMPILED_PATTERNS = [re.compile(p) for p in SKIP_PATH_PATTERNS]

# 定义一个泛型变量 T，表示列表中的元素类型
T = TypeVar('T')

def some_of_match(iterable: Iterable[T], predicate: Callable[[T], bool]):
    """
    检查可迭代对象中的元素是否满足 predicate 指定的条件
    :param iterable: 任何可迭代对象 (list, tuple, set 等)
    :param predicate: 接收一个参数并返回 bool 的函数
    """
    return any(predicate(item) for item in iterable)

# 每一个都满足
def all_of_match(iterable: Iterable[T], predicate: Callable[[T], bool]):
    """
    检查可迭代对象中的元素是否都满足 predicate 指定的条件
    :param iterable: 任何可迭代对象 (list, tuple, set 等)
    :param predicate: 接收一个参数并返回 bool 的函数
    """
    return all(predicate(item) for item in iterable)

def is_skip_path(path: str) -> bool:
    """
    判断路径是否匹配提供的正则模式列表
    :param path: 当前请求的路径字符串
    :param patterns: 正则表达式字符串的集合 (默认为全局 SKIP_PATH_PATTERNS)
    """
    return some_of_match(_COMPILED_PATTERNS, lambda p: bool(p.match(path)))
