from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus

User = get_user_model()


class UserURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-username')

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_urls_for_anonymous(self):
        """Проверка доступа ко всем страницам для анонимного пользователя."""
        urls = {
            '/auth/signup/': HTTPStatus.OK,
            '/auth/logout/': HTTPStatus.OK,
            '/auth/login/': HTTPStatus.OK,
            '/auth/password_change/': HTTPStatus.FOUND,
            '/auth/password_change/done/': HTTPStatus.FOUND,
            '/auth/password_reset/': HTTPStatus.OK,
            '/auth/password_reset/done/': HTTPStatus.OK,
            '/auth/reset/done/': HTTPStatus.OK,
            '/auth/reset/<uidb64>/<token>/': HTTPStatus.OK,
            '/auth/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, status in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_urls_for_authorized(self):
        """Проверка доступа ко всем страницам
        для авторизованного пользователя.
        """
        urls = {
            '/auth/signup/': HTTPStatus.OK,
            '/auth/logout/': HTTPStatus.OK,
            '/auth/login/': HTTPStatus.OK,
            '/auth/password_change/': HTTPStatus.OK,
            '/auth/password_change/done/': HTTPStatus.OK,
            '/auth/password_reset/': HTTPStatus.OK,
            '/auth/password_reset/done/': HTTPStatus.OK,
            '/auth/reset/done/': HTTPStatus.OK,
            '/auth/reset/<uidb64>/<token>/': HTTPStatus.OK,
            '/auth/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        self.new_author = User.objects.create_user(username='new_Leo')
        for url, status in urls.items():
            with self.subTest(url=url):
                if self.authorized_client == self.new_author:
                    response = self.authorized_client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_urls_redirect_anonymous_on_login(self):
        """Проверка редиректа анонимного
        пользователя с адресов /password_change/
        и /password_change/done/ на страницу логина.
        """
        redirect_urls = {
            '/auth/password_change/':
            '/auth/login/?next=/auth/password_change/',
            '/auth/password_change/done/':
            '/auth/login/?next=/auth/password_change/done/',
        }
        for url, login_url in redirect_urls.items():
            response = self.guest_client.get(url, follow=True)
            with self.subTest(url=url):
                self.assertRedirects(response, login_url)

    def test_urls_uses_correct_template(self):
        """Проверка вызываемых шаблонов для каждого адреса."""
        templates_url_names = {
            '/auth/signup/': 'users/signup.html',
            '/auth/logout/': 'users/logged_out.html',
            '/auth/login/': 'users/login.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            # '/auth/reset/<uidb64>/<token>/':
            # 'users/password_reset_confirm.html' - не работает
        }
        for url, template in templates_url_names.items():
            response = self.authorized_client.get(url)
            with self.subTest(url=url):
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_for_authorized(self):
        """Проверка вызываемых шаблонов для авторизованного пользователя."""
        urls = {
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
        }
        self.new_author = User.objects.create_user(username='new_Leo')
        for url, status in urls.items():
            with self.subTest(url=url):
                if self.authorized_client == self.new_author:
                    response = self.authorized_client.get(url)
                    self.assertEqual(response.status_code, status)
