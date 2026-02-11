from django import forms
from .models import Comment

class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=25)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False, widget=forms.Textarea)

class CommentForm(forms.ModelForm):                   # ModelFrom - форма модели. Меньше кода, автоматическая валидация, автоматическое сохранение
    class Meta:
            model = Comment                               # какая модель
            fields = ['name', 'email', 'body']            # какие поля включить


class SearchForm(forms.Form):
    query = forms.CharField(max_length=64)

