from django.urls import path
from . import views
from .feeds import LatestPostsFeed

app_name = 'blog'

urlpatterns = [
    # ============================================
    # URL-МАРШРУТЫ ДЛЯ БЛОГА
    # ============================================
    
    # Главная страница - список всех постов
    path('', views.post_list, name='post_list'),
    
    # Список постов по тегу
    path('tag/<slug:tag_slug>/', views.post_list, name='post_list_by_tag'),
    
    # Детальная страница поста (год, месяц, день, slug)
    path('<int:year>/<int:month>/<int:day>/<slug:post>/', views.post_detail, name='post_detail'),
    
    # Комментарий к посту
    path('<int:post_id>/comment/', views.post_comment, name='post_comment'),
    
    # Поделиться постом
    path('<int:post_id>/share/', views.post_share, name='post_share'),
    
    # ============================================
    # RSS ЛЕНТА
    # ============================================
    # URL для RSS ленты: /blog/feed/
    # LatestPostsFeed() - экземпляр класса Feed, который Django автоматически
    # преобразует в XML-файл RSS формата
    # Когда пользователь переходит по /blog/feed/, Django генерирует XML
    path('feed/', LatestPostsFeed(), name='post_feed'),
    
    path('search/', views.post_search, name='post_search'),
]



    # Что происходит:
    # Пользователь переходит по URL 
    # Django сопоставляет паттерн
    # Извлекает параметры из URL
    # Передаёт их в view
