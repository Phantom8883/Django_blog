from django.contrib.sitemaps import Sitemap
from .models import Post



# Определили конкретно-прикладную карту сайт, унаследовав класс Sitemap модуля sitemaps.
# Атрибуты changefreq и priority указывают частоту изменения страниц постов и их релевантность на веб-сайте (Макс значение равно 1)
class PostSitemap(Sitemap):
    changefreq = 'weekly' 
    priority = 0.9 # Приоритет, максимум 1


    # Метод items() возвращает набор запросов QuerySet объектов, подлежащих включению в эту карту сайта
    # По умолчанию Django вызывает метод get_absolute_url() по каждому объекту, чтобы получить его URL-адрес.
    def items(self):
        return Post.published.all()
    
    def lastmod(self, obj):
        return obj.updated