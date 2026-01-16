from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [

    # представление поста
    path('', views.post_list, name='post_list'), # Превращает класс в функцию для Django 

    path('tag/<slug:tag_slug>/', views.post_list, name='post_list_by_tag'),

    path('<int:year>/<int:month>/<int:day>/<slug:post>/', views.post_detail, name='post_detail'), # год, месяц, день, название публикации

    path('<int:post_id>/comment/', views.post_comment, name='post_comment'),

    path('<int:post_id>/share/', views.post_share, name='post_share'),

]



    # Что происходит:
    # Пользователь переходит по URL 
    # Django сопоставляет паттерн
    # Извлекает параметры из URL
    # Передаёт их в view
