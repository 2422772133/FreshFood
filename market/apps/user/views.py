from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View
from django.core.paginator import Paginator
from celery import Celery
from django.contrib.auth.decorators import login_required
from .models import User, Address, AddressManage
from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo,OrderGoods
from utils.mixin import LoginRequiredView, LoginRequiredMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from celery_tasks.tasks import send_register_active_email
import re

# Create your views here.

# def login_required(view_func):
#     def wrapper(request, *args, **kwargs):
#         if request.session.has_key('islogin'):
#             return view_func(request, *args, **kwargs)
#         else:
#             return redirect('/login')
#     return wrapper

def register_1(request):
    """注册信息"""
    return render(request, 'market/register.html')


def register_handle(request):
    """校验信息"""
    # 收到信息
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    # 参数校验（后端校验）
    if not all([username,password,email]):

        return render(request,'market/register.html',{'errmsg': '数据不完整'})
    # 校验邮箱
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):

        return render(request, 'market/register.html', {'errmsg': '邮箱格式不正确'})
    # 校验用户名是否存在
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # 用户名不存在
        user = None
    if user:
        # 用户名已存在
        return render(request, 'market/register.html', {'errmsg': '用户名已存在'})

    # 3. 业务处理：用户注册
    user = User.objects.create_user(username, email, password)
    user.is_active = 0
    user.save()
    # 4. 返回应答：跳转的首页
    return redirect(reverse('goods:index'))


