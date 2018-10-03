from logging.handlers import RotatingFileHandler
import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config, config
from flask_session import Session
import logging
from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import generate_csrf

# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG)  # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
# 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)

# MYSQL实例
db = SQLAlchemy()

# redis实例
redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)


def create_app(config_name):
    """通过传入不同的配置名字，初始化其对应配置的应用实例"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # MYSQL实例
    # db = SQLAlchemy(app)
    db.init_app(app)

    # 开启CSRF保护
    CSRFProtect(app)

    # session实例
    Session(app)

    # 请求钩子实现csrf_token
    @app.after_request
    def after_request(response):
        # 调用函数生成 csrf_token
        crsf_token = generate_csrf()
        response.set_cookie("csrf_token", crsf_token)
        return response

    # 注册首页蓝图
    from .modules.news.views import news_blue
    app.register_blueprint(news_blue)
    # 图片验证码
    from .modules.passport.views import passport_blue
    app.register_blueprint(passport_blue)

    return app
