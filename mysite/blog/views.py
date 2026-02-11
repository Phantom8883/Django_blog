from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import EmailPostForm, CommentForm, SearchForm

from django.core.mail import send_mail
from django.views.generic import ListView
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count # модуль содержит функции агрегирования Avg (среднее значение), Max, Min, Count (общее количество объектов)





def post_list(request, tag_slug=None):

    sort_by = request.GET.get('sort', 'date_new')
    posts = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags__in=[tag])


    # Сортировка постов
    if sort_by == 'date_new':
        posts = posts.order_by('-publish')  # новые сначала (DESC)
    elif sort_by == 'date_old':
        posts = posts.order_by('publish')  # старые сначала (ASC)
    elif sort_by == 'title_asc':
        posts = posts.order_by('title')  # по алфавиту A-Z (ASC)
    elif sort_by == 'title_desc':
        posts = posts.order_by('-title')  # по алфавиту Z-A (DESC)
    else:
        # По умолчанию: новые сначала
        posts = posts.order_by('-publish')




    # Пагинация
    # Постраничная разбивка с 3 постами на страницу
    paginator = Paginator(posts, 3)
    page_number = request.GET.get('page', 1)

    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        # Если page_number находится вне диапазона, то
        # выдать последнюю страницу результатов
        posts = paginator.page(1)
    except EmptyPage:
        # Если page_number находятся вне диапазона, то
        # выдать последнюю страницу
        posts = paginator.page(paginator.num_pages)


    return render(
        request, 
        'blog/post/list.html', 
        {'posts': posts,
        'tag': tag}
    )


