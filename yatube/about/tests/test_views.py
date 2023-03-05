from django.test import TestCase, Client
from http import HTTPStatus
from django.urls import reverse


class StaticPagesViewTest(TestCase):
    def setUp(self):
        # Создаем неавторизованый клиент
        self.guest_client = Client()

    def test_about_access_by_name(self):
        """URL, генерируемый при помощи namespace:name, доступен."""
        name_urls = {
            'author': 'about:author',
            'tech': 'about:tech',
        }
        for names in name_urls.values():
            response = self.guest_client.get(reverse(names))
            with self.subTest(names=names):
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_correct_template(self):
        """При запросе к staticpages:about
        применяется шаблон staticpages/about.html."""
        name_templates = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html',
        }
        for name, expected_templates in name_templates.items():
            response = self.guest_client.get(reverse(name))
            with self.subTest(name=name):
                self.assertTemplateUsed(response, expected_templates)
