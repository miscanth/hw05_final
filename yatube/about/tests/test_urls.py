# staticpages/tests/test_urls.py
from django.test import TestCase, Client
from http import HTTPStatus


class StaticPagesURLTest(TestCase):
    def setUp(self):
        # Создаем неавторизованый клиент
        self.guest_client = Client()

    def test_about_correct_url(self):
        """Проверка доступности адресов about."""
        name_urls = {
            'author': '/about/author/',
            'tech': '/about/tech/',
        }
        for expected_urls in name_urls.values():
            response = self.guest_client.get(expected_urls)
            with self.subTest(expected_urls=expected_urls):
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_url_correct_template(self):
        """Проверка шаблона для адресов about."""
        name_templates = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, expected_templates in name_templates.items():
            response = self.guest_client.get(url)
            with self.subTest(url=url):
                self.assertTemplateUsed(response, expected_templates)
