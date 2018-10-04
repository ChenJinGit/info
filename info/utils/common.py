import functools
from flask import current_app, g, session
from info.models import User


def index_class(index):
    """自定义过滤器，过滤点击排序html的class"""
    if index == 0:
        return "first"
    elif index == 1:
        return "second"
    elif index == 2:
        return "third"
    else:
        return ""


# 定义装饰器实现用户状态信息的获取
def login_request(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # 获取用户id
        user_id = session.get('user_id')
        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
            # 使用应用上下文g变量存储用户信息, 传给视图函数
        g.user = user
        return f(*args, **kwargs)

    return wrapper
