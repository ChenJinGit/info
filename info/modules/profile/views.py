from . import profile_blue
from info.utils.common import login_request
from flask import render_template, g, request


@profile_blue.route('/base_info', methods=['GET', 'POST'])
@login_request
def base_info():
    """
    用户基本信息
    1. 获取用户登录信息
    2. 获取到传入参数
    3. 更新并保存数据
    4. 返回结果
    :return:
    """
    # 1.获取用户登录信息
    user = g.user
    print(user)
    if request.method == 'GET':
        return render_template('news/user_base_info.html', data={'user_info': user.to_dict()})
    # 2.获取到传入参数

    # 3.更新并保存数据

    # 4.返回结果

