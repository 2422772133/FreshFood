from django.conf.urls import url
from apps.user import views
from apps.user.views import RegisterView, ActiveView, LoginView, LogoutView, UserInfoView, UserOrderView, UserAddressView
from django.contrib.auth.decorators import login_required


urlpatterns = [
    # url(r'^register$', views.register, name='register')
    url(r'^register$', RegisterView.as_view(), name='register'),
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(),name='active'),
    # url(r'^register_handle$', views.register_handle, name='register_handle'),  # 注册处理
    url(r'^login$', LoginView.as_view(), name='login'),  # 登录
    url(r'^logout$', LogoutView.as_view(), name='logout'),  # 注销
    # url(r'^order$', login_required(UserOrderView.as_view()), name='order'),
    # url(r'^address$',login_required(UserAddressView.as_view()), name='address'),
    #
    # url(r'^$', login_required(UserInfoView.as_view()), name='user'),
    url(r'^order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),
    url(r'^address$', UserAddressView.as_view(), name='address'),

    url(r'^$', UserInfoView.as_view(), name='user'),


]
