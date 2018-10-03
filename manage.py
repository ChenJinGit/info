from flask_migrate import Migrate, MigrateCommand
from info import create_app, db, models
from flask_script import Manager


# 调用工厂函数创建app
app = create_app('development')

# 数据库迁移管理
manage = Manager(app)
Migrate(app, db)
manage.add_command('db', MigrateCommand)

if __name__ == '__main__':
    # print(app.url_map)
    manage.run()
