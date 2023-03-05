from django.test import TestCase
from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, Comment, User
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
import shutil
import tempfile


# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем запись в базе данных
        cls.user = User.objects.create_user(
            username='test-username',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        # Создаем форму, если нужна проверка атрибутов
        cls.form = PostForm()
        cls.form_comment = CommentForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение,
        # изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='uncle_Motya')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author.force_login(PostCreateFormTest.user)

    def test_create_post_correct_form(self):
        """Валидная форма создает запись Post."""
        posts_count = Post.objects.count()
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст для формы создания второго поста',
            'group': self.group.pk,
            'image': uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с заданной группой и текстом
        self.assertTrue(
            Post.objects.filter(
                text='Текст для формы создания второго поста',
                author=self.user,
                group=self.group.pk,
                image='posts/small.gif'
            ).exists()
        )
        # Берём метод first(), т.к. в модели задана обратная
        # сортировка по дате и последний созданный пост
        # в выборке будет первым.
        last_post = Post.objects.first()
        new_post = Post.objects.get(
            text='Текст для формы создания второго поста'
        )
        self.assertEqual(new_post.pk, last_post.pk)
        self.assertEqual(self.user, last_post.author)
        self.assertEqual(self.group, last_post.group)
        self.assertEqual(Post.objects.first().image, 'posts/small.gif')

    def test_edit_post_correct_form(self):
        """Валидная форма изменяет запись Post."""
        second_post = Post.objects.create(
            author=self.user,
            text='ТестТест',
            group=self.group,
        )
        posts_count = Post.objects.count()
        before = set(Post.objects.all())
        # Считаем, сколько постов есть в старой(первой) группе
        old_group_response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        posts_count_old_group = (
            old_group_response.context['page_obj'].paginator.count
        )
        # Создаём новую группу и новые данные для внесения изменений
        new_post_text = 'Post has been changed'
        new_group = Group.objects.create(
            title='Brand new group',
            slug='new_test_slug',
            description='Special new group for testing edit-form'
        )
        form_data = {'text': new_post_text, 'group': new_group.pk}
        response = self.authorized_client.post(
            reverse('posts:post_edit', args={second_post.pk}),
            data=form_data, follow=True,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': second_post.pk}
            )
        )
        # Сравниваем два списка постов до и после изменений
        after = list(Post.objects.all())
        self.assertNotEqual(before, after)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.context.get('post').text, new_post_text)
        self.assertEqual(
            response.context.get('post').group.title,
            new_group.title
        )
        # Проверяем, что пост исчез из старой группы, и там на один меньше
        # И проверяем, что в новой группе есть один пост
        old_group_response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        new_group_response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': new_group.slug})
        )
        self.assertEqual(
            old_group_response.context['page_obj'].paginator.count,
            posts_count_old_group - 1,
        )
        self.assertEqual(
            new_group_response.context['page_obj'].paginator.count, 1,
        )
        # Проверка отображения is_edit в контексте шаблона
        response = self.authorized_client.get(
            reverse('posts:post_edit', args={second_post.pk}),
            data=form_data, follow=True,
        )
        self.assertIn('is_edit', response.context)

    def test_add_comment_correct_form(self):
        """Валидная форма создает комментарий на странице поста."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст для формы создания нового комментария',
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:add_comment', args={self.post.pk}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                args={self.post.pk}
            )
        )
        # Проверяем, увеличилось ли число комментариев
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        # Проверяем, что создался комментарий с заданным текстом
        self.assertTrue(
            Comment.objects.filter(
                text='Текст для формы создания нового комментария'
            ).exists()
        )
        last_comment = Comment.objects.last()
        new_comment = Comment.objects.get(
            text='Текст для формы создания нового комментария'
        )
        self.assertEqual(new_comment.post.pk, last_comment.post.pk)
        self.assertEqual(self.user, new_comment.author)

    def test_add_comment_for_authorized(self):
        """Проверка того, что только авторизированный
        пользователь может отправлять комментарии.
        """
        form_data = {
            'text': 'Комментарий от гостя',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', args={self.post.pk}),
            data=form_data,
            follow=True
        )
        # Проверяем, что такой комментарий не создался
        self.assertFalse(
            Comment.objects.filter(
                text='Комментарий от гостя'
            ).exists()
        )
        # Проверяем, сработал ли редирект на страницу авторизации
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        )

    def test_form_labels(self):
        """Проверка меток полей формы (labels),
        если они были переопределены в форме.
        """
        # В форме создания нового поста
        form_labels = {
            PostCreateFormTest.form.fields['text'].label: 'Текст записи',
            PostCreateFormTest.form.fields['group'].label: 'Группа',
            PostCreateFormTest.form.fields['image'].label: 'Изображение',
        }
        for label, expected in form_labels.items():
            with self.subTest(label=label):
                self.assertEqual(label, expected)
        # В форме создания нового комментария
        expected = 'Текст Вашего комментария'
        self.assertEqual(
            PostCreateFormTest.form_comment.fields['text'].label, expected
        )

    def test_form_help_texts(self):
        """Проверка текстов подсказок (help_text),
        если они были переопределены в форме.
        """
        # В форме создания нового поста
        form_help_texts = {
            PostCreateFormTest.form.fields['text'].help_text:
            'Начните писать',
            PostCreateFormTest.form.fields['group'].help_text:
            'Выберите группу, к которой будет относиться пост',
            PostCreateFormTest.form.fields['image'].help_text:
            'Загрузите изображение',
        }
        for help_text, expected in form_help_texts.items():
            with self.subTest(help_text=help_text):
                self.assertEqual(help_text, expected)
        # В форме создания нового комментария
        expected = 'Начните писать текст комментария'
        self.assertEqual(
            PostCreateFormTest.form_comment.fields['text'].help_text, expected
        )
