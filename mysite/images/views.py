from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ImageCreateForm



@login_required # Только авторизованные пользователи могут попасть на эту страницу.
def image_create(request):
    if request.method == 'POST': # Django различает HTTP методы: GET для отоюражения формы, POST для её отправки
        # форма отправлена
        form = ImageCreateForm(data=request.POST)

        if form.is_valid(): # is_valid() - магический метод Django Forms который:
            # 1. Проверяет все поля формы на валидность (включая твой метод clean_url)
            cd = form.cleaned_data # Здесь cd - это словарь вида: {'title': '...', 'url': '...', 'description': '...'}
            # 2. Если всё ок создаёт словарь cleaned_data с уже очищенными и безопасными данными

            # данные в форме валидны
            new_image = form.save(commit=False)
            # Вызываем переопределённый метод save из формы ImageCreateForm
            # commit = False означает: создать объект модели, но ещё не сохранять в базе данных\

            # назначить текущего пользователя элементу
            new_image.user = request.user
            new_image.save()
            # Магия Django: ForeignKey связывает объект с пользователем автоматически.
            # Благодаря ORM не нужно писать SQL вручную — Django создаёт нужный INSERT с user_id


            messages.success(
                request,
                'Image added successfully'
            )
            return redirect(new_image.get_absolute_url())
    else:
        form = ImageCreateForm(data=request.GET)
    return render(
        request,
        'images/image/create.html',
        {
            'section': 'images',
            'form': form
        }
    )
