from django.conf.urls import url
from apps.cart.views import CartAddView, CartInfoView, CartUpdataView, CartDeleteView

urlpatterns = [
    # url(r'^register$', views.register, name='register')
    # url(r'^register$', views.register, name='register'),
    url(r'^add$', CartAddView.as_view(), name='add'),
    url(r'^$', CartInfoView.as_view(), name='show'),
    url(r'^update$',CartUpdataView.as_view(), name='update'),
    url(r'^delete$', CartDeleteView.as_view(), name='delete'),
]
