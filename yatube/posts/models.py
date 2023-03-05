from django.db import models
from django.contrib.auth import get_user_model
from .validators import validate_not_empty
from django.conf import settings
from core.models import CreatedModel


User = get_user_model()


class Group(models.Model):
    """Класс для описания сообществ"""
    title = models.CharField('Имя', max_length=200)
    slug = models.SlugField('Адрес', unique=True)
    description = models.TextField('Описание', null=True, blank=True)

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'


class Post(CreatedModel):
    """Класс для описания записей/постов"""
    text = models.TextField(
        'Текст поста', validators=[validate_not_empty],
        help_text='Текст нового поста')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Сообщество',
        help_text='Группа, к которой будет относиться пост'
    )
    # Поле для картинки (необязательное)
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        null=True,
        help_text='Загрузите картинку'
    )
    # Аргумент upload_to указывает директорию,
    # в которую будут загружаться пользовательские файлы.

    def __str__(self):
        return self.text[:settings.QUANTITY_SYMBOL]

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'


class Comment(CreatedModel):
    """Класс для описания комментариев к постам"""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост'
    )
    text = models.TextField(
        'Текст комментария', validators=[validate_not_empty],
        help_text='Текст нового комментария')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )

    class Meta:
        ordering = ['pub_date']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return 'Comment {} by {}'.format(self.text, self.author)


class Follow(CreatedModel):
    """Класс для описания системы подписки на авторов"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )
    # колонка для soft delete design pattern,
    # исправно работает , но в функции отписки во views.py
    # пришлось закомментить её реализацию, чтобы пройти тесты из репозитория
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Статус отписки'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        if not self.is_deleted:
            return f'{self.user} подписался на {self.author}'
        else:
            return f'{self.user} отписался от {self.author}'
