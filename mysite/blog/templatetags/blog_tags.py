from django import template
from ..models import Post
from django.db.models import Count
from django.utils.safestring import mark_safe
import markdown



register = template.Library()

@register.simple_tag(name='my_tag')
def total_posts():
    return Post.published.count()


@register.inclusion_tag('blog/post/latest_posts.html')
def show_latest_posts(count=5):
    latest_posts = Post.published.order_by('-publish')[:count]
    return {'latest_posts': latest_posts}


@register.simple_tag
def get_most_commented_posts(count=5):
    return Post.published.annotate(
        total_comments=Count('comments')
    ).order_by('-total_comments')[:count]


# ============================================
# ШАБЛОННЫЙ ФИЛЬТР ДЛЯ MARKDOWN
# ============================================
#
# ЧТО ТАКОЕ MARKDOWN?
# -------------------
# Markdown - это синтаксис форматирования обычного текста, который очень прост
# в использовании и предназначен для конвертирования в HTML.
#
# ЗАЧЕМ НУЖЕН MARKDOWN?
# ---------------------
# 1. Проще писать посты - не нужно знать HTML
# 2. Читается как обычный текст (даже в сыром виде)
# 3. Автоматически конвертируется в HTML
# 4. Другие не сведущие в технологиях участники легко пишут посты
#
# ПРИМЕРЫ MARKDOWN СИНТАКСИСА:
# -----------------------------
# *курсив* → <em>курсив</em>
# **жирный** → <strong>жирный</strong>
# # Заголовок → <h1>Заголовок</h1>
# [ссылка](url) → <a href="url">ссылка</a>
# - Список → <ul><li>Список</li></ul>
#
# КАК ЭТО РАБОТАЕТ?
# -----------------
# 1. Автор пишет пост в формате Markdown
# 2. В шаблоне применяется фильтр |markdown
# 3. Markdown конвертируется в HTML
# 4. HTML отображается в браузере
#
# БЕЗОПАСНОСТЬ:
# -------------
# Django по умолчанию ЭКРАНИРУЕТ весь HTML (защита от XSS атак).
# Но нам нужно показать HTML, который мы сами сгенерировали из Markdown.
# Поэтому используем mark_safe() - помечаем HTML как "безопасный".

@register.filter(name='markdown')
def markdown_format(text):
    """
    Шаблонный фильтр для конвертации Markdown в HTML.
    
    Параметры:
    - text - текст в формате Markdown (строка)
    
    Что делает:
    1. markdown.markdown(text) - конвертирует Markdown в HTML
       Библиотека markdown парсит синтаксис и создает HTML-теги
    2. mark_safe(...) - помечает HTML как безопасный для отображения
       Без этого Django экранирует HTML (заменит < на &lt;)
    
    Что возвращает:
    - HTML-код (безопасный для отображения в шаблоне)
    
    Использование в шаблоне:
    {{ post.body|markdown }}
    
    Пример:
    Вход:  "**Жирный текст**"
    Выход: "<strong>Жирный текст</strong>"
    
    Почему функция называется markdown_format, а фильтр markdown?
    - Во избежание конфликта имен между функцией и модулем markdown
    - В шаблонах используется короткое имя: |markdown
    - В коде функция имеет понятное имя: markdown_format
    """
    return mark_safe(markdown.markdown(text))
