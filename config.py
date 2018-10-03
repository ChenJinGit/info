import os, base64, redis


class Config(object):
    # 设置密钥
    SECRET_KEY = base64.b64encode(os.urandom(64)).decode()

    # mysql配置
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/info'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis配置
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # session配置
    SESSION_TYPE = 'redis'  # 指定session保存到redis中
    SESSION_USE_SIGNER = True  # 让 cookie中的 session_id 被加密签名处理
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 使用 redis 的实例
    PERMANENT_SESSION_LIFETIME = 86400  # session 的有效期，单位是秒


class DevelopementConfig(Config):
    """开发模式下的配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产模式下的配置"""
    pass


# 定义配置字典
config = {
    "development": DevelopementConfig,
    "production": ProductionConfig,
}
