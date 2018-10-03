from flask import current_app, session, render_template
from . import news_blue
from info.models import User


@news_blue.route('/')
def index():
    """
    需要在用户请求首页的时候去数据库查询用户数据
    如果查询到用户数据，则传入模板中，进行渲染，再进行返回
    如果未查询到，返回用户数据为 None，模板代码中自行判断
    """
    # 获取当前登陆用户id
    user_id = session.get('user_id')
    # 通过id获取用户信息
    user = None
    if user_id:
        # 用户存在，从数据库中读取
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    return render_template('news/index.html', data={"user_info": user.to_dict() if user else None})


@news_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