def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post, # Первый аргумент - модель Обязательна
        status=Post.Status.PUBLISHED, 
        slug=post, # post из URL - это название поста (slug)
        publish__year=year, # __year - обращение к году даты
        publish__month=month, # __month -  обращение у месяцу даты
        publish__day=day # __day - обращение к дню даты
    )
    # Список активных комментариев к этому посту
    comments = post.comments.filter(active=True) # Все активные комментарии к посту

    # Форма для комментирования пользователями
    form = CommentForm() # пустая форма для нового комментария


    # ============================================
    # ЛОГИКА ПОХОЖИХ ПОСТОВ (по общим тегам)
    # ============================================
    # Цель: найти посты, которые имеют общие теги с текущим постом
    # Алгоритм:
    # 1. Получить ID тегов текущего поста
    # 2. Найти посты с этими тегами
    # 3. Исключить текущий пост
    # 4. Подсчитать количество общих тегов у каждого поста
    # 5. Отсортировать по количеству общих тегов (больше = более похожий)
    # 6. Взять первые 4 поста

    # ШАГ 1: Получаем ID тегов текущего поста
    # values_list('id', flat=True) - получаем список ID тегов, а не объекты Tag
    # Зачем: filter(tags__in=...) ожидает список ID [1, 2, 3], а не объекты
    # flat=True - возвращает простой список [1, 2, 3], а не кортежи [(1,), (2,)]
    # Пример: если у поста теги "Python" (id=1), "Django" (id=2), "Web" (id=3)
    # Результат: [1, 2, 3] - список ID тегов текущего поста
    post_tags_ids = post.tags.values_list('id', flat=True)

    # ШАГ 2: Ищем посты с этими тегами
    # Post.published - только опубликованные посты (используем кастомный менеджер)
    # filter(tags__in=post_tags_ids) - ищем посты, у которых есть хотя бы один из этих тегов
    #   tags - это ManyToMany связь с тегами (поле в модели Post)
    #   __in - lookup "в списке", проверяет, есть ли теги поста в списке post_tags_ids
    #   post_tags_ids - список ID тегов текущего поста [1, 2, 3]
    # Как работает: Django ищет посты, у которых в таблице TaggedItem есть записи
    # с тегами из списка post_tags_ids
    # Результат: все посты, которые имеют хотя бы один общий тег с текущим постом
    # Пример: если post_tags_ids = [1, 2, 3], найдём посты с тегами 1, 2, 3 или их комбинацией
    # Например: пост с тегами [1, 5] - найдётся (есть тег 1)
    #           пост с тегами [2, 4, 6] - найдётся (есть тег 2)
    #           пост с тегами [7, 8, 9] - НЕ найдётся (нет общих тегов)
    similar_posts = Post.published.filter(tags__in=post_tags_ids)

    # ШАГ 3: Исключаем текущий пост из результатов
    # exclude(id=post.id) - убираем сам пост из списка похожих
    # Зачем: не нужно рекомендовать тот же самый пост
    # Результат: похожие посты БЕЗ текущего поста
    similar_posts = similar_posts.exclude(id=post.id)

    # ШАГ 4: Подсчитываем количество тегов у каждого поста
    # annotate(same_tags=Count('tags')) - добавляем вычисляемое поле same_tags к каждому посту
    # Count('tags') - считает ВСЕ теги у каждого поста (не только общие!)
    # ⚠️ ВАЖНО: Count('tags') считает все теги поста, но так как мы уже отфильтровали
    # посты с общими тегами (filter(tags__in=...)), то посты с большим количеством тегов
    # чаще имеют больше общих тегов с текущим постом
    # Почему это работает: если пост имеет 10 тегов, вероятность, что среди них есть
    # общие с текущим постом, выше, чем у поста с 2 тегами
    # Результат: у каждого поста теперь есть поле same_tags с количеством тегов
    # Пример: если пост имеет 5 тегов, same_tags = 5
    # Теперь можно обращаться: post.same_tags (количество тегов этого поста)
    similar_posts = similar_posts.annotate(same_tags=Count('tags'))

    # ШАГ 5: Сортируем по релевантности (похожести)
    # order_by('-same_tags', '-publish') - сортировка по двум полям:
    #   - '-same_tags' - сначала по количеству тегов (убывание, больше = лучше)
    #     Минус перед полем означает сортировку по убыванию (от большего к меньшему)
    #     Посты с большим количеством тегов = более похожие (чаще имеют общие теги)
    #   - '-publish' - потом по дате публикации (убывание, новые = лучше)
    #     Если количество тегов одинаковое, показываем более новые посты
    # Зачем: сначала показываем посты с большим количеством тегов (более похожие),
    # если количество одинаковое - показываем более новые
    #image.pn Результат: отсортированный список похожих постов (самые похожие первыми)
    # Пример сортировки:
    #   Пост A: same_tags=5, publish=2025-01-13 → первый
    #   Пост B: same_tags=5, publish=2025-01-10 → второй (такое же количество, но старше)
    #   Пост C: same_tags=3, publish=2025-01-15 → третий (меньше тегов)
    similar_posts = similar_posts.order_by('-same_tags', '-publish')

    # ШАГ 6: Берём только первые 4 поста
    # [:4] - срез QuerySet, берём только первые 4 результата
    # Зачем: не нужно показывать все похожие посты, только самые релевантные
    # Результат: 4 самых похожих поста, отсортированных по релевантности
    # Пример: если было 10 похожих постов, останется только 4 самых похожих
    similar_posts = similar_posts[:4]


    # ============================================
    # ПЕРЕДАЧА ДАННЫХ В ШАБЛОН
    # ============================================
    # Возвращаем шаблон с контекстом:
    # - post - текущий пост (объект Post)
    # - comments - активные комментарии к посту (QuerySet)
    # - form - форма для добавления комментария (CommentForm)
    # - similar_posts - похожие посты (QuerySet из 4 постов, отсортированных по релевантности)
    return render(
        request,
        'blog/post/detail.html',
        {
            'post': post,           # Текущий пост
            'comments': comments,   # Комментарии к посту
            'form': form,           # Форма комментария
            'similar_posts': similar_posts  # Похожие посты (4 штуки)
        }
    )
    '''
    Как работает
        1. year, month, day, post — параметры из URL
        2. get_object_or_404(Post, ...) — ищет пост в модели Post
        3. slug=post — slug из URL
        4. publish__year=year — год публикации
        5. publish__month=month — месяц публикации
        6. publish__day=day — день публикации

        Зачем __:
        publish__year — обращение к году поля publish
        Django ORM позволяет обращаться к частям даты через __

        Что происходит:
        Django ищет пост по условиям
        Если найден — возвращает пост
        Если не найден — ошибка 404
    '''



class PostListView(ListView):
    """
    Альтернативное представление списка постов
    """

    queryset = Post.published.all() # Какие объекты показывать
    context_object_name = 'posts' # Имя переменной в шаблоне
    paginate_by = 3 # Колличество постов на странице
    template_name = 'blog/post/list.html' # Какой шаблон использовать





