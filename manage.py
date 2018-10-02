from info import create_app
from flask_script import Manager
from flask_migrate import MigrateCommand

# 调用工厂函数创建app
app = create_app('development')

# 数据库迁移管理
manage = Manager(app)


if __name__ == '__main__':
    print(app.url_map)
    app.run()
