from flask import session,render_template
from . import news_blue


@news_blue.route('/')
def index():
    session['name'] = 'xxx'
    return render_template('news/index.html')



