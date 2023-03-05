from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from ..models import Group, Post, User, Follow, Comment
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django import forms
from http import HTTPStatus
from django.conf import settings
import shutil
import tempfile
from django.core.cache import cache


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности
        # адресов со slug, username и post_id
        cls.user = User.objects.create_user(
            username='current_test_user',
        )
        cls.author_user = User.objects.create_user(
            username='another_user_author'
        )
        cls.another_user = User.objects.create_user(
            username='another_user_for_check'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
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
        self.author.force_login(PostViewTest.user)
        cache.clear()

    def test_reverse_name_template(self):
        """URL-адрес через namespace:
        name использует соответствующий шаблон.
        """
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': PostViewTest.group.slug
            }):
            ('posts/group_list.html'),
            reverse('posts:profile', kwargs={
                'username': PostViewTest.user.username
            }):
            ('posts/profile.html'),
            reverse('posts:post_detail', kwargs={
                'post_id': PostViewTest.post.pk
            }):
            ('posts/post_detail.html'),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            response = self.authorized_client.get(reverse_name)
            with self.subTest(reverse_name=reverse_name):
                self.assertTemplateUsed(response, template)

    def test_reverse_name_template_for_author(self):
        """Проверка вызываемого шаблона /edit/ для автора."""
        response = self.author.get(reverse(
            'posts:post_edit', args={PostViewTest.post.pk}
        ))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_index_context(self):
        """Проверка того, что шаблон index
        сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        context_names = {
            first_object.text: PostViewTest.post.text,
            first_object.author.username: PostViewTest.user.username,
            first_object.pub_date: PostViewTest.post.pub_date,
            first_object.group.slug: PostViewTest.group.slug,
            first_object.image: PostViewTest.post.image,
            first_object.comments: PostViewTest.post.comments,
        }
        for test_context, expected in context_names.items():
            with self.subTest(test_context=test_context):
                self.assertEqual(test_context, expected)

    def test_group_list_context(self):
        """Проверка того, что шаблон group_list
        сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': PostViewTest.group.slug}
        ))
        first_object = response.context['page_obj'][0]
        context_names = {
            first_object.text: PostViewTest.post.text,
            first_object.author.username: PostViewTest.user.username,
            first_object.pub_date: PostViewTest.post.pub_date,
            first_object.image: PostViewTest.post.image,
            first_object.comments: PostViewTest.post.comments,
            first_object.group.title: PostViewTest.group.title,
            first_object.group.slug: PostViewTest.group.slug,
            first_object.group.description: PostViewTest.group.description,
        }
        for test_context, expected in context_names.items():
            with self.subTest(test_context=test_context):
                self.assertEqual(test_context, expected)

    def test_post_detail_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': PostViewTest.post.pk
            })
        ))
        context_names = {
            response.context.get('post').text: 'Тестовый пост',
            response.context.get('post').pub_date: PostViewTest.post.pub_date,
            response.context.get('post').author.username: 'current_test_user',
            response.context.get('post').group.title: 'Тестовая группа',
            response.context.get('post').group.slug: 'test-slug',
            response.context.get('post').image: PostViewTest.post.image,
            response.context.get('post').comments: PostViewTest.post.comments,
            response.context.get('post').comments.first().text:
            'Тестовый комментарий',
            response.context.get('post').comments.first().author.username:
            'current_test_user',
        }
        for test_context, expected in context_names.items():
            with self.subTest(test_context=test_context):
                self.assertEqual(test_context, expected)

    def test_profile_context(self):
        """Проверка того, что шаблон profile
        сформирован с правильным контекстом.
        """
        response = self.client.get(
            reverse('posts:profile', kwargs={
                'username': PostViewTest.user.username
            })
        )
        first_object = response.context['page_obj'][0]
        context_names = {
            first_object.text: PostViewTest.post.text,
            first_object.author.username: PostViewTest.user.username,
            first_object.pub_date: PostViewTest.post.pub_date,
            first_object.group.slug: PostViewTest.group.slug,
            first_object.image: PostViewTest.post.image,
            first_object.comments: PostViewTest.post.comments,
        }
        for test_context, expected in context_names.items():
            with self.subTest(test_context=test_context):
                self.assertEqual(test_context, expected)

    def test_follow_index_context(self):
        """Проверка того, что шаблон follow_index
        сформирован с правильным контекстом.
        """
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
        self.new_post = Post.objects.create(
            author=self.author_user,
            text='Новый пост для проверки ленты друзей',
            group=self.group,
            image=uploaded,
        )
        self.follow = Follow.objects.create(
            user=self.user,
            author=self.author_user,
            is_deleted=False,
        )
        self.comment = Comment.objects.create(
            post=self.new_post,
            author=PostViewTest.user,
            text='Тестовый комментарий в посте following',
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        context_names = {
            first_object.text: self.new_post.text,
            first_object.author.username: PostViewTest.author_user.username,
            first_object.pub_date: self.new_post.pub_date,
            first_object.group.slug: PostViewTest.group.slug,
            first_object.image: self.new_post.image,
            first_object.comments: self.new_post.comments,
            first_object.comments.first().text:
            self.new_post.comments.first().text,
        }
        for test_context, expected in context_names.items():
            with self.subTest(test_context=test_context):
                self.assertEqual(test_context, expected)

    # Проверка словаря контекста страницы create (в нём передаётся форма)
    def test_create_form_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            # При создании формы поля модели типа TextField
            # преобразуются в CharField с виджетом forms.Textarea
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        # Проверяем, что типы полей формы в
        # словаре context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_create_with_group(self):
        """Проверка отображения поста на 3-х страницах,
        если при создании поста указать группу.
        """
        self.new_post = Post.objects.create(
            author=self.user,
            text='Новый пост для проверки корректности группы',
            group=self.group,
        )
        response = [
            (self.authorized_client.get(reverse('posts:index'))),
            (self.authorized_client.get(reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ))),
            (self.authorized_client.get(reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ))),
        ]
        for i in response:
            self.assertContains(i, self.new_post.text, 1, HTTPStatus.OK)

    def test_create_with_another_group(self):
        """Проверка отображения поста на странице другой группы."""
        self.test_create_with_group()
        self.another_group = Group.objects.create(
            title='Ещё одно новое сообщество',
            slug='test-slug_2',
            description='Новая группа для проверки отображения не её поста',
        )
        self.assertNotEqual(self.new_post.group, self.another_group)

    def test_edit_form_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.author.get(
            reverse('posts:post_edit', args={PostViewTest.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_add_comment_form_context(self):
        """Шаблон add_comment сформирован с правильным контекстом."""
        response = self.authorized_client.post(reverse(
            'posts:add_comment',
            args={PostViewTest.post.pk}
        ), follow=True)
        form_field = response.context.get('form').fields.get('text')
        self.assertIsInstance(form_field, forms.fields.CharField)

    def test_cache_index(self):
        """Проверка работы кеширования заглавной страницы index."""
        response_first = self.author.get(reverse('posts:index'))
        first_posts = response_first.content
        Post.objects.all().delete()
        response_second = self.author.get(reverse('posts:index'))
        second_posts = response_second.content
        self.assertEqual(first_posts, second_posts)
        """self.assertTrue(cache.get('index_page'))"""
        cache.clear()
        response_third = self.author.get(reverse('posts:index'))
        third_posts = response_third.content
        self.assertNotEqual(first_posts, third_posts)

    def test_follow_user(self):
        """Авторизированный пользователь может
        подписываться на других пользователей.
        """
        follows_count = Follow.objects.count()
        # Отправляем POST-запрос
        response = self.authorized_client.post(reverse(
            'posts:profile_follow',
            args={PostViewTest.author_user.username}
        ), follow=True)
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.author_user.username}
            )
        )
        self.assertTrue(Follow.objects.filter(
            user=self.user,
            author=self.author_user,
            is_deleted=False
        ))
        # Проверяем, что число подписок увеличилось на 1
        self.assertEqual(Follow.objects.count(), follows_count + 1)

    def test_self_follow_user(self):
        """Проверяем, что пользователь не может подписаться сам на себя"""
        follows_count = Follow.objects.count()
        # Авторизуем третьего пользователя и проверим самоподписку
        self.authorized_client.force_login(self.another_user)
        self.authorized_client.post(
            reverse('posts:profile_follow', args={self.another_user.username}),
            follow=True
        )
        # Проверяем, что число подписок осталось прежним
        self.assertEqual(Follow.objects.count(), follows_count)
        self.assertFalse(Follow.objects.filter(
            user=self.another_user,
            author=self.another_user
        ))

    def test_follow_anonymous(self):
        # Проверяем, что неавторизированный пользователь
        # не может подписаться на других пользователей
        follows_count = Follow.objects.count()
        self.guest_client.post(reverse(
            'posts:profile_follow',
            args={PostViewTest.author_user.username}
        ), follow=True)
        # Проверяем, что число подписок осталось прежним
        self.assertEqual(Follow.objects.count(), follows_count)
        self.assertFalse(Follow.objects.filter(
            user=self.user.is_anonymous,
            author=self.author_user,
            is_deleted=False
        ))

    def test_unfollow_user(self):
        """Авторизированный пользователь может
        удалять других пользователей из подписок.
        """
        # Отправляем POST-запрос - сначала подписываемся на автора
        response = self.authorized_client.post(reverse(
            'posts:profile_follow',
            args={PostViewTest.author_user.username}
        ), follow=True)
        # считаем подписчиков, фильтруя статус отписки, и напрямую
        followers_count_1 = Follow.objects.filter(
            author=self.author_user,
            is_deleted=False
        ).count()
        followers_1 = self.user.follower.count()
        # Отправляем POST-запрос - теперь отписываемся от того же автора
        response = self.authorized_client.post(reverse(
            'posts:profile_unfollow',
            args={PostViewTest.author_user.username}
        ), follow=True)
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.author_user.username}
            )
        )
        self.assertFalse(Follow.objects.filter(
            user=self.user,
            author=self.author_user,
            is_deleted=False
        ))
        # снова счиатем подписчиков уже после отписки,
        # фильтруя статус отписки, и напрямую
        followers_count_2 = Follow.objects.filter(
            author=self.author_user,
            is_deleted=False
        ).count()
        self.assertEqual(followers_count_2, followers_count_1 - 1)
        followers_2 = self.user.follower.count()
        self.assertEqual(followers_2, followers_1 - 1)
        # Неактуально: Проверка Follow.objects.count() не подойдёт
        # при использовании soft delete,
        # т.к. при отписке количество объектов Follow осталось прежним,
        # изменился лишь статус is_deleted с False на True
        """self.assertTrue(Follow.objects.filter(
            user=self.user,
            author=self.author_user,
            is_deleted=True
        ))"""

    def test_self_unfollow_user(self):
        """Авторизированный пользователь
         не может отписаться от самого себя.
         """
        follows_count = Follow.objects.count()
        # Авторизуем третьего пользователя и проверим самоотписку
        self.authorized_client.force_login(self.another_user)
        self.authorized_client.post(reverse(
            'posts:profile_unfollow', args={self.another_user.username}
        ), follow=True)
        # Проверяем, что число подписок осталось прежним
        self.assertEqual(Follow.objects.count(), follows_count)
        self.assertFalse(Follow.objects.filter(
            user=self.another_user,
            author=self.another_user
        ))

    def test_unfollow_anonymous(self):
        """Неавторизированный пользователь
        не может отписаться от других пользователей.
        """
        follows_count = Follow.objects.count()
        self.guest_client.post(reverse(
            'posts:profile_unfollow',
            args={PostViewTest.author_user.username}
        ), follow=True)
        # Проверяем, что число подписок осталось прежним
        self.assertEqual(Follow.objects.count(), follows_count)
        self.assertFalse(Follow.objects.filter(
            user=self.user.is_anonymous,
            author=self.author_user,
            is_deleted=False
        ))

    def test_following_new_post(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан, и не появляется в ленте тех, кто не подписан.
        """
        self.new_post = Post.objects.create(
            author=self.author_user,
            text='Новый пост для проверки ленты друзей',
            group=self.group,
        )
        self.follow = Follow.objects.create(
            user=self.user,
            author=self.author_user,
            is_deleted=False,
        )
        self.assertContains(self.authorized_client.get(
            reverse('posts:follow_index')
        ), self.new_post.text, 1, HTTPStatus.OK)
        # Возьмём для проверки третьего пользователя,
        # который не подписан на автора
        # Возможно он даже был ранее подписан, но уже отписался
        self.unfollow = Follow.objects.create(
            user=self.another_user,
            author=self.author_user,
            is_deleted=True,
        )
        # Авторизуем этого пользователя
        self.authorized_client.force_login(self.another_user)
        # Проверяем, что новый пост автора не пояляется
        # в ленте отписавшегося пользователя
        self.assertContains(self.authorized_client.get(
            reverse('posts:follow_index')
        ), self.new_post.text, 0)
