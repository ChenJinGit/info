import random, re, datetime
from flask import request, current_app, jsonify
from flask import session
from flask.helpers import make_response
from info.models import User
from . import passport_blue
from info.utils.captcha.captcha import captcha
from info import redis_store, db
from info import constants
from info.utils.response_code import RET
from info.lib.yuntongxun.sms import CCP


@passport_blue.route('/image_code')
def get_image_code():
    """获取短信验证码"""
    # 1,获取图片id
    code_id = request.args.get('code_id')
    # 生产图片验证码
    name, text, image = captcha.generate_captcha()
    # 保存验证码到redis
    try:
        # 保存当前生成的图片验证码内容
        redis_store.setex('ImageCode_' + code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        return make_response(jsonify(errno=RET.DATAERR, errmsg='保存图片验证码失败'))
    # 返回响应数据
    resp = make_response(image)
    resp.headers['Content-Type'] = 'image/jpg'
    return resp


@passport_blue.route('/smscode', methods=['POST'])
def send_code():
    """发送短信验证码"""
    # 1,获取数据
    mobile = request.json.get('mobile')
    image_code = request.json.get('image_code')
    image_code_id = request.json.get('image_code_id')
    # 检查参数的完整性
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')
    # 2,校验数据
    # 2.１ 校验手机号是正确
    if not re.match(r'^1[3-9]\d{9}$', mobile):
        return jsonify(errno=RET.DATAERR, errmsg='手机号错误')
    # 2.2 通过传入的图片编码去redis中查询真实的图片验证码内容
    try:
        real_image_code = redis_store.get('ImageCode_' + image_code_id)
        # 如果能够取出来值，删除redis中缓存的内容
        if real_image_code:
            real_image_code = real_image_code.decode()
            redis_store.delete('ImageCode_' + 'image_code_id')
    except Exception as e:
        current_app.logger.error(e)
        # 获取图片验证码失败
        return jsonify(errno=RET.DBERR, errmsg='获取图片验证码失败')
    # 2.3 判断图片验证码是否过期
    if not real_image_code:
        # 验证码已过期
        return jsonify(errno=RET.NODATA, errmsg='验证码已过期')
    # 3,比较验证码是否一致
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='验证码错误')

    # 4,校验该手机是否已经注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询错误')
    # 判断手机号是否注册
    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')

    # 5,生成短信验证码
    code = random.randint(0, 999999)
    sms_code = '%06d' % code
    # 5.1记录发送短信异常
    current_app.logger.debug("短信验证码的内容：%s" % sms_code)
    # 5.2　调用第三方工具发送短信验证码
    result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], '1')
    if result != 0:
        return jsonify(errno=RET.THIRDERR, errmsg='短信发送失败')
    # 6,保存短信验证码
    try:
        redis_store.set('SMS_' + mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存短信验证码失败')

    # 7,返回响应内容
    return jsonify(errno=RET.OK, errmsg='短信发送成功')


@passport_blue.route('/register', methods=['POST'])
def register():
    """
    1. 获取参数和判断是否有值
    2. 从redis中获取指定手机号对应的短信验证码的
    3. 校验验证码
    4. 初始化 user 模型，并设置数据并添加到数据库
    5. 保存当前用户的状态
    6. 返回注册的结果
    :return:
    """
    # 1,获取参数,校验参数
    mobile = request.json.get('mobile')
    sms_code = request.json.get('smscode')
    password = request.json.get('password')
    print(sms_code)
    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 2.从redis中获取指定手机号对应的短信验证码的
    try:
        # 从数据看获取的是二进制数据
        real_sms_code = redis_store.get('SMS_' + mobile).decode()
        print(real_sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询失败')
    # 3.校验验证码
    # 3.1判断是否过期
    if not real_sms_code:
        return jsonify(errno=RET.NODATA, errmsg='验证码已过期')
    # 3.2判断验证码是否正确
    if sms_code != real_sms_code:
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码错误')
    # 3.3删除短信验证码
    try:
        redis_store.delete('SMS_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
    # 4. 初始化 user 模型，并设置数据并添加到数据库
    user = User()
    user.nick_name = mobile
    user.mobile = mobile
    user.password = password
    # 4.1 保存到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='保存数据失败')
    # 5.保存当前用户的状态
    session['user_id'] = user.id
    session['nick_name'] = user.nick_name
    session['mobile'] = user.mobile
    # 6.返回注册的结果
    return jsonify(errno=RET.OK, errmsg='注册成功')


@passport_blue.route('/login', methods=['POST'])
def login():
    """
    1. 获取参数和判断是否有值
    2. 从数据库查询出指定的用户
    3. 校验密码
    4. 保存用户登录状态
    5. 返回结果
    :return:
    """
    # 1. 获取参数和判断是否有值
    mobile = request.json.get('mobile')
    password = request.json.get('password')
    if not all([mobile, password]):
        return jsonify(errno=RET.NODATA, errmsg='参数缺失')
    # 2. 从数据库查询出指定的用户
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询用户失败')
    # 2.1判断用户是否存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg='用户未注册')
    # 3. 校验密码
    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR, errmsg='密码错误')
    # 4. 保存用户登录状态
    session['user_id'] = user.id
    session['nick_name'] = user.nick_name
    session['mobile'] = user.mobile
    # 4.1记录用户最后一次登陆的时间
    user.last_login = datetime.datetime.now()
    # 4.2提交到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
    # 5. 返回结果
    return jsonify(errno=RET.OK, errmsg='OK')


@passport_blue.route('/logout', methods=['POST'])
def logout():
    """
    登出实现:清除session中的对应登录之后保存的信息
    :return:
    """
    # 清除session中的对应登录之后保存的信息
    session['user_id'] = None
    session['nick_name'] = None
    session['mobile'] = None
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK')
