# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_remove_address_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='user',
            field=models.ForeignKey(default='', to=settings.AUTH_USER_MODEL, verbose_name='所属账户'),
            preserve_default=False,
        ),
    ]
