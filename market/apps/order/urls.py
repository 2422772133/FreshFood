from django.conf.urls import url
from apps.order.views import OrderPlaceView,OrderCommitView,OrderPayView,OrderCheckView
urlpatterns = [
    # url(r'^register$', views.register, name='register')
    # url(r'^register$', views.register, name='register'),
    url(r'^place$', OrderPlaceView.as_view(), name='place'),
    url(r'^commit$', OrderCommitView.as_view(),name='commit'),
    url(r'^pay$', OrderPayView.as_view(), name='pay'), # 订单支付
    url(r'^check$', OrderCheckView.as_view(), name='check'), # 支付结果查询
]