def register(request):
    """注册"""
    if request.method == 'GET':
        return render(request, 'market/register.html')

    elif request.method == 'POST':
        username = request.POST.get('user_name')  # None
        password = request.POST.get('pwd')
        email = request.POST.get('email')

        # 2. 参数校验（后端校验)
        # 校验数据的完整性
        if not all([username, password, email]):
            return render(request, 'market/register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'market/register.html', {'errmsg': '邮箱格式不正确'})

        # 校验用户名是否存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已存在
            return render(request, 'market/register.html', {'errmsg': '用户名已存在'})

        # 3. 业务处理：用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 4. 返回应答：跳转的首页
        return redirect(reverse('goods:index'))


class RegisterView(View):
    """注册"""
    def get(self, request):
        return render(request, 'market/register.html')

    def post(self, request):
        username = request.POST.get('user_name')  # None
        password = request.POST.get('pwd')
        email = request.POST.get('email')

        # 2. 参数校验（后端校验)
        # 校验数据的完整性
        if not all([username, password, email]):
            return render(request, 'market/register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'market/register.html', {'errmsg': '邮箱格式不正确'})

        # 校验用户名是否存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已存在
            return render(request, 'market/register.html', {'errmsg': '用户名已存在'})

        # 3. 业务处理：用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()


        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm':user.id}
        token = serializer.dumps(info) # bytes
        token = token.decode()
        #
        # # 组织邮件信息
        # subject = '天天生鲜欢迎信息'
        # message = ''
        # sender = settings.EMALL_FROM
        # receiver = [email]
        # html_message = """
        # <h1>%s, 欢迎您成为天天生鲜注册会员</h1>
        #             请点击以下链接激活您的账号<br/>
        #              <a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>
        #                 """ % (username, token, token)
        # send_mail(subject,message,sender,receiver,html_message=html_message)
        send_register_active_email.delay(email, username, token)
        # 4. 返回应答：跳转的首页
        return redirect(reverse('goods:index'))


class ActiveView(View):
    """激活"""
    def get(self, request, token):
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)

            user_id = info['confirm']

            user = User.objects.get(id=user_id)

            user.is_active = 1

            user.save()

            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            return HttpResponse('<h1>激活连接已失效</h1>')


class LoginView(View):
    """登录"""
    def get(self, request):
        """显示"""
        # 尝试从cookie中获取username
        if 'username' in request.COOKIES:
            # 获取username
            username = request.COOKIES['username']
            checked = 'checked'
        else:
            username = ''
            checked = ''
        # 使用模板
        return render(request, 'market/login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """登录验证"""
        # 接收参数
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 参数校验
        if not all([username, password]):
            return render(request, 'market/login.html', {'errmsg': '数据不完整'})

        # 业务处理：登录验证
        # 根据用户名和密码查找用户的信息
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 账户已激活
                # 记住用户的登录状态
                login(request, user)

                # 获取登录后跳转的url
                next_url = request.GET.get('next', reverse('goods:index'))

                print(next_url)

                # 返回应答：跳转到首页
                # HttpResponseRedirect类->HttpRespose类的子类
                response = redirect(next_url)
                # / user / address
                # 判断是否需要记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    # 清除用户名
                    response.delete_cookie('username')

                # 返回应答：跳转到首页
                return response
            else:
                # 账户未激活
                return render(request, 'market/login.html', {'errmsg': '账户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'market/login.html', {'errmsg': '用户名或密码错误'})


# request对象有一个属性user：request.user
# 如果用户已登录，user是一个认证系统用户模型类的对象(User)
# 如果用户未登录，user是一个匿名用户类(AnonymousUser)的对象
# User和AnonymousUser类中都有一个方法is_authenticated
# User中的is_authenticated永远返回True
# AnonymousUser中的is_authenticated永远返回False
# 在模板文件中可以直接使用user对象


# /user/logout
class LogoutView(View):
    """注销"""
    def get(self, request):
        """注销登录"""
        # 清除用户的登录状态
        logout(request)

        # 返回应答：跳转到登录页面
        return redirect(reverse('user:login'))


#  /user/
# class UserInfoView(View):
# class UserInfoView(LoginRequiredView):
class UserInfoView(LoginRequiredMixin,View):
    """用户中心--信息页"""
    def get(self, request):
        """显示"""
        # 获取用户默认的地址
        user = request.user
        address = Address.objects.get_default_address(user)
        # 获取用户的历史浏览记录
        from redis import StrictRedis
        conn = StrictRedis(host='127.0.0.1', port=6379, db=13)
        # 拼接key
        history_key = 'history_%s'%user.id
        # 获取用户最新的5个商品浏览记录
        sku_ids = conn.lrange(history_key,0,4)
        # 查询对应的商品信息
        skus = GoodsSKU.objects.filter(id__in=sku_ids)

        skus_li=[]
        for sku_id in sku_ids:
            for sku in skus:
                if sku.id == int(sku_id):
                    skus_li.append(sku)

        # 组织模板上下文
        context =  {'page': 'user',
                    'address': address,
                    'skus': skus_li
                    }
        # 使用模板




        return render(request, 'market/user_center_info.html',context)

#  /user/order
# class UserOrderView(View):
# class UserOrderView(LoginRequiredView):
class UserOrderView(LoginRequiredMixin, View):
    """用户中心--订单页"""
    def get(self, request, page):
        """显示"""
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')
        for order in orders:
            order_skus = OrderGoods.objects.filter(order=order)
            for order_sku in order_skus:
                amount = order_sku.count * order_sku.price
                order_sku.amount = amount

            total_pay = order.total_price + order.transit_price
            order.total_pay = total_pay

            status_name = OrderInfo.ORDER_STATUS[order.order_status]
            order.status_name= status_name

            order.order_skus = order_skus

        paginator = Paginator(orders,1)
        page=int(page)
        if page > paginator.num_pages:
            page = 1
        order_page = paginator.page(page)
        num_pages = paginator.num_pages
        if num_pages <5:
            pages = range(1, num_pages + 1)
        elif page <=3:
            pages = range(1,6)
        elif num_pages - page <=2:
            pages = range(num_pages-4 , num_pages +1)
        else:
            pages = range(page - 2, page + 3)


        context = {
            'order_page':order_page,
            'pages':pages,
            'page': 'order'
        }
        return render(request, 'market/user_center_order.html',context)

#  /user/address
# @login_required
# class UserAddressView(View):
# class UserAddressView(LoginRequiredView):
class UserAddressView(LoginRequiredMixin, View):
    """用户中心--地址页"""
    def get(self,request):
        """显示"""
        user = request.user
        try:
            address = Address.objects.get(user=user, is_default=True)
        except Address.DoesNotExist:
            address = None

        content = {'page': 'address','address':address}
        return render(request, 'market/user_center_site.html',content)

    def post(self,request):
        """post方式"""
        # 接受信息
        receiver = request.POST.get('receiver')
        phone = request.POST.get('phone')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        # 校验信息

        if not all([receiver,phone, addr]):
            return render(request,'market/user_center_site.html',{'errmsg': '数据不完整'})
        # 处理信息
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None
        address = Address.objects.get_default_address(user)
        print(address)
        # 返回应答
        is_default = True
        if address:
            is_default = False

        Address.objects.create(user=user, phone = phone, addr=addr,zip_code=zip_code,receiver=receiver,is_default=is_default)
        return redirect(reverse('user:address'))






