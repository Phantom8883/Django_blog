from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models



class CustomUser(AbstractUser): # создаём кастомного пользователя
    pass

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # OneToOne связь.
    date_of_birth = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to='users/%Y/%m/%d', blank=True, null=True)

    def __str__(self):
        return f'Profile of {self.user.get_username()}'
