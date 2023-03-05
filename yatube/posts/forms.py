from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст записи',
            'group': 'Группа',
            'image': 'Изображение',
        }
        help_texts = {
            'text': 'Начните писать',
            'group': 'Выберите группу, к которой будет относиться пост',
            'image': 'Загрузите изображение',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст Вашего комментария',
        }
        help_texts = {
            'text': 'Начните писать текст комментария',
        }
