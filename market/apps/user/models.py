from django.db import models
from django.contrib.auth.models import AbstractUser
from db.base_model import BaseModel
# Create your models here.


# 使用django默认的认证系统
# python manage.py createsuperuser->auth_user->User模型类
class User(AbstractUser, BaseModel):
    """用户模型类"""

    class Meta:
        db_table = 'df_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

class AddressManage(models.Manager):
    """继承models.Manager"""
    def all(self):
        res = super(AddressManage, self).all()
        res = res.filter(is_delete=False)
        return res
    def get_default_address(self, user):
        try:
            address = Address.objects.get(user=user, is_default=True)
        except Address.DoesNotExist:
            address = None
        return address


class Address(BaseModel):
    """地址模型类"""
    user = models.ForeignKey('User', verbose_name='所属账户')
    receiver = models.CharField(max_length=20, verbose_name='收件人')
    addr = models.CharField(max_length=256, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, null=True, verbose_name='邮政编码')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    objects = AddressManage()

    class Meta:
        db_table = 'df_address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name

