from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'account'

urlpatterns = [

    # Встроенные URL-адреса Django для аутентификации
    path('', include('django.contrib.auth.urls')), # АВТОМатичски добавляет все пути: login/ logout/ password reset/change 
    
    path('', views.dashboard, name='dashboard'),

    path('register/', views.register, name='register'),

    path('edit/', views.edit, name='edit'),
]

