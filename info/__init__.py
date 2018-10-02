import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config, config
from flask_session import Session


def create_app(config_name):
    """通过传入不同的配置名字，初始化其对应配置的应用实例"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # MYSQL实例
    db = SQLAlchemy(app)

    # redis实例
    redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

    # session实例
    Session(app)

    # 注册蓝图
    from .moudels.news.views import news_blue
    app.register_blueprint(news_blue)

    return app
