from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Group, Post, Comment, Follow
from http import HTTPStatus
from django.core.cache import cache

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности
        # адресов со slug, username и post_id
        cls.user = User.objects.create_user(username='current_test_user')
        cls.user_2 = User.objects.create_user(username='another_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user_2,
            is_deleted=False,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author.force_login(PostURLTest.user)
        cache.clear()

    def test_urls_for_anonymous(self):
        """Проверка доступа ко всем страницам для
        анонимного пользователя.
        """
        urls_code_status = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/create/': HTTPStatus.FOUND,
            f'/posts/{self.post.pk}/edit/': HTTPStatus.FOUND,
            f'/posts/{self.post.pk}/comment': HTTPStatus.MOVED_PERMANENTLY,
            '/follow/': HTTPStatus.FOUND,
            f'/profile/{self.user.username}/follow/': HTTPStatus.FOUND,
            f'/profile/{self.user.username}/unfollow/': HTTPStatus.FOUND,
        }
        for url, status in urls_code_status.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_urls_for_authorized(self):
        """Проверка доступа ко всем страницам для
        авторизованного пользователя.
        """
        urls_code_status = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/create/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/edit/': HTTPStatus.FOUND,
            f'/posts/{self.post.pk}/comment': HTTPStatus.MOVED_PERMANENTLY,
            '/follow/': HTTPStatus.OK,
            f'/profile/{self.user.username}/follow/': HTTPStatus.FOUND,
            f'/profile/{self.user.username}/unfollow/': HTTPStatus.FOUND,
        }
        for url, status in urls_code_status.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_urls_for_author(self):
        """Проверка доступа ко всем страницам для автора."""
        urls_code_status = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/create/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/edit/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/comment': HTTPStatus.MOVED_PERMANENTLY,
            '/follow/': HTTPStatus.OK,
            f'/profile/{self.user.username}/follow/': HTTPStatus.FOUND,
            f'/profile/{self.user.username}/unfollow/': HTTPStatus.FOUND,
        }
        for url, status in urls_code_status.items():
            with self.subTest(url=url):
                response = self.author.get(url)
                self.assertEqual(response.status_code, status)

    def test_urls_redirect_login(self):
        """Проверка редиректа анонимного
        пользователя с адресов /edit/ и /create/ на страницу логина.
        """
        redirect_urls = {
            f'/posts/{self.post.pk}/edit/':
            f'/auth/login/?next=/posts/{self.post.pk}/edit/',
            '/create/': '/auth/login/?next=/create/',
            '/follow/': '/auth/login/?next=/follow/',
            f'/profile/{self.user.username}/follow/':
            f'/auth/login/?next=/profile/{self.user.username}/follow/',
            f'/profile/{self.user.username}/unfollow/':
            f'/auth/login/?next=/profile/{self.user.username}/unfollow/',
            f'/posts/{self.post.pk}/comment/':
            f'/auth/login/?next=/posts/{self.post.pk}/comment/',
        }
        for url, login_url in redirect_urls.items():
            response = self.guest_client.get(url, follow=True)
            with self.subTest(url=url):
                self.assertRedirects(response, login_url)

    def test_url_template(self):
        """Проверка вызываемых шаблонов для каждого адреса."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        for url, template in templates_url_names.items():
            response = self.authorized_client.get(url)
            with self.subTest(url=url):
                self.assertTemplateUsed(response, template)

    def test_url_template_for_author(self):
        """Проверка вызываемого шаблона /edit/ для автора."""
        response = self.author.get(f'/posts/{self.post.pk}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
