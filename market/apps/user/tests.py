from django.test import TestCase
from .models import User

# Create your tests here.
user = User.objects()
user.username = 'python1'
user.password = '11111111'
user.is_active = '1'
user.save()