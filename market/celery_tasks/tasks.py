from django.conf import settings
from django.core.mail import send_mail
from celery import Celery
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
import os

# 这两行代码，在启动worker的一端打开注释
# import os
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")

# 创建一个Celery类的对象
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/13')


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    """发送激活邮件"""
    # 组织邮件的内容
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = """
                        <h1>%s, 欢迎您成为天天生鲜注册会员</h1>
                        请点击以下链接激活您的账号<br/>
                        <a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>
                    """ % (username, token, token)

    # 发生激活邮件
    # send_mail(subject='邮件标题', message='邮件正文', from_email='发件人', recipient_list='收件人邮箱列表')
    import time
    time.sleep(5)
    send_mail(subject, message, sender, receiver, html_message=html_message)


@app.task
def generate_static_index_html():
    """生成静态首页文件"""
    # 获取商品种类的信息
    types = GoodsType.objects.all()

    # 获取首页轮播商品的信息
    index_banner = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页促销活动的信息
    promotion_banner = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示的信息
    for type in types:
        # 查询type种类首页展示的文字商品的信息
        title_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

        # 查询type种类首页展示的图片商品的信息
        image_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')

        # 给type对象增加属性title_banner和image_banner
        # 分别保存type种类首页展示的文字商品信息和图片商品信息
        type.title_banner = title_banner
        type.image_banner = image_banner

    # 获取登录用户购物车记录商品的条目数
    cart_count = 0

    # 使用模板
    # 1. 加载模板文件，获取模板对象
    from django.template import loader
    temp = loader.get_template('market/static_index.html')
    context = {'types': types,
               'index_banner': index_banner,
               'promotion_banner': promotion_banner,
               'cart_count': cart_count}
    static_html = temp.render(context)

    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')

    with open(save_path, 'w') as f:
        f.write(static_html)