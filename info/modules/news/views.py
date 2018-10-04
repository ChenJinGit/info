from flask import current_app, session, render_template, request, jsonify, abort, g
from info.utils.common import login_request
from . import news_blue
from info.models import User, News, Category, Comment
from info import constants, db
from info.utils.response_code import RET


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
    # 获取点击排行的数据
    news_list = None
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.HOME_PAGE_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    # 新闻点击排行列表
    click_news_list = []
    for news in news_list if news_list else []:
        click_news_list.append(news.to_basic_dict())

    # 新闻分类
    # 获取新闻分类
    categories = Category.query.all()
    # 定义保存分类列表
    categories_dicts = []
    # 遍历分类以及分类索引保存
    for category in categories:
        categories_dicts.append(category)

    data = {"user_info": user.to_dict() if user else None,
            "click_news_list": click_news_list,
            "categories": categories_dicts
            }

    return render_template('news/index.html', data=data)


@news_blue.route('/newslist')
def get_news_list():
    """
    首页新闻列表数据
    1、尝试获取参数，cid、page、per_page
    2、如果没有需要给默认值
    request.args.get("cid",'1')
    3、把页数和每页的条目数进行强转int
    4、根据分类id查询数据库，按照新闻的发布时间进行排序，使用paginate进行分页
    5、获取分页对象
    6、使用分页对象，获取分页后的新闻数据
    paginate = News.query.filter(News.category_id==cid).order_by(News.create_time.desc()).paginate(page,per_page,False)
    news_data = paginate.items --->总新闻数据
    total_page = paginate.pages ---> 总页数
    current_page = paginate.page --->当前页数
    7、遍历分页后的总页数，定义容器，调用to_dict()
    8、返回结果：总页数、当前页数、新闻列表数据
    :return:
    """
    # 1. 获取参数
    cid = request.args.get('cid', '1')
    page = request.args.get('page', '1')
    par_page = request.args.get('per_page', '10')
    # 2、如果没有需要给默认值
    try:
        page, par_page = int(page), int(par_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 3. 查询数据并分页
    filters = []
    # 如果分类id不为1，那么添加分类id的过滤
    if cid != '1':
        filters.append(News.category_id == cid)
    # 根据分类id查询数据库
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, par_page, False)
        # 获取查询数据
        items = paginate.items
        # 获取总页数
        total_page = paginate.pages
        current_page = paginate.page
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.NODATA, errmsg='查询数据失败')
    # 新建新闻列表存储列表新闻
    news_li = []
    # 从所有新闻数据中获取每一条新闻并保存到新闻列表
    for news in items:
        news_li.append(news.to_basic_dict())
    # 返回数据
    return jsonify(errno=RET.OK, errmsg='OK', totalPage=total_page,
                   currentPage=current_page, newsList=news_li, cid=cid)


@news_blue.route('/news/<int:user_id>')
@login_request
def news_detail(user_id):
    """
    获取新闻详情信息
    １,获取详情数据
    2,判断新闻详情数据
    3,返回新闻详情数据
    :param user_id:
    :return:
    """

    # １,获取详情数据
    try:
        news_detail_data = News.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        abort(404)
        return jsonify(errno=RET.DBERR, errmsg='查询数据失败')
    # 2,点击排行数据
    news_list = []
    # 获取点击排行数据
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
    click_news_list = []
    for news in news_list if news_list else []:
        click_news_list.append(news)

    is_collected = False
    if g.user:
        if news_detail_data in g.user.collection_news:
            is_collected = True

    data = {
        "news": news_detail_data,
        "is_collected": is_collected,
        "click_news_list": click_news_list,
        "user_info": g.user.to_dict() if g.user else None,
    }

    return render_template('news/detail.html', data=data)


@news_blue.route('/news/news_collect', methods=['POST'])
@login_request
def news_collect():
    """
    收藏新闻
    :return:
    """
    # 收藏新闻
    # 判定用户是否收藏，收藏为True,默认为False
    is_collected = False
    user = g.user
    news_id = request.json.get('news_id')
    action = request.json.get('action')

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    if not news_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    if action not in ('collect', 'cancel_collect'):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 获取新闻
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询新闻数据失败')
    # 判断新闻数据是否存在
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='无新闻数据')
    # 判断是否收藏
    if action == 'collect':
        user.collection_news.append(news)
    else:
        user.collection_news.remove(news)
    # 操作数据库，保存收藏状态

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='操作成功')


@news_blue.route('/news/news_comment', methods=['POST'])
@login_request
def news_comment():
    """
    新闻评论
    :return:
    """
    # 1,获取当前用户，判断是否登陆
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='未登陆')
    # 2,获取当前新闻id,评论,父id
    news_id = request.json.get('news_id')
    comment_str = request.json.get('comment')
    parent_id = request.json.get('parent_id')
    print(parent_id, news_id)
    # 2.1校验参数完整性
    if not all([news_id, comment_str]):
        return jsonify(errno=RET.NODATA, errmsg='参数缺失')
    # 3,从数据库获取新闻
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取新闻数据失败')
    # 3.1,判断信新闻是否存在
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='该新闻不存在')
    # 4,保存评论，初始化模型
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_str
    # 4.1判读父id是否存在
    if parent_id:
        comment.parent_id = parent_id
    # 5,保存到数据库
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存评论数据失败')
    # 6,返回保存结果
    return jsonify(errno=RET.OK, errmsg='保存评论成功', data=comment.to_dict())
















@news_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
