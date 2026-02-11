from django.db import models
from django.utils import timezone
#from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
from taggit.managers import TaggableManager






class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)






class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    title = models.CharField(max_length=250)
    slug= models.SlugField(max_length=250, unique_for_date='publish') # указываем что slug уникален для даты публикации
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        related_name='blog_posts'
    )    
    body = models.TextField()
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT
    )

    objects = models.Manager()
    published = PublishedManager()
    tags = TaggableManager()

    class Meta:
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish']),
        ]

    def __str__(self):
        return self.title

    # Один главный URL для каждого поста 
    # Вместа разных ссылок используем один метод
    # Зачем? Удобно использовать один метод заместо повторяющегося кода
    # Стандарт: Django рекомендует так делать
    # Как работает:
    # В модели добавляем метод get_absolute_url()
    # Он возвращает URL поста через reverse()
    # В шаблонах используем {{ post.get_absosute_url }} А не прописываем адрес каждый раз. Тем более, если изменим URL то он автоматически изменится везде.
    def get_absolute_url(self):
        return reverse(
            'blog:post_detail', 
            args=[
                self.publish.year,
                self.publish.month,
                self.publish.day,
                self.slug
            ]
        )






class Comment(models.Model):
    user = models.ForeignKey( # связь с постом (много комментариев к одному посту)
        settings.AUTH_USER_MODEL, # сам пост с которым связываем комментарии
        on_delete=models.CASCADE, # если удаляем пост, то удаляются и комментарии к нему
        related_name='comments', # доступ через post.comments.all()
        null=True,
        blank=True
    )

    post = models.ForeignKey(
        'Post',  # модель поста
        on_delete=models.CASCADE,
        related_name='comments'
    )

    
    # Данные комментариев
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()

    # Даты создания и обновления
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # флаг активности (можно скрывать неуместные)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created'] # сортировка по дате созднаия
        indexes = [
            models.Index(fields=['created']), # индекс для быстрого поиска
        ]

    def __str__(self):
        return f"Comment by {self.name} on {self.post}"

