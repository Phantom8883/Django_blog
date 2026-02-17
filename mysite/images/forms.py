from django import forms
from .models import Image

from django.core.files.base import ContentFile
from django.utils.text import slugify
import requests



# Определили форму ModelForm из модели Image,
# включая только поля title, url и description.
# Пользователи не будут вводить url адрес страницы прямо в форму.
# Вместо этого предоставим им инструмент JavaScrip, который позволит
# им выбирать изображение с внешнего сайта, а форма будет получать готовый url 
# в качестве параметра. Переопределили стандартный виджет поля url, чтобы использовать виджет
# HiddenInput. Этот виджет прорисовывает как HTML-элемент imput с атрибутом typy="hidden".
class ImageCreateForm(forms.ModelForm):
    class Meta:
        model = Image # форма привязана к модели Image
        fields = ['title', 'url', 'description'] # указываем какие поля из модели включить в форму
        widgets = {
            'url': forms.HiddenInput, # переопределям отображение поля
        }



    # Определяем метод clean_url(), чтобы очищать поле url.

    # 1)
    # значение поля url извлекается путем обращения к словарю clean_data экземпляра формы 

    # 2) 
    # URL-адрес разбивается на части, чтобы проверит ьналичие валидного расширения у файла.
    # Если расширение невалидно, то выдаётся ошибка ValidationError, и экземпояр формы не валидируется
    
    def clean_url(self):
        url = self.cleaned_data['url']
        valid_extensions = ['jpg', 'jpeg', 'png']
        extension = url.rsplit('.', 1)[1].lower()
        # ['https://example.com/image/photo', 'jpeg'] - rsplit()

        if extension not in valid_extensions:
            raise forms.ValidationError(
                'The given URL does not '
                'match valid image extensions. '
                )
        return url
    

    def save(
            self,
            force_insert=False,
            force_update=False,
            commit=True
    ):
        image = super().save(commit=False) # вызывается метод save родительского класса ModelForm. commit=False значит: создаём объект моедли без сохранения в БД
        image_url = self.cleaned_data['url']
        name = slugify(image.title)
        extension = image_url.rsplit(.1)[1].lower()
        image_name = f'{name}.{extension}'

        # скачать изображение с данного URL-адреса
        response = requests.get(image_url)
        image.image.save(
            image_name,
            ContentFile(response.content),
            save=False
        )
        if commit:
            image.save()
        return image