def post_share(request, post_id):

    # 1. Получаем пост извлекая по идентификатору id
    post = get_object_or_404(
        Post,
        id=post_id,
        status=Post.Status.PUBLISHED
    )

    # 2. Инициализирует флаг 
    sent = False


    # 3. Проверяем метод запроса
    if request.method == 'POST': # True - Пользователь отправил, иначе он просто открыл страницу. POST - форма отправлена, GET - страница просто открыта

        # 4. Форма отправлена
        form = EmailPostForm(request.POST) # создание формы с данными. request.POST - словарь с данными формы (Имя, email, комментарий) EmailPostForm(request.POST) - создаёт форму с этими данными
        if form.is_valid(): # проверка правильности данных если не True, то данные неправильные и будет показана ошибка

            # 5. Данные правильные
            cd = form.cleaned_data                                                                       # Это словарь с валидированными и очищенными данными формы. Получаем их. Нужно проверять данные, для отправки письма.
            post_url = request.build_absolute_uri(post.get_absolute_url())                               # полный URL поста. (с протоколом и доменом. Это возможно за счёт build_absolute_uri()  ). Формируем полный URL поста. Нужен полный URL, чтобы получатель мог перейти по ссылке
            subject = f"{cd['name']} recommends you read {post.title}"                                   # Тема письма. Используем данные из cd и используем заголовок поста. Зачем? Тема должна быть короткой и информативной
            message = f"Read {post.title} at {post_url}\n\n{cd['name']}'s comments: {cd['comments']}"    # Текст. 
            send_mail(subject, message, 'your_email@gmail.com', [cd['to']])                              # отправка email
            sent = True                                                                                  # успешная отправка
    else:
        # 6. Страница просто открыта
        form = EmailPostForm()
        # 7. Возвращает шаблон
    return render(
        request, 
        'blog/post/share.html',
        {'post': post, 
        'form': form, 
        'sent': sent}
    )





@require_POST # Только POST-запросы (безопастность)
def post_comment(request, post_id):
    post = get_object_or_404(       # получаем пост
        Post, 
        id=post_id,
        status=Post.Status.PUBLISHED
    )
    comment = None # изначально комментария нет
    form = CommentForm(data=request.POST) # создаём форму с данными

    if form.is_valid(): # проверяем данные
        comment = form.save(commit=False) # создаём объект, но не сохраняем   ЗАЧЕМ comit=False ? Создаёт объект без сохранения. Добавляем post перед сохранением. Потом сохраняем всё вместе.
        comment.post = post # привязываем к посту
        if request.user.is_authenticated:
            comment.user = request.user
        comment.save() # сохранвяем в БД

    return render(
        request,
        'blog/post/comment.html',
        {'post': post, 
        'form': form, 
        'comment': comment}
    )



from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
# SearchVector - создаёт поисковой вектор из полей (объединяет текст для поиска)
# SearchQuery - преобразует запрос пользователя в поисковый запрос PostgresSQL 
# SearchRank - вычисляет релевантность (насколько результат соответствует запросу)



def post_search(request):
    form = SearchForm()  # Пустая форма (когда пользователь ещё не искал)
    query = None         # Запрос пользователя (пока None)
    results = []         # Результат поиска (пока пустой список)

# Зачем: готовим переменные для двух сценариев:
# Пользователь только открыл страницу поиска (форма пустая)
# Пользователь уже отправил запрос (есть результаты)




# Проверка был ли запрос отправлен
# Как работает?

# request.GET - параметры из IRL (например: ?query=django)

# form = SearchForm(request.GET) - создаём форму с данными из URL

# from.is_valid() - проверям что данные корректны

# from.cleaned_data['query'] - получаем очищенную строку поиска

# Пример URL: http://127.0.0.1.8000/search/?query=django

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']



# Что происходит?
# SearchVector('title', 'body'): 

# Объединяет поля 'title' и 'body' в один поисковый вектор 
# PostgreSQL индексирует этот текст для быстрого поиска
# Аналог: "создай один больной тест из заголовка и содержимого"


# SearchQuery(query):
# 
# Преобразует запрос пользователя в формат PostgreSQL
# Обрабытвает специальные операторы (AND, ORM NOT)
# Пример: SearchQuery('django AND python') найдёт посты, есть оба слова

            search_vector = SearchVector('title', 'body')
            search_query = SearchQuery(query)


# .annotate(search=search_vector):
# Добавляет временное поле search к каддому посту
# Это поле содержит объединённый текст из title и body.

# .annotate(rank=SearchRank()):
# Добавляет поле rank (релевантность от 0 до 1)
# Чем выше rank, тем больше совпадений с запросом

# .filter(search=search_query):
# Оставляет только посты, где search соответствует search_query
# Это и есть сам поиск
# 
# .order_by('-rank'):
# Сортирует по убыванию релевантности
# Самые релевантные посты - первыми
# .

            results = Post.published.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
            ).filter(search=search_query).order_by('-rank')



# рендерим результат
    return render(
        request,
        'blog/post/search.html',
        {'form': form,
        'query': query,
        'results': results}
    )